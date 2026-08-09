## Context

本变更在已有考试（ExamRecord）、练习（PracticeSession）、诊断（StudentAnswer, BarrierProfile）、学生（Student）数据基础上，构建两个新服务：PanelService（聚合计算）和 EarlyWarningService（异常检测）。现有 APScheduler 已注册 2 个 cron（daily_practice 08:00, notify_parents 20:00），需新增第 3 个。现有 `WarningLog` 模型（diagnosis.py:226-259）缺少 6 个字段，需 Alembic 迁移补充。

## Goals / Non-Goals

**Goals:**
- 提供 12 个 API 端点（Panel 7 + Warning 5），覆盖教师学情面板和预警管理
- 实现按需实时聚合（不建预计算快照表，简化为先跑通，后续按需加缓存）
- 四类预警检测规则纯函数实现，不依赖外部 LLM 或 API
- 预警生命周期完整（pending → processing → resolved/dismissed）
- 每天 00:00 定时自动检测

**Non-Goals:**
- 不在此 Phase 提供 Analytics API（13 端点暂缓，详见 proposal）
- 不构建前端面板页面（仅后端 API）
- 不发送预警通知（通知推送属于后续 Phase）
- 不处理家长端面板（仅教师端）

## Decisions

### 1. 按需实时聚合（方案 A）

**选择**：每次 API 请求实时查库 + Python 计算，不建 ClassSnapshot 预计算表。

**理由**：班级规模有限（几十人），单次聚合计算量可控；避免"今天考了试但面板看不到"的一致性问题；Phase 1 先跑通，后续若有性能问题再加缓存层。

**备选**：方案 B — 定时预计算快照写入 ClassSnapshot 表。被否决原因：增加新表 + 快照逻辑 + 一致性维护复杂度，且设计文档未要求预计算。

### 2. 加权指数衰减公式

**公式**：`w_i = exp(-λ × (t_now - t_i) / T_week)`，λ = ln(2) ≈ 0.693

**理由**：设计文档 §2.1 明确要求；半衰期为一周（7 天前考试权重降为 0.5）；PanelService 在内存中计算，不需要存储中间权重。

### 3. 预警数据源分离

**选择**：`score_drop` 仅取 ExamRecord（考试成绩），PracticeSession 不纳入。其他规则（high_error_rate、new_barrier）可使用双数据源。

**理由**：设计文档 §5.2 流程图明确只使用考试成绩检测成绩下滑，练习数据波动大、不稳定。

### 4. BarrierProfileHistory 新表

**选择**：新建独立表（4 字段：student_id, snapshot_at, profile JSON, dominant_barrier），不修改 Student.barrier_profile 结构。

**理由**：Student 表只存当前最新障碍画像；历史快照独立存储用于趋势比较和 new_barrier 检测基线。

### 5. WarningLog 模型丰富

**选择**：在现有 WarningLog 基础上增加 6 字段，保持已有枚举值名称（`consecutive_absence`, `severe` 等），不重命名。

**理由**：向后兼容，避免破坏已有数据。Alembic 迁移处理新增列，已有列不变。

### 6. PanelService 结构

**选择**：单一 `PanelService` 类，方法按聚合维度拆分（`get_class_overview`, `get_student_detail`, `get_knowledge_points`, `get_barriers`, `get_concern_students`, `get_exam_trend`），共用内部 helper（`_weighted_avg`, `_error_rate`, `_barrier_distribution`）。

**理由**：所有聚合共享数据源（同一班级的学生、考试、练习），单一类避免跨服务数据重复加载。

### 7. EarlyWarningService 结构

**选择**：四个检测规则独立方法 + 一个 orchestrator（`run_all_checks`），每条规则返回 `List[WarningResult]`。

**理由**：规则间无依赖，可独立测试、独立演进。每条规则自行判断"是否已存在未处理预警"以去重。

## Risks / Trade-offs

- **[Risk] 实时聚合性能**：每次请求都查库计算，若班级人数多（>100）或考试次数多（>50），响应可能变慢。→ **Mitigation**：Monitor SlowAPI 指标；若 P95 > 1s 则后续引入 Redis 缓存 + TTL 5min。
- **[Risk] BarrierProfileHistory 数据缺失**：首次部署时所有学生无历史快照，new_barrier 检测跳过，需等第二次检测才有基线。→ **Mitigation**：首次检测自动将当前障碍画像写入快照作为基线，第二次检测即可正常运行。
- **[Risk] 预警重复生成**：去重逻辑依赖"是否存在未处理同类型预警"，若教师 dismiss 后又触发相同条件会重新生成。→ **Mitigation**：这是预期行为——dismiss 表示单次误判，不应永久屏蔽。

## Migration Plan

1. Alembic 迁移：新增 BarrierProfileHistory 表 + WarningLog 加 6 列（title, data, status, processed_by, processed_at, note）
2. 部署新代码（FastAPI 重启），新路由自动注册
3. 调度器启动时自动注册 warning_check cron（00:00）
4. 首次预警检测"冷启动"友好：无历史快照的学生自动建立基线
5. 回滚：Alembic downgrade 移除新表和列，移除新注册的路由和 cron

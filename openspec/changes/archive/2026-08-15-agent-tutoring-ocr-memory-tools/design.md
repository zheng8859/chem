# 设计 — 辅导、OCR 与记忆 Agent 工具组

## Context

16 个工具的代码已基本落地（见 proposal.md - Why），但存在三类问题：

1. **行为测试为零**：只有 `test_agent_engine.py` 的注册完整性测试（`test_all_tools_registered` 等），没有任何工具行为测试。
2. **记忆工具存在真实 bug**（非仅缺测试）：
   - `agent/tools/memory_tools.py::memory_student_get` 第 29 行 `from app.agent.store import read_diagnosis_snapshots, read_learning_plan` —— 这两个函数在 `app/agent/store.py` 中**不存在**（实际名为 `read_diagnosis_history` / `read_learning_plan_summary`，且签名带 `db` 参数）。该 import 位于 `try` 块之外，调用即抛 `ImportError`。
   - `memory_teacher_get` 是硬编码占位（返回 `"balanced"` / `"auto"`）。
   - 已有 `MemoryType.teacher_preference` 枚举与 `LongTermMemory.teacher_id` 列，实现真实读取的基础已就绪。
3. **结构噪声**：`app/chem_skills/` 整棵树为空（真实引擎在顶层 `chem_skills/`）；`memory_student_get` 存在两份同名实现（注册工具版 + `app/agent/tools/memory_student_get.py` 上下文注入辅助版，均读 `LongTermMemory` 表）。

底层约束：`app/agent/store.py` 是 `LongTermMemory` 表的唯一读写抽象（best-effort 写、失败不阻塞）；`MainSession()` 是工具打开 DB 会话的统一入口（OCR 工具已示范）。

## Goals / Non-Goals

**Goals:**
- 为 16 个工具建立行为测试，固化文档58 完成标准要求的验证点。
- 修复 `memory_student_get` 的 import bug，实现 `memory_teacher_get` 真实读取。
- 补 `simulate_experiment` 为有意义结构。
- 清理空目录与命名碰撞。

**Non-Goals:**
- 不把 6 个专题 Socratic 工具重写为调用确定性引擎（`build_ice_table` 等）——纯 prompt 引导是合法形态，打通属后续工作，本次不动。
- 不新增 REST API、不新增数据库表、不改 Provider。
- 不实现教师偏好的**写入**路径（见 Open Questions）。

## Decisions

### 决策 1：测试分层策略

**决定**：按工具是否有 DB 依赖分层——纯函数工具走 L1 单元测试（mock/内存），DB 依赖工具走 L2 集成测试（真实 `MainSession` + 内存 SQLite）。

- **L1 单元**：`make_tutoring_tool` 三态流转（entry/step/complete）、6 专题的 step_prompts 结构、`chemistry_tutor` 双模式、`simulate_experiment` 结构、`balance_equation` 确定性（mock 配平引擎成功/失败/不可用三态）。
- **L2 集成**：OCR 3 工具（依赖 `OCRTask` + `GradingService`）、`generate_parent_report` / `send_report_to_parent`（依赖 `ParentService` / `NotificationService`）、`memory_student_get` / `memory_teacher_get`（依赖 `LongTermMemory`）。

**备选**：全部走 L2 集成 —— 拒绝，纯工具无 DB 依赖，走集成会拖慢且引入无关 setup。

### 决策 2：simulate_experiment 实现方式

**决定**：返回结构化实验信息（`name` / `steps` / `phenomena` / `equations` / `safety_notes`）+ `_component`（experiment-card）标记，**不硬编码大量实验数据**。具体实验步骤/现象/方程式由 LLM 基于返回结构在对话中生成，工具只负责提供结构化骨架与渲染标记。

**备选 A**：硬编码常见实验数据库 —— 拒绝，维护成本高、覆盖面窄，且文档30 未要求确定性实验数据。
**备选 B**：接 `chem_skills` 引擎 —— 拒绝，当前无实验模拟引擎，新建属过度设计（YAGNI）。

### 决策 3：memory_student_get 修复

**决定**：改为调用 `store.read_diagnosis_history(db, student_id)` 与 `store.read_learning_plan_summary(db, student_id)`，用 `async with MainSession() as db` 打开会话（对齐 OCR 工具的写法）。返回结构保持不变（`diagnosis_history` / `active_learning_plan` / `diagnosis_count`）。

**备选**：继续用旧的 `read_diagnosis_snapshots` 名并在 store.py 里补这两个函数 —— 拒绝，store.py 已有等价实现，改名会制造第三个同义函数。

### 决策 4：memory_teacher_get 实现

**决定**：在 `store.py` 新增 `read_teacher_preference(db, teacher_id)`，读 `LongTermMemory` 中 `teacher_id == teacher_id AND memory_type == teacher_preference` 的最新一条；工具用 `MainSession()` 调用，无记录时返回默认值（`"balanced"` / `"auto"` / `{}`）。

**备选**：新建 `teacher_preferences` 表 —— 拒绝，`LongTermMemory` + `MemoryType.teacher_preference` 已为此设计，无需新表。

### 决策 5：命名碰撞与空目录清理

**决定**：
- 保留 `app/agent/tools/memory_student_get.py` 的上下文注入辅助函数，但**改名为 `fetch_student_memory`**（或让其委托 store.py），消除与注册工具的语义混淆。改名前先 grep 确认调用点。
- 删除 `app/chem_skills/` 空目录树（先 `grep -r "app.chem_skills"` 确认无 import，真实 import 均为顶层 `chem_skills.`）。

**备选**：不动 `app/agent/tools/memory_student_get.py` —— 拒绝，同名两函数 + 两处重复读 `LongTermMemory` 是维护隐患。

## Risks / Trade-offs

- **[Risk] `memory_student_get` 修复可能暴露下游消费方对旧返回结构的依赖** → 保持返回结构不变，仅修 import 与 db 传递；新增测试断言返回结构。
- **[Risk] 删除 `app/chem_skills/` 可能误删有 import 的目录** → 删除前 grep 确认；若存在 `from app.chem_skills...` 则改为迁移而非删除。
- **[Risk] 教师偏好无写入路径，`memory_teacher_get` 长期返回默认值** → 明确记为 Open Question；测试断言「无记录返回默认值」而非「返回真实偏好」。
- **[Trade-off] OCR 工具测试依赖真实 `GradingService` 与 DB** → 接受，文档24 §11 的边界用例（空批次、状态过滤）正需要真实 DB 才能验证。

## Migration Plan

无运行时迁移。清理类操作（删空目录、改名）在测试全绿后进行，且各自独立提交，便于回滚。

## Open Questions

- **教师偏好的写入时机**：目前没有 `write_teacher_preference` 调用点。本次只实现读取（缺省返回默认值），写入路径待后续定义教师「偏好设置」功能时补。此问题不改变 spec 或本变更的任务拆分。

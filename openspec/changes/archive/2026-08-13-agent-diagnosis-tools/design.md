## Context

本变更只动「工具层」：`agent/tools/diagnosis_tools.py` 的 7 个工具及其 `@register_tool` 元数据，底层服务与引擎已就绪。现状与可复用点：

- `DiagnosisService.get_student_diagnosis(db, student_id)` — 个体诊断（工具已用）。
- `DiagnosisService.get_class_diagnosis(db, class_id, exam_id)` — 班级级诊断（**已存在，未被工具使用**；需 exam_id，故本变更改用 `PanelService.get_barriers`，见 D2）。
- `PanelService.get_student_detail` / `get_class_overview` / `get_concern_students` / `get_barriers` — 面板数据（`show_diagnosis`/`weekly_report` 已用）。
- `AdaptivePracticeService.create_practice(db, student_id, ...)` — 单生 ZPD 出题（工具已用）。
- `llm_chat`（`app.llm.router`）— 工具内调 LLM 的现成模式（`exam_tools` 的 `web_search` 已用）。
- `_route` 约定：`{"page": "exam-v2", "params": {...}}`；`_component` 约定：`{"type": ..., "action": "open", ...}`。
- `resolve_student_id(db, account_id)`（`app/api/deps.py`）仅做 Account.id→Student.id 映射，**不含中文姓名解析**——需新增。

设计文档 27/28/30 为动机来源（见 proposal.md - Why），不再复述。

## Goals / Non-Goals

**Goals:**
- 补齐 7 个工具的签名/语义缺口，使诊断-干预闭环在 Agent 对话里可用。
- 用一份专属规格固化工具契约（对标 `agent-exam-tools`）。
- 工具元数据与设计 30 §3.3 逐项对齐。

**Non-Goals:**
- 不动诊断引擎、ZPD 引擎、学习计划 REST API 等底层实现（它们已实现且有独立规格）。
- 不做 Guard L1 前置条件的 OR 语义扩展（见 Decisions）。
- 不实现 28 号文档「全题型 × 全障碍」蓝图（仅 `choice` 已落地，其余留作后续）。
- 不重构 ZPD 目录归属、不清理 `app/chem_skills` 空壳（YAGNI）。

## Decisions

### D1：中文姓名解析 — 新增 `resolve_student_by_identity`

- **选择**：新增一个服务层静态方法 `DiagnosisService.resolve_student_by_identity(db, identity: str)`，返回 `list[Student]`。
- **匹配策略**：纯数字 → 按 `Student.id` 精确查（单结果）；非数字 → 先按 `Student.name` 精确匹配，无果再按 `name.contains` 子串匹配；多结果按班级维度排序返回。
- **依据**：`resolve_student_id` 只做 account→student，不符合「姓名/ID 双输入」语义。放在 `DiagnosisService` 而非工具内，便于 `diagnose_barrier` 与未来工具复用。
- **备选**：(a) 直接在工具内联查询——拒绝，工具应薄封装不写查询逻辑；(b) 引入拼音/简称匹配——过度，留作未来扩展。

### D2：`diagnose_barrier` 两级分支

- **选择**：工具签名改为 `diagnose_barrier(student_id: int = 0, class_id: int = 0, student_name: str = "")`。分支：`student_name` 或 `student_id` 命中 → `get_student_diagnosis`；仅 `class_id` → `PanelService.get_barriers`。名称解析走 D1，多结果返回候选列表。
- **依据**：`get_class_diagnosis(db, class_id, exam_id)` 需 exam_id，而班级级诊断只需「各障碍类型为主导的学生人数与占比」；`PanelService.get_barriers(db, class_id)` 恰好返回 `[{barrier_type, count, percentage}]` 且无需 exam_id，故采用之，零新底层代码。

### D3：`assign_adaptive_practice` 班级级编排

- **选择**：工具签名改为 `assign_adaptive_practice(class_id: int = 0, student_id: int = 0, knowledge_point: str = "", count: int = 5)`。`student_id` 非零走现有单生路径；`class_id` 非零则查询班级学生，按每批 5 名顺序分批调用 `create_practice`，返回每生参数摘要（ZPD 难度、主导障碍、薄弱知识点、题目数）。
- **依据**：`create_practice` 是单生原语，班级级是工具层编排，不在服务层新增批量方法（保持服务原子性，符合设计 28 决策三「5 人/批」）。
- **备选**：在 `AdaptivePracticeService` 新增 `create_practice_for_class`——拒绝，会扩大服务 API 面，且预览语义（见 D4）下编排留在工具层更清晰。

### D4：`generate_learning_plan` 预览路由（不写库）

- **选择**：工具改为返回 `_route`（`{"page": "students", "params": {"student_id": ..., "action": "open_learning_plan"}}`），移除对 `LearningPlanService.create_plan` 的直接调用。持久化由前端抽屉确认后走既有 REST API（`learning-plan-api` 已规格化 `POST /api/v1/learning-plan`）。
- **依据**：学习计划有生命周期（预览→应用→发送），且设计 28 §6 明确「Agent 版本用于预览和确认，不写数据库」。直接写库绕过了审批/确认门控。

### D5：`weekly_report` LLM 自然语言周报

- **选择**：工具先用 `PanelService.get_student_detail`/`get_class_overview` 取面板数据，再调 `llm_chat` 用周报 prompt 生成 ≤200 字自然语言文本。prompt 模板为模块级常量，`temperature=0.3`、`max_tokens≈500`。
- **降级**：LLM 调用失败时回退返回结构化面板数据（保留现有行为），不阻断对话。
- **依据**：复用 `llm_chat` 的 provider 回退；prompt 内联常量而非独立文件，符合 `exam_tools` 现有风格（YAGNI）。

### D6：`show_students` 障碍过滤

- **选择**：工具签名增加 `barrier: str = ""`，透传给 `_component` params。前端据此筛选主导障碍学生。
- **依据**：现有 `show_students` 是纯路由工具（只回传 `class_id`+`keyword`，前端负责取数），障碍过滤同理透传即可，无需后端查询。

### D7：工具元数据对齐（含 call_limit 收紧）

- **选择**：按设计 30 §3.3 更新 `@register_tool`：`diagnose_barrier` call_limit=2、`show_diagnosis`=1、`show_students`=1、`weekly_report`=2、`assign_adaptive_practice`=1（requires_approval）、`generate_learning_plan`=5、`send_learning_plan`=2（requires_approval）。
- **关于 OR 前置条件**：设计 30 §5.2 的「student_id 或 class_id 至少一个非空」是 OR 语义，当前 Guard `prerequisites` 是 AND 语义（列表内全非空）。**不在本次扩展 Guard**——这些工具 `prerequisites` 置空，改由工具内部校验（无标识符时返回清晰错误），OR 校验作为未来 Guard 增强另立变更。

## Risks / Trade-offs

- **[call_limit 收紧可能影响现有测试]** → 同步更新测试断言；这些工具尚未作为 change 发布，收紧对齐设计无用户回归。
- **[名称模糊匹配歧义]** → 唯一命中直诊、多命中返回候选，绝不猜测；避免张冠李戴。
- **[LLM 周报依赖 LLM 可用性]** → 复用 `llm_chat` 多 provider 回退；仍失败则降级结构化数据（D5）。
- **[`_route` 前端页面支持]** → `students` 页是否已支持 `open_learning_plan` action 需前端确认；若未支持，标记为前端待办，不阻断本变更（工具返回的 `_route` 与页面桥接协议兼容）。

## Migration Plan

- 纯代码 + 规格变更，无数据/表结构迁移。
- 工具签名变更（`assign_adaptive_practice` 增 `class_id`、`diagnose_barrier` 增 `class_id`/`student_name`、`show_students` 增 `barrier`）为向后兼容的**新增参数**，旧调用仍可用；`generate_learning_plan` 行为从「写库」改为「路由」，属 pre-release 对齐。
- 回滚 = revert 本次 commit。

## Open Questions

- `generate_learning_plan` 的 `_route` 页面标识（`page`）与 action 参数名（`open_learning_plan`）需与前端 `students` 页确认——不影响规格，实施时对齐即可。
- 姓名解析是否需要支持「姓 + 简称/拼音」——当前「精确→包含」两级足够，可后续扩展。

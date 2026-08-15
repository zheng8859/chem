## Why

出题与题库是 ChemAI 教师端的核心工作流，但当前 7 个 Agent 工具（`search_exam_bank`、`web_search`、`show_exam_workbench`、`save_to_bank`、`generate_questions`、`list_banks`、`delete_bank`）处于「骨架在、血肉未接」状态：3 个会在运行时崩溃（字段名对不上 / 传错 schema），2 个是占位桩，且 call_limit/persona 元数据与 SSE 组件契约和设计文档（25 号「AI出题与题库管理系统设计」、30 号「Agent对话系统设计」）存在系统性漂移。教师目前无法通过 Agent 对话完成「搜题 → 出题 → 存库」的闭环。

## What Changes

- 修复 3 个运行时崩溃的工具：
  - `search_exam_bank`：当前调用 `list_items(set_id=None)` 且访问 `item.stem`/`item.knowledge_point`（实际字段为 `content`/`knowledge_point_tags`）
  - `save_to_bank`：当前把 `{stem, answer, ...}` 裸 dict 传给 `add_item(db, QuestionSetItemAdd)`，字段与 schema 完全不符
  - `generate_questions` 工具包装：对 Pydantic `QuestionRead` 对象调用 `.get("audit_passed")`
- 实现 `search_exam_bank` 三级搜索（关键词 → 向量 → 联网兜底），并接通 `web_search` 真实实现（LLM 摘要 ≤400 字）
- 实现 `save_to_bank` 三实体入库（`QuestionSet` + `Question` + `QuestionSetItem`）+ ChromaDB 增量同步 + `_route` 导航
- `generate_questions` 透传题型 / 变体题参数（服务层已支持，工具层未暴露）
- 对齐 7 个工具的 `call_limit` 与 `persona` 元数据（含 `web_search` 补 parent、`save_to_bank`/`list_banks`/`delete_bank`/`generate_questions` 补 tutor）
- 统一 SSE `_component`/`_route` 契约（`_component` 用 `props` 而非 `params`；`_route` 适配器不再包裹 `route` 键）

## Capabilities

### New Capabilities
- `agent-exam-tools`: 7 个出题与题库 Agent 工具的行为与元数据 —— 三级搜索、联网搜索、LLM 出题+四维审核、变体题透传、三实体入库 + ChromaDB 同步、题库列表 / 删除、`_component`/`_route` 返回契约。

### Modified Capabilities
- `agent-engine-core`: SSE `_component`/`_route` 契约形状对齐 —— `_component` 的载荷字段由 `params` 改为 `props`（与前端渲染器一致）；`_route` 适配器不再把 `_route` 包裹为 `{route: {...}}`，改为铺平为 `{page, params}`。

## Impact

- `chemai-backend/agent/tools/exam_tools.py` —— 7 工具实现与元数据
- `chemai-backend/app/agent/sse/adapter_v2.py` —— component/navigate 事件发射形状
- `chemai-backend/app/services/question_generation_service.py` —— 已支持变体/题型，仅工具层透传
- `chemai-backend/app/services/question_bank_service.py` —— save_to_bank 三实体入库复用
- `chemai-backend/frontend/pages/index.html` —— navigate handler 与 component props 契约
- 测试：`chemai-backend/tests/unit/`、`tests/integration/`（新增出题工具行为测试）

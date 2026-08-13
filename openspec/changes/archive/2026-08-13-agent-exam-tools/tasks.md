## 1. 工具元数据对齐

- [x] 1.1 修正 7 工具的 persona：`web_search` 补 `parent`（4 角色全可见）；`save_to_bank`/`list_banks`/`delete_bank`/`generate_questions` 补 `tutor`
- [x] 1.2 修正 7 工具的 call_limit：search=3、web=2、workbench=3、save=1、generate=5、list=1、delete=1
- [x] 1.3 更新 `tests/integration/test_agent_engine.py` 的 persona 工具集断言（web_search 进 parent 集合、save/list/delete 进 tutor 集合）

## 2. SSE `_component`/`_route` 契约对齐

- [x] 2.1 修 `app/agent/sse/adapter_v2.py`：navigate 事件载荷铺平为 `{page, params}`，去掉 `{route: {...}}` 包裹
- [x] 2.2 修 `show_exam_workbench`：返回 `_component: {type: "exam-workbench", props: {...}}`，删除失效的 `action`/`tabs` 字段
- [x] 2.3 补 SSE 事件形状单测（component 用 props、navigate 载荷铺平）

## 3. `search_exam_bank` 三层搜索

- [x] 3.1 重写关键词匹配层：改查 `Question` 表，字段改为 `content`/`knowledge_point_tags`/`difficulty`/`question_type`，修正当前 `item.stem`/`item.knowledge_point` 崩溃点
- [x] 3.2 接向量补充层：候选集用 `search_questions_vector` 重排，历年真题用 `VectorSearchService.search_similar` 补充
- [x] 3.3 接联网兜底层：前两层合计 < 3 且有关键词时调 `web_search`，结果带 `source`（bank/historical/web）并按 `(source, id)` 去重
- [x] 3.4 新增 `search_exam_bank` 单测（关键词命中 / 向量补充 / 联网兜底三路径）

## 4. `web_search` 真实实现

- [x] 4.1 实现 MiMo search 调用 + DeepSeek 摘要（≤400 字），无 `MIMO_API_KEY` 或调用失败时降级返回占位文案
- [x] 4.2 新增 `web_search` 单测（mock MiMo/DeepSeek，验证摘要截断与降级路径）

## 5. `generate_questions` 透传与修复

- [x] 5.1 新增 `question_types: list[str]` 与 `variant_qid: str` 入参并透传 `question_generation_service.generate_questions`
- [x] 5.2 修审核汇总：用 `QuestionRead.audit_status == "passed"` 统计，替代对 Pydantic 对象 `.get("audit_passed")` 的崩溃写法
- [x] 5.3 新增 `generate_questions` 单测（题型透传 / 变体题透传 / 审核汇总正确）

## 6. `save_to_bank` 三实体入库

- [x] 6.1 改批量签名 `questions: list[dict]` + 可选 `bank_name`，`bank_name` 为空时自动命名（时间戳 + 知识点）
- [x] 6.2 实现三实体入库：`create_question_set` → 逐题 `TeachingService.create_question`（`source=ai_generated`）→ `QuestionBankService.add_item` 建关联，单事务内异常回滚
- [x] 6.3 提交后 `index_questions` 增量同步 ChromaDB，成功后返回 `_route: {page: "exam-v2", params: {...}}`
- [x] 6.4 新增 `save_to_bank` 单测（三实体落库 / 自动命名 / 事务回滚 / `_route` 返回）

## 7. `list_banks` / `delete_bank` 复核

- [x] 7.1 复核 `list_banks` 输出字段（`id`/`name`/`item_count` 取自 `QuestionSetRead.question_count`）
- [x] 7.2 复核 `delete_bank`：`requires_approval` 门控生效、`is_system` 文件夹拒绝删除
- [x] 7.3 新增 `list_banks`/`delete_bank` 单测（列表 / 审批 / 系统预设拒绝）

## 8. 全量回归与校验

- [x] 8.1 跑 `pytest -k "agent"` 与新增出题工具测试全绿
- [x] 8.2 `openspec validate agent-exam-tools` 通过，无 spec/design/tasks 校验错误

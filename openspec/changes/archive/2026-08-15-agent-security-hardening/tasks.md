## Tasks

- [x] 1. `app/agent/guard.py`：GuardState 新增 `teacher_id`/`student_id`/`bound_student_ids` 字段 + `bind_identity()` 方法；`guard_tool_call_wrapper` 在 `check()` 前调用 `bind_identity`，拒绝则短路。
- [x] 2. `app/agent/engine/factory.py`：`create_agent_with_checkpointer` 增加 `teacher_id`/`student_id`/`bound_student_ids` 参数并透传 GuardState。
- [x] 3. `app/api/deps.py`：新增 `resolve_parent_bound_student_ids(db, account_id)` helper。
- [x] 4. `app/api/v1/chat.py`：`chat_stream` 按 persona 解析权威身份并透传；`resume_conversation` 修复 owner_id None fail-closed + `_resolve_persona` 重校验 + 透传 user_id。
- [x] 5. `agent/tools/browser_tools.py`：新增 `_validate_url` + `browse_navigate` 顶部校验（SSRF）。
- [x] 6. `app/agent/planner.py`：`PLAN_PROMPT` 分隔符包裹 `{message}` + 信任声明；`_plan_to_instruction` 加「仅供参考」声明。
- [x] 7. 测试：`tests/integration/test_agent_engine.py` 新增身份绑定测试 + Planner 加固测试；`tests/unit/test_browser_tools.py` 新增 SSRF 校验测试。
- [x] 8. 跑全量单测/集成测试 + Evals 确认无劣化。

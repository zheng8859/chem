## 1. Guard 纵深防御修复

- [x] 1.1 未知工具 fail-closed：`GuardState.check()` 中 `get_tool_meta` 返回 `None` 时由 `GuardResult(allowed=True)` 改为 `allowed=False, layer="L0"`，reason 提示「未在 TOOL_META 注册」
- [x] 1.2 dict 形态 content 剥离：`guard_tool_call_wrapper` 归一化工具结果（str→json.loads / dict→直接用 / 其他跳过），命中 `_component`/`_route` 时经 `strip_special_fields` 剥离并 `json.dumps` 重写 ToolMessage
- [x] 1.3 `_is_present` 契约：保留「0 = 未提供（仅 ID 哨兵）」语义，强化 docstring 明确该约定与适用边界
- [x] 1.4 抽取 `_args_json(args)` 助手，替换 `_make_dedup_key` 与 `_make_approval_id` 中重复的 `json.dumps(args, sort_keys=True, ensure_ascii=False, default=str)`

## 2. 类型标注与文档同步

- [x] 2.1 补齐 `guard_tool_call_wrapper(request, execute)` 参数/返回类型标注
- [x] 2.2 补齐 `_extract_tool_result(output)` 返回类型标注
- [x] 2.3 补齐 `get_thread_guard_state(thread_id)` 返回类型标注
- [x] 2.4 补齐 `_resolve_persona(user, requested_role)`、`_resume_stream(...)` 参数类型标注（另补 `_extract_guard_identity`、`_read_pending_approval_id`）
- [x] 2.5 同步 `student_name` 文档：确认 `diagnose_barrier` 描述/签名与 `prerequisite_any_of`（student_id/class_id/student_name）一致，spec 示例同步为三者 OR

## 3. 测试补全

- [x] 3.1 新增未知工具 fail-closed 测试（`get_tool_meta` 返回 None → 拒绝，layer=L0）
- [x] 3.2 新增 dict 形态 content 剥离测试（ToolMessage content 为 dict 时 `_component` 被剥离进 GuardState）
- [x] 3.3 新增 `_is_present` 契约测试（None/空串/0 → 未提供；非零/非空 → 提供）
- [x] 3.4 新增 `_args_json` 助手测试（去重键与审批 ID 参数序列化一致）

## 4. 验证

- [x] 4.1 全量 pytest 通过（无回归，覆盖新增用例）—— 1654 passed, 51 skipped

## Context

`agent-guard-wiring` 已实现 Guard L1–L4 四层护栏及 `guard_tool_call_wrapper`（`ToolNode(tools, awrap_tool_call=...)`），GuardState 通过 `Command(update={"guard_state": ...})` 跨 checkpoint 持久。code-review 后，越权防护（persona 由认证身份决定、线程归属、approval_id 绑定、fail-closed）已在 `app/agent/guard.py` / `app/api/v1/chat.py` / `app/agent/engine/factory.py` / `app/agent/sse/adapter_v2.py` 中落地但未提交、未进 spec。本 change 补 spec + 增量修复 6 个剩余项。

## Goals / Non-Goals

**Goals:**
- 把已实现的越权/fail-closed 行为固化进 delta spec。
- 未知工具 fail-closed、dict 形态 content 剥离、类型标注、去重助手、`_is_present` 契约、`student_name` 文档同步。

**Non-Goals:**
- 不引入新的 Guard 层级（L0 之外）。
- 不改动 `prerequisites`/`prerequisite_any_of` 的注册语义。
- 不重构 Guard 与 ToolNode 的挂载方式。

## Decisions

1. **未知工具 fail-closed 而非放行** — 已核实全部工具（含 5 个浏览器工具）都经 `@register_tool` 注册，`get_tool_meta` 返回 `None` 只发生在「漏注册 / meta 名拼错」这类真 bug。改为 `GuardResult(allowed=False, layer="L0")` 与 fail-closed 哲学一致，无合法放行场景。备选「保留放行 + 日志告警」被否：会让漏登记静默化且绕过四层防护。

2. **dict 形态 content 剥离：在 wrapper 内归一化** — `guard_tool_call_wrapper` 现仅处理 `isinstance(content, str)`。改为先归一化：str 尝试 `json.loads`，dict 直接用，其余（list/多模态）跳过。命中 `_component`/`_route` 时经 `strip_special_fields` 剥离后以 `json.dumps(clean)` 重写 ToolMessage。备选「要求工具一律返回字符串」被否：侵入工具实现且无法约束未来工具。

3. **`_is_present` 保留 0 = 未提供，明确契约** — 当前全部 `prerequisites`/`prerequisite_any_of` 参数均为 ID 哨兵（`plan_id`/`bank_id`/`session_id`/`student_id`/`class_id`，默认 0），把 0 当「未提供」是正确语义；改为 0=提供会破坏 `diagnose_barrier` 的 any_of。故不改变行为，仅强化 docstring 说明「0 仅对 ID 哨兵视为未提供」并补单测锁定契约。备选「0 一律视为提供」被否：需改工具默认值 + 破坏 any_of。

4. **去重助手 `_args_json`** — `_make_dedup_key` 与 `_make_approval_id` 重复同一行 `json.dumps(args, sort_keys=True, ensure_ascii=False, default=str)`，抽为模块级 `_args_json(args)` 供两处调用，消除未来改一处漏一处导致去重键/审批 ID 分叉的风险。

5. **类型标注按 CLAUDE.md 3.3 补齐** — 目标：`guard_tool_call_wrapper(request, execute)`、`_extract_tool_result(output)`、`get_thread_guard_state(thread_id)`、`_resume_stream(...)`、`_resolve_persona(user, requested_role)` 等无标注签名补齐参数/返回类型，不改逻辑。

## Risks / Trade-offs

- [未知工具 fail-closed 可能拦截未来未登记工具] → `validate_tool_integrity()` 已在启动/测试时告警漏登记；fail-closed 的错误信息显式提示「未在 TOOL_META 注册」，便于定位。
- [dict 剥离归一化引入分支复杂度] → 归一化集中在 wrapper 内一小段，`strip_special_fields` 复用不变；新增 dict 用例锁定。
- [`_is_present` 契约仅文档化，未来非 ID 数值参数仍可能踩坑] → 单测 + docstring 显式标注「仅 ID 哨兵」，未来新增非 ID 数值参数时须另行评估。
- [类型标注为纯质量项，无运行收益] → 低风险、机械改动，符合项目规范成本可控。

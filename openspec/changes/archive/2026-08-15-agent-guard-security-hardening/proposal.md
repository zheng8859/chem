## Why

上一变更 `agent-guard-wiring` 落地了 Guard L1–L4 四层护栏，但 code-review 发现两条纵深防御缺口：(1) 越权防护依赖请求体 `context.role` 而非 JWT 认证身份，且 resume 端点缺少线程归属校验，可被跨角色工具泄漏 / 越权恢复攻击；(2) Guard 在「护栏状态缺失」时放行、在「工具未登记 TOOL_META」时放行，与 fail-closed 安全哲学相悖。此外还有若干代码质量项（类型标注、重复代码、`_is_present` 数值 0 语义、非字符串 content 剥离）未处理。

## What Changes

- **越权防护（已实现，补 spec）**：persona 由 JWT 认证身份决定（teacher→teacher/tutor、student→student、parent→parent），请求体 `context.role` 视为不可信，越权请求返回 403。
- **线程归属 + 审批绑定（已实现，补 spec）**：`GuardState` 持久化 `user_id`，`/chat/resume` 校验线程归属（跨用户 403）与 pending approval_id 匹配（错配 409）。
- **fail-closed 纵深防御（已实现，补 spec）**：护栏状态缺失时拒绝执行；新增 L0 角色校验（Guard 层兜底拦截绕过工具过滤的越权调用）。
- **未知工具 fail-closed（新修）**：`get_tool_meta` 返回 `None` 时由「放行」改为「拒绝执行」，避免工具漏登记 meta 时静默绕过四层护栏。
- **非字符串 content 剥离（新修）**：`_component`/`_route` 剥离兼容 dict 形态的工具结果（当前仅处理 JSON 字符串）。
- **代码质量（新修）**：补齐函数签名类型标注（CLAUDE.md 3.3）、抽取 `_args_json` 去重助手、明确 `_is_present` 数值 0 契约、`student_name` 文档同步。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `agent-chat-api`: 「Unified SSE chat streaming endpoint」persona 由认证身份决定、越权 403；「Approval resume endpoint」线程归属校验 403 + approval_id 绑定 409。
- `agent-engine-core`: 「Guard four-layer safety」新增 L0 角色校验、fail-closed、GuardState.user_id、未知工具 fail-closed、`_is_present` 契约；「SSE event adapter」剥离兼容 dict 形态 content。

## Impact

- **代码**：`app/agent/guard.py`、`app/agent/engine/factory.py`、`app/agent/sse/adapter_v2.py`、`app/api/v1/chat.py`（均已含前序未提交改动，本次在其上增量修复）。
- **测试**：`tests/integration/test_agent_engine.py` 新增 L0/未知工具/dict 剥离用例；`tests/unit/` 补充 `_is_present` 契约测试。
- **无 API 破坏**：`/chat/stream`、`/chat/resume` 签名不变，仅收紧校验语义（新增 403/409 分支）。
- **依赖**：无新增。

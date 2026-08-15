## Why

Phase 6 收尾前的安全审计发现 4 个 HIGH 级漏洞，均可在工具层造成越权或注入：

1. **IDOR（水平越权）**：身份参数（`student_id`/`teacher_id`）直接来自 LLM 生成的工具实参，未经 JWT 认证身份绑定。学生可通过 `memory_student_get(student_id=他人)` 读取任意学生档案；家长可通过 `generate_parent_report`/`diagnose_barrier` 读取任意子女数据；`teacher_id` 未绑定且当前 `teacher_id = user.user_id`（Account.id）与工具期望的 `Teacher.id` 类型不符。
2. **SSRF**：`browse_navigate(url)` 无 URL 校验，可访问内网地址（127.0.0.1 / 169.254.169.254 云元数据 / 私网网段 / file:// 等）。
3. **resume fail-open**：`/chat/resume` 当 guard_state 缺 `user_id` 时跳过归属校验（`owner_id is not None and ...`），且重建 Agent 不复用 `_resolve_persona`，存在越权重放风险。
4. **Planner 提示注入**：`PLAN_PROMPT` 中 `{message}` 未加分隔符与信任声明，用户消息可注入指令操纵规划输出；`_plan_to_instruction` 将 LLM 生成的 `intent`/`args_hint` 作为 system 指令原样下发，无「仅供参考」声明。

## What Changes

- **身份参数绑定（防 IDOR）**：在 Guard 层新增身份绑定步骤，把 `teacher_id` 强制绑定到认证教师、`student_id` 对学生绑定到本人、对家长校验绑定关系；入口 `chat_stream` 从 JWT 解析权威身份（`Teacher.id`/`Student.id`/绑定子女集合）写入 GuardState。
- **SSRF 防护**：`browse_navigate` 增加 URL 校验，仅放行 http/https，拒绝回环/链路本地/私网/保留地址与 file:// 等非 http 协议。
- **resume fail-closed**：`owner_id` 为 None 时拒绝重放；重建 Agent 前用 `_resolve_persona` 校验线程 persona 与认证角色一致。
- **Planner 注入加固**：`PLAN_PROMPT` 用分隔符包裹 `{message}` 并加信任声明；`_plan_to_instruction` 加「计划仅供参考」声明。

## Capabilities

### New Capabilities

（无新能力，均落在既有能力的既有需求上）

### Modified Capabilities

- `agent-engine-core`: 新增「身份参数绑定（IDOR 防护）」与「Planner 提示注入加固」需求。
- `agent-chat-api`: 修改「Approval resume endpoint」需求（fail-closed 归属校验 + persona 重校验）。
- `agent-tools`: 新增「浏览器工具 URL 校验（SSRF 防护）」需求。

## Impact

- `app/agent/guard.py` — GuardState 新增身份字段 + `bind_identity` 绑定步骤。
- `app/agent/engine/factory.py` — `create_agent_with_checkpointer` 透传权威身份到 GuardState。
- `app/api/v1/chat.py` — `chat_stream` 入口身份解析；`resume_conversation` fail-closed 修复。
- `app/api/deps.py` — 新增 `resolve_parent_bound_student_ids` helper。
- `agent/tools/browser_tools.py` — `browse_navigate` URL 校验。
- `app/agent/planner.py` — `PLAN_PROMPT` 分隔符 + `_plan_to_instruction` 声明。
- 测试：`tests/integration/test_agent_engine.py`（身份绑定/Planner）、`tests/unit/test_browser_tools.py`（SSRF 新增）。

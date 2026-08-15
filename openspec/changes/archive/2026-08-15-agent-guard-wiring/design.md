## Context

`app/agent/guard.py` 已定义 `GuardState`（四层护栏状态）和 `wrap_tool_node`（langgraph 0.2 函数式 tool_node 包装器），并有完整单元测试。但 `app/agent/engine/factory.py` 的 `create_agent_with_checkpointer` 把裸工具列表直接传给 `create_react_agent`，`wrap_tool_node` 从未被调用，`guard_state.check()` 在真实 ReAct 循环中不生效；只有 `sse/adapter_v2.py` 用 `guard_state.strip_special_fields()` 做前后端字段剥离。

环境实际安装 **langgraph 1.1.10**（requirements.txt 写 `>=0.2.0` 已失真）。1.1.10 的 `ToolNode.__init__` 提供官方拦截挂点 `wrap_tool_call` / `awrap_tool_call`，签名 `(ToolCallRequest, execute) -> ToolMessage | Command`，`ToolCallRequest` 携带 `tool_call` / `tool` / `state` / `runtime`。`create_react_agent` 已标记 deprecated（迁移目标是 `langchain.agents.create_agent`，需新增 `langchain` 包，本变更不迁移）。

## Goals / Non-Goals

**Goals:**
- 让 L1–L4 四层护栏在每次工具执行前真实生效，被拒工具绝不执行。
- 审批门控走 LangGraph 原生 interrupt/resume，`/chat/resume` 真实恢复执行并继续 SSE 流。
- 补齐 L1 的长度校验与 OR 条件语义，替换 `wrap_tool_node` 死代码。

**Non-Goals:**
- 不迁移到 `create_agent` / 新增 `langchain` 依赖（独立后续提案）。
- 不改变 `GuardState` 的对外方法语义（`check`/`record_execution`/`approve`/`reject`/`strip_special_fields` 保留）。
- 不新增工具、不动 Persona 过滤、不动 MCP。

## Decisions

### D1 — 用 `awrap_tool_call` 拦截器接入 Guard（而非其他挂点）

在工厂函数中构造自定义 `ToolNode(tools, awrap_tool_call=guard_wrapper)` 传给 `create_react_agent(tools=...)`，拦截器在每次工具执行前运行。

- **理由**：这是 langgraph 1.x 为「工具执行前拦截 + 短路返回」设计的一等公民挂点，签名与 Guard 语义完全匹配——被拒时短路返回 `ToolMessage` 不调 `execute`，放行时调 `execute` 后剥离特殊字段。
- **备选**：
  - `post_model_hook`：在 LLM 之后、工具之前运行，是状态变换节点，不适合逐工具短路注入拒绝消息。
  - 手写 StateGraph 替代 `create_react_agent`：改动面大、失去 prebuilt 便利，YAGNI。
  - 迁移 `create_agent` + middleware：需新增 `langchain` 依赖，与 Guard 接线正交，延后。

### D2 — GuardState 放进图状态（state_schema），而非闭包捕获

用自定义 `state_schema`（扩展 `MessagesState`）增加一个 `guard_state` 字段，拦截器从 `request.state["guard_state"]` 读取并回写。

- **理由**：审批 interrupt 会把图状态 checkpoint；`/chat/resume` 是独立请求、会重建 agent 与闭包。若 GuardState 只活在闭包里，L2 计数、L3 去重键、审批队列会在 resume 后全部丢失。放入图状态才能跨 interrupt/resume 持久。
- **备选**：闭包捕获 `guard_state`（现状思路）——仅单请求内有效，无法支撑审批中断恢复，被否决。

### D3 — L4 审批用 `interrupt()` + `Command(resume=...)`

拦截器对 `requires_approval=True` 且未审批的工具调用 `interrupt(approval_payload)` 暂停图；`/chat/resume` 调 `agent.ainvoke(Command(resume={"approved": bool}), config)` 恢复，拦截器从 `interrupt()` 的返回值拿到决策。

- **理由**：`interrupt()` 在节点内阻塞并在 resume 时返回 resume 值，是 LangGraph 人在回路的原生机制；`Command` 已确认有 `resume` 参数、`langgraph.types` 已确认可导入 `interrupt`。
- **备选**：`interrupt_before=["tools"]`——对所有工具调用一律暂停，粒度太粗，需额外路由逻辑区分「哪些工具要审批」，被否决。

### D4 — 扩展 TOOL_META 前置条件表达 OR 与长度

`register_tool` 的 `prerequisites`（现为 `list[str]`，全部必填）保持兼容，新增两个可选元数据字段：`prerequisite_any_of: list[list[str]]`（每组内至少一个非空）与 `prerequisite_min_length: dict[str, int]`（参数最小长度）。`GuardState.check` 的 L1 依次校验：必填参数、any_of 组、min_length。`diagnose_barrier` 声明 `prerequisite_any_of=[["student_id", "class_id"]]`，`search_exam_bank` 声明 `prerequisite_min_length={"keyword": 3}`。

- **理由**：显式声明式，复用现有 TOOL_META 注册中心，与设计文档 §5.2 一致。
- **备选**：把 `prerequisites` 改成结构化 dict——破坏现有注册代码与测试的兼容性，被否决。

### D5 — 删除 `wrap_tool_node`，保留 `GuardState`

`wrap_tool_node` 是 langgraph 0.2 死代码，删除；新增 `guard_tool_call_wrapper`（或 `build_guard_wrapper`）产出拦截器。`GuardState` 类与方法不变，仅把 `check` 的 L1 逻辑扩展（D4）。

## Risks / Trade-offs

- **`create_react_agent` 已 deprecated** → 本变更不迁移，`requirements.txt` 收紧为 `langgraph>=1.1,<2` 锁定当前行为；迁移单列后续提案，避免被大版本升级打断。
- **`interrupt()` 在异步拦截器中的行为** → 需在实现时用集成测试验证异步 `awrap_tool_call` 内调用 `interrupt()` 能正确暂停/恢复；若异步上下文不支持则回退到同步 `wrap_tool_call`（D1 已保留同步钩子）。
- **GuardState 序列化进 checkpoint** → `GuardState` 含 `dict`/`set` 字段，需确保其经 LangGraph 默认序列化器可往返；`set` 若不被支持则改存为 `list`（去重键去重后再转 list）。
- **SSE 剥离字段的读法变化** → `adapter_v2.py` 现从 bundle 的 `guard_state` 读 `stripped_components/stripped_routes`；改后应从图状态/流事件读取，需同步适配并保持 `component`/`navigate` 事件不变。
- **审批等待的 SSE 事件** → 现有 `phase` 事件类型已含 `awaiting_approval`，需在 interrupt 触发时由 SSE 适配器发射该 phase 事件，前端审批卡片逻辑复用。

## Migration Plan

1. 实现新拦截器 + state_schema + 工厂改造，本地跑 `pytest tests/integration/test_agent_engine.py` 确认 Guard 层测试仍绿。
2. 新增「拦截器在 ReAct 循环生效」「审批 interrupt→resume 端到端」集成测试。
3. 收紧 `requirements.txt`，跑全量测试与 Evals 基线对比，确认无劣化后合并。
4. 回滚：变更为纯代码 + 配置，无 schema/迁移脚本，直接 revert 提交即可。

## Open Questions

（无——所有影响规格或任务分解的决策已在本设计中确定。）

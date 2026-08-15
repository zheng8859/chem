## Why

设计文档（30号 §5）承诺的四层护栏（L1 前置 / L2 限次 / L3 去重 / L4 审批）在 `guard.py` 中已定义并通过单元测试，但从未接入 ReAct 工具执行路径——工厂函数 `create_agent_with_checkpointer` 把裸工具列表直接传给 `create_react_agent`，`wrap_tool_node` 无人调用，`guard_state.check()` 在真实执行中从不触发。审批恢复端点 `/chat/resume` 也是 stub（只回文本，不恢复执行）。这是「设计已承诺、代码已写好、测试已通过，但生产路径没生效」的安全缺口：LLM 当前可以无限制重复调用同一工具，破坏性操作不经审批门控。

根因是版本错配：`guard.py` 的 `wrap_tool_node` 按 langgraph 0.2 的函数式 `tool_node(state)->dict` 写法设计，而环境实际安装的是 langgraph 1.1.10（类式 `ToolNode` + `create_react_agent`）。1.1.10 自带了官方拦截挂点 `ToolNode(awrap_tool_call=...)`，无需放弃 prebuilt 或手写 StateGraph。

## What Changes

- **接入 Guard 到工具执行路径**：工厂改用自定义 `ToolNode(awrap_tool_call=guard_wrapper)` 传给 `create_react_agent`，让 L1–L4 检查在每次工具执行前真实生效。
- **审批改走 LangGraph 原生 interrupt/resume**：L4 审批用 `interrupt_before=["tools"]` 暂停图 + `Command(resume=...)` 恢复，取代当前「GuardState 队列 + 假恢复」的 stub。
- **实现真正的审批恢复**：`/chat/resume` 从静态文本 stub 改为从 checkpoint 恢复中断、注入审批结果并继续 SSE 流。
- **替换死代码**：`guard.py` 的 `wrap_tool_node`（langgraph 0.2 写法，已无人调用）删除，由新的 `guard_tool_call_wrapper` 取代；`GuardState` 类保留。
- **修正 L1 前置条件语义**：`guard.py` 的 L1 目前只校验参数非空，补齐设计文档 §5.2 定义的长度校验（如 `keyword` > 2 字符）与「至少一个非空」的 OR 语义（如 `student_id` 或 `class_id`）。
- **修正依赖版本约束**：`requirements.txt` 的 `langgraph>=0.2.0` 已失真（实际 1.1.10），收紧为 `>=1.1,<2`。

## Capabilities

### New Capabilities

（无——本次不新增能力，全部是既有能力的接线与行为澄清。）

### Modified Capabilities

- `agent-engine-core`: Guard 四层护栏从「已定义但未接入」改为「在每次工具执行前真实拦截」；审批门控从 GuardState 队列改为 LangGraph 原生 interrupt/resume；L1 前置条件语义补齐（长度校验 + OR 条件）。
- `agent-chat-api`: `/chat/resume` 审批恢复端点从静态文本 stub 改为真正从 checkpoint 恢复中断、注入审批结果并继续 SSE 流。

## Impact

- **代码**：`app/agent/engine/factory.py`（改用自定义 ToolNode）、`app/agent/guard.py`（新增 guard_tool_call_wrapper，删除 wrap_tool_node，L1 语义补齐）、`app/api/v1/chat.py`（resume 真实恢复 + interrupt 配置）、`app/agent/sse/adapter_v2.py`（如审批等待的 phase 事件接入 interrupt）。
- **依赖**：无新增依赖；收紧 `requirements.txt` 中 `langgraph` 版本约束为 `>=1.1,<2`。不迁移到 `langchain.agents.create_agent`（需新增 `langchain` 包，是独立事项）。
- **测试**：`tests/integration/test_agent_engine.py` 中 Guard 层测试已覆盖 `GuardState` 逻辑，需新增「Guard 拦截器在 ReAct 循环中真实生效」的集成测试与「审批 interrupt → resume」端到端测试。
- **风险**：`create_react_agent` 在 langgraph 1.1.10 已标记 deprecated（但仍可用），本变更保持现状不迁移；迁移作为后续独立提案。

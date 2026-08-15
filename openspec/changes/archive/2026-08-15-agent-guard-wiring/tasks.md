## 1. TOOL_META 前置条件扩展（D4）

- [x] 1.1 `register_tool` 新增可选元数据 `prerequisite_any_of: list[list[str]]` 与 `prerequisite_min_length: dict[str, int]`，写入 `_tool_meta` 条目并保留 `prerequisites` 向后兼容
- [x] 1.2 `diagnose_barrier` 注册声明 `prerequisite_any_of=[["student_id", "class_id", "student_name"]]`（含姓名，对齐 §3.3 名称解析）；`search_exam_bank` 声明 `prerequisite_min_length={"keyword": 3}`
- [x] 1.3 单测：`validate_tool_integrity` 校验新增元数据字段类型合法；`get_tool_meta` 返回完整新字段

## 2. GuardState L1 逻辑扩展与序列化（D2/D4）

- [x] 2.1 `GuardState.check` 的 L1 依次校验：必填参数非空 → any_of 组至少一个非空 → min_length 长度达标，任一层失败返回 `layer="L1"` 拒绝结果
- [x] 2.2 单测：`diagnose_barrier` 传空 student_id/class_id 触发 L1 拒绝；`search_exam_bank` keyword 长度 ≤2 触发 L1 拒绝；长度达标放行
- [x] 2.3 确认 `GuardState`（含 `dict`/`set` 字段）可经 LangGraph 默认序列化器（msgpack）往返，`set` 无损，无需改存 `list`
- [x] 2.4 单测：`GuardState` 序列化往返后 `tool_call_counts`/`dedup_keys`/`approval_queue` 不丢失

## 3. 图状态 schema 接入 GuardState（D2）

- [x] 3.1 新增自定义 `state_schema`（扩展 `MessagesState`）增加 `guard_state` 字段
- [x] 3.2 工厂函数把 `GuardState` 实例注入初始图状态，替代当前 bundle 单独回传的方式

## 4. Guard 拦截器（D1/D3）

- [x] 4.1 在 `guard.py` 新增 `guard_tool_call_wrapper`（异步 `awrap_tool_call` 签名）：读 `request.state["guard_state"]` → `check()` → 拒绝则短路返回带 `{error, layer}` 的 `ToolMessage`；L4 未审批则 `interrupt(approval_payload)`；放行则 `record_execution` + `execute` + `strip_special_fields`
- [x] 4.2 单测：mock `ToolCallRequest` 验证 L1/L2/L3 拒绝短路不调 `execute`、放行调 `execute` 且剥离 `_component/_route`

## 5. 工厂函数改造（① D1）

- [x] 5.1 `create_agent_with_checkpointer` 构造自定义 `ToolNode(tools, awrap_tool_call=guard_wrapper)` 传给 `create_react_agent`，替代裸工具列表
- [x] 5.2 集成测试：用 mock LLM 跑一次 ReAct 循环，验证同一工具超 `call_limit` 后第二次调用被 L2 拒绝、不执行工具函数

## 6. 审批 interrupt/resume 与 `/chat/resume`（④ D3）

- [x] 6.1 `/chat/resume` 从静态文本 stub 改为：加载 checkpoint → `agent.ainvoke(Command(resume={"approved": bool}), config)` → 恢复执行并继续 SSE 流
- [x] 6.2 集成测试：审批门控工具触发 interrupt → SSE 发射 `awaiting_approval` phase → resume 后工具执行；拒绝路径工具不执行且 Agent 告知取消
- [x] 6.3 确认异步 `awrap_tool_call` 内 `interrupt()` 能正确暂停/恢复；不支持则回退同步 `wrap_tool_call`（D1 风险项）

## 7. SSE 适配器适配（D5 风险项）

- [x] 7.1 `adapter_v2.py` 的 `strip_special_fields`/`stripped_components`/`stripped_routes` 改为从图状态读取，保持 `component`/`navigate` 事件格式不变
- [x] 7.2 在 interrupt 触发时由 SSE 适配器发射 `phase: awaiting_approval` 事件

## 8. 清理死代码与版本约束（②⑤ D5）

- [x] 8.1 删除 `guard.py` 的 `wrap_tool_node`，移除 `factory.py` 中相关 import
- [x] 8.2 `requirements.txt` 收紧 `langgraph>=1.1,<2`，并同步 `langgraph-checkpoint-sqlite` 版本约束
- [x] 8.3 全量 `pytest` + Evals 基线对比，确认无劣化

## 9. 文档与规格同步

- [x] 9.1 更新 `CONTEXT.md` / `docs/agent-architecture.md` 中 Guard 接线说明（若提及 wrap_tool_node 或「护栏待接入」）
- [x] 9.2 `/opsx:sync` 同步 delta spec 到主 spec（归档前）

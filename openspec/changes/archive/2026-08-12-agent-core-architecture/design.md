# Agent 核心架构 — 技术设计

## Context

项目已有完整的 REST API 层（143 端点、26 Service 模块）和 chem_skills 引擎（parser + diagnosis 完整实现，memory 4 模块未导出）。但 Agent 引擎层为零——没有 ReAct、Gateway、Guard、SSE 适配器。学生端和家长端虽已有聊天 UI，但后端绕过 LangGraph 直接裸调 LLM。参见 proposal.md 了解动机。

已有基础设施：SQLite（主库 + checkpoint + memory 三文件）、ChromaDB 向量检索、LangGraph ≥0.2、FastAPI SSE 原生支持、6 个 JS 前端模块（sse-client.js、agent-renderer.js 等）。

## Goals / Non-Goals

**Goals:**
- 实现 30号文档定义的完整 Agent 引擎：Gateway → Planner → ReAct → Guard → SSE
- 30 个工具通过 `@register_tool` 统一注册，4 套 Persona YAML 配置
- 统一 `/api/v1/chat/` 端点，替代现有分散的家长/学生裸 LLM 端点
- 三层上下文裁剪 + LLM 摘要 + 学生上下文注入
- JSONL 审计日志记录所有工具执行
- 三级 LLM Provider 回退（MiMo → 通义千问 → DeepSeek）

**Non-Goals:**
- 不做 v1 Multi-Agent（决定：只做 v2 单 Agent）
- 不做 MCP Server（30号 §12，延后到后续 Phase）
- 不迁移 exam/diagnosis/ocr 等现有 REST 端点——只新增 chat 路由
- 不做 WebSocket 传输层（只做 SSE + 预留传输适配器接口）
- 不做离线 Agent
- 不做多 Agent 协作

## Decisions

### D1: 单 Agent ReAct v2（不做 v1 Multi-Agent）

**选择**：只实现 LangGraph `create_react_agent` v2，不实现 v1 Coordinator+Router 架构。

**理由**：v2 路由准确率 87% vs v1 75%，代码量 ~188 行 vs ~372 行，状态管理用 LangGraph 内置 `MessagesState` 而非自定义 12 字段。v1 设计中的"回退"价值不成立——如果 v2 出问题，v1 路由准确率更低、更不可靠。

**备选方案**：保留 v1 作为 `version` 参数切换（30号原设计），但维护成本高且实际降级价值为负。

### D2: Gateway 瘦身为 Provider 选择器

**选择**：Gateway 只做 Provider 选择（视觉 vs 推理），不做意图分类（chat vs navigate）、工具推荐（最多 3 个）、关键词兜底。

**理由**：意图分类被 ReAct system prompt 吸收（"如果用户只是打开页面，直接返回 _route"），工具推荐在 Persona 过滤后（2-8 工具）已无必要（30→8 比 30→3→1 更简单），关键词兜底移到前端（识别纯导航意图直接不走 Agent）。保留 Provider 选择因为 ReAct 内部无法切换模型——必须在 Agent 构建前决定。

**备选方案**：30号原设计——每次用户输入都走 Gateway LLM 调用，为 90% chat 消息增加延迟和成本。

### D3: Guard 作为中间件包装 + TOOL_META 元数据

**选择**：Guard 作为 ReAct tool_node 外层包装（对工具函数透明），元数据从 `@register_tool` 参数读取。四层检查顺序：L1 前置条件 → L2 次数限制 → L3 去重 → L4 审批门控。

**理由**：工具函数保持纯粹（"收到参数 → 执行业务 → 返回结果"），Guard 逻辑集中在一个模块。`@register_tool` 已有 `call_limit`，只需扩展 `requires_approval` 和 `prerequisites`。GuardState 请求级实例，状态不跨请求共享。

**备选方案**：装饰器直接包裹工具（工具感知 Guard），会污染工具的独立可测试性。

### D4: Planner 每次消息都调用 + 独立超时

**选择**：Planner 在每条用户消息进入 ReAct 前执行。单意图消息走 `single_step_fallback` 返回 1 步 Plan，复杂消息拆为 ≤ 6 步。`inject_dependencies` 用正则 `${step_N.field}` 替换前序步骤输出。Planner LLM 调用设独立超时 5 秒——超时直接走 `single_step_fallback` 返回单步 Plan，不阻塞主流程。

**理由**：Planner 不是处理"复杂度"的，是保"准确率"的——每一步只面对一个明确工具调用，从"8 选 1"降为"确认当前 step 的工具"，这是 87% 准确率的关键支撑。额外 1 次 LLM 调用换取更高工具选中率是值得的。但 Planner 和 ReAct 串行执行——如果 Planner 的 LLM 调用超时（P99 15s），ReAct 永远不启动。独立 5s 超时 + fallback 确保最坏情况下 Agent 仍能响应（以降低拆解精度为代价）。

**备选方案**：仅多意图消息调 Planner、ReAct 直接承接所有消息、不做 Planner——每种都会降低工具选择准确率。不用独立超时而共享超时——Planner 卡住会连带阻塞整个请求。

### D5: 统一 `/api/v1/chat/` 端点

**选择**：所有角色通过 POST /api/v1/chat/stream + `context.role` 区分 Persona。废弃 `/api/v1/parent/agent/*` 和旧学生 SSE 端点。

**理由**：ReAct 引擎、Guard、SSE 适配器对任何角色都是同一套代码——换 Persona 只是换 YAML 路径 + System Prompt。7 个端点在统一路径下：GET conversations（prefix 过滤）、GET history/{thread_id}、POST new、DELETE conversations/{thread_id}、POST stream、POST resume、POST reset。

**备选方案**：分角色端点（`/chat/teacher/stream`、`/chat/student/stream`）——代码重复，新角色需要新路由。

### D6: 工具调用已有 Service 层

**选择**：Agent 工具直接 import 已有 Service 函数，不新建 chem_skills engines/。parser 和 diagnosis 引擎照常 import，exam/memory/notification/improvement 工具调 Service，4 个新 tutoring 引擎（equilibrium/ionic/redox/stoichiometry）新建 chem_skills 目录。

**理由**：26 个 Service 模块已有完整业务逻辑和集成测试。Agent 工具的角色是"自然语言 → 服务调用"的适配层，不是重新实现。

**备选方案**：每个工具建新 engine——增加间接层，维护成本翻倍，与现有 Service 测试重复。

### D7: SSE 特殊字段在 Guard 层剥离

**选择**：Guard 执行工具后、返回给 LLM 前，剥离 `_component` 和 `_route`，分别写入 GuardState 供 SSE 适配器读取。

**理由**：Guard 是工具执行包装层，天然是剥离点。SSE 适配器只负责序列化，不应理解工具返回语义。剥离逻辑只需检查两个 key，不增加复杂度。

**备选方案**：SSE 适配器剥离——适配器需要理解工具返回结构，职责不清晰。

### D8: 上下文裁剪保留 LLM 摘要

**选择**：消息 > 30 条时触发三层裁剪：无条件保留最近 6 条 + 15 个教学关键词过滤 + 丢弃 ≥ 10 条时 LLM 摘要（≤ 200 字）。摘要缓存 per checkpoint，不重复生成。

**理由**：LLM 摘要在化学教学领域虽可能丢失精度，但比硬截断能保留语义（"上次的氧化还原练习错误集中在电子转移计算" vs 完全丢失）。缓存机制避免重复摘要消耗。

**备选方案**：硬截断（省成本但丢信息）、只保留 Layer 1（省成本但丢关键词消息）、不做裁剪（token 爆炸）。

### D9: 教师端改造现有 index.html

**选择**：基于 `pages/index.html` 的 CSS 骨架加载 `sse-client.js` + `agent-renderer.js`，仿照学生端 `pages/m/index.html` 实现消息循环。新增 4 个教师工具渲染器和 3 个内联面板（exam-workbench、diagnosis、student-list）。

**理由**：index.html 已有完整 CSS（气泡、输入框、侧边栏），只缺 JavaScript。学生端是经过验证的参考实现。Vue 3 组件化重写更好但工程量大，不适合 Agent 引擎同步交付的节奏。

**备选方案**：Vue 3 重写（长期最优但耗时）、新建独立 chat.html（多一份维护）。

### D10: LLM Provider 三级回退 + 指数退避 + 熔断器

**选择**：首选 MiMo-V2.5（视觉+联网）→ 备选通义千问 qwen-turbo（最快 1.8s）→ 兜底 DeepSeek-V4-Flash（化学满分）。每级 3 次重试，指数退避（1s → 2s → 4s）。通过环境变量配置 endpoint + key。统一的 `model_factory` 函数按 Provider 标识返回 `ChatOpenAI` 兼容实例。增加**熔断器**状态机防止重复调用已故障的 Provider：

```
CLOSED（正常）──连续失败 3 次──→ OPEN（熔断，30s 内直接跳过）
OPEN ──30s 后──→ HALF_OPEN（放行 1 次试探）
HALF_OPEN ──成功──→ CLOSED（恢复）
HALF_OPEN ──失败──→ OPEN（重新计时 30s）
```

熔断状态在进程内存中维护（重启清零），每个 Provider 独立一个熔断器。

**理由**：38号实测数据：MiMo 唯一支持视觉+联网搜索（P99 15.2s），通义千问最低延迟（P99 5.1s），DeepSeek 化学满分+成本最低。但没有熔断器时，MiMo 故障会导致每个请求重试 3 次（浪费 7s），100 个请求 = 700 秒无效等待。熔断器 OPEN 后直接跳过故障 Provider，请求延迟不增加。

**备选方案**：单 Provider（无容错）、随机轮询（延迟不稳定）、自部署开源模型（种子期 ROI 不匹配）、纯重试无熔断（故障 Provider 持续拖慢所有请求）。

### D11: 三数据库文件

**选择**：主库（chemai.db — 业务数据）+ checkpoint.db（LangGraph AsyncSqliteSaver — Agent 对话状态）+ memory.db（LangGraph AsyncSqliteStore — 长期记忆），全部启用 WAL 模式。

**理由**：分离 Agent 状态和业务数据——checkpoint 读写频率远高于业务库，分离避免锁竞争。WAL 模式允许读写并发。checkpointer 和 store 均为进程级单例。

**备选方案**：单数据库（锁竞争风险）、MySQL（运维成本不匹配种子期规模）。

### D12: 文本去重算法

**选择**：SSE 适配器维护四个状态：上次工具输出文本、LLM 新回复前缀累积、去重决策锁、工具完整性标记。当 LLM 流式文本与上次工具输出重叠 > 70% 时跳过。辅导工具返回 guidance/step 键自动标记完整。

**理由**：LLM 有时逐字复述工具输出，直接推给前端造成重复渲染。30号 §13.2 提供的算法已在学生端得到验证。

### D13: SSE 背压保护

**选择**：SSE 适配器增加背压检测——当 `asyncio.Queue` 中待发送事件超过 100 条时，跳过非关键事件（text 事件的中间 token），只保留 tool_call/tool_result/error/done 等结构事件。text 事件合并为单条"内容已截断，请查看完整回复"提示。

**理由**：SSE 是单向推送——前端 tab 切到后台时 `requestAnimationFrame` 暂停，事件在前端队列堆积。41号 §7.1 只定义了正常帧同步，未定义队列溢出策略。后端适配器层面的背压保护确保：即使前端消费停滞，后端不会无限堆积内存。丢弃 text token 中间帧不影响最终结果——最后一个 text 事件包含完整累积文本。

**备选方案**：不做保护（内存无限堆积，极端情况 OOM）、前端背压通过 HTTP/2 flow control 反推（实现复杂，且中间代理可能破坏）。

## Risks / Trade-offs

- **[R1] Planner 每次调用增加延迟**：每条消息多 1 次 LLM 调用。缓解：单步任务走 fallback（非 LLM），只有复杂消息触发 LLM 拆解；Planner 独立超时 5s，超时走 fallback。P50 额外延迟约 1-1.5s。

- **[R2] 30 个工具全量注册可能超出 LLM 上下文**：Persona 过滤将暴露量降为 2-8 个，但 tool description 需控制长度。缓解：每个工具 docstring ≤ 200 字，强调"何时用/何时不用"。

- **[R3] Gateway 瘦身后没有意图分类兜底**：已确认接纳——ReAct system prompt 吸收意图分类。如果准确率低于预期，可后续加回 LLM 分类。

- **[R4] 上下文 LLM 摘要质量不确定**：200 字压缩可能丢失化学术语精度。缓解：缓存摘要，用户可随时重置对话；摘要失败时静默丢弃不阻塞主流程。

- **[R5] 学生/家长端点迁移为 BREAKING**：旧 `/parent/agent/chat` 和旧学生 SSE 端点被废弃。缓解：两个前端页面同时在改，部署时需要前后端同步上线。无外部 API 消费者。

- **[R6] checkpoint.db 写入失败导致对话丢失**：SQLite WAL 模式下单文件故障罕见。缓解：checkpointer 配置为进程级单例，服务启动时自动创建/迁移。

- **[R7] Provider 故障拖慢全局**：无熔断器时故障 Provider 每次请求都被重试。缓解：熔断器 OPEN 后 30s 内直接跳过故障 Provider，避免无效等待累积。

- **[R8] SSE 事件堆积导致内存溢出**：前端消费停滞时后端持续生产事件。缓解：适配器内队列上限 100 条，超限后丢弃 text token 中间帧，保留结构和最终事件。

## Migration Plan

1. **Phase 6 开发期间**：旧学生/家长端点保持运行，新 `/api/v1/chat/` 端点并行部署
2. **前后端同步上线**：`pages/m/index.html` 和 `pages/m/parent.html` 同时切换到新 URL
3. **旧端点废弃**：`/api/v1/parent/agent/*` 和相关学生端点标记 deprecated（保留 1 个 Phase 后删除）
4. **回滚策略**：前端保留旧 URL 的注释代码（1 行切换），后端旧端点保留但停用——恢复只需取消注释
5. **数据库迁移**：checkpoint.db 和 memory.db 为全新数据库，无需迁移现有数据

## Open Questions

1. **MCP Server 时机**：30号 §12 设计了 16 个 MCP 工具。当前决定延后到 Phase 6 完成后独立提案——MCP 工具与 Agent 工具使用不同的调用路径，不阻塞核心引擎。
2. **WebSocket 传输层**：41号 §2.2 预留了传输层可替换架构。当前只实现 SSE——WebSocket 适配器在有具体场景（如实时协作）时再做。
3. **性能基准**：Agent 引擎的性能指标（首 Token 延迟 P95 < 3s、对话成功率 > 95%）需要在实际 LLM 调用环境中测量，而非 mock。

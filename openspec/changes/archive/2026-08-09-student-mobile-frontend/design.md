## Context

现有学生端 `frontend/pages/m/` 下 6 个 HTML 页面中，practice/wrong/review 已通过 `student-practice-frontend` 变更完成 API 接入。剩余 login / index(AI 助教) / report 三个页面 UI 结构完整但缺少 JS 逻辑。共有模块 `frontend/js/auth.js` (JWT 管理) 和 `api-client.js` (fetch 封装 + KaTeX) 已就绪。

后端 Agent 引擎 (`agent/tools/`、`app/agent/`) 拥有 30 个注册工具、4 套 Persona YAML 配置、Guard 护栏层、SSE 适配器，但 Agent SSE 流式端点未注册到 `app/api/v1/` router。

项目前端采用 MPA 架构（多 HTML 页、零打包工具、CDN 引入 KaTeX），共享 JS 模块通过 `<script src="...">` 加载。

## Goals / Non-Goals

**Goals:**
- login.html 接入真实 JWT 认证流程
- index.html 接入完整 SSE Agent 对话（11 种事件、7 个 Student 工具）
- report.html 接入 stats/plan/diagnosis 数据 API
- 新增后端 SSE 聊天端点并注册到 v1 router
- 所有 6 页共享 TabBar 导航壳 + 认证守卫

**Non-Goals:**
- 不做 WebSocket 替代 SSE（SSE 已是产品设计决策，30号 §1.2）
- 不新增外部 npm 依赖（保持现有 CDN + Vanilla JS 模式）
- 不改变 Student Persona 的工具集（现有 7 工具 + periodic_law_tutor 已满足需求）
- 不上线家长端页面（parent.html 保持不变）
- 不做离线缓存/PWA（非本次范围）

## Decisions

### D1: SSE 端点位置与路由

**决议**: 新建 `app/api/v1/chat.py`，注册到 v1_router，路径前缀 `/api/v1/chat`。

**理由**: 
- 现有 15 个 v1 路由模块均按领域拆分（practice.py、review.py、stats.py 等），单独 chat.py 保持一致性
- Agent SSE 对话是独立领域，不应塞入 teaching.py（教学流程管理）或 agent/（引擎内部）
- `app/agent/` 目录只放引擎内部模块（context、store、tools），API 层放 `app/api/v1/`

**替代方案**: 
- 放 teaching.py：语义不匹配，teaching.py 管理考试/答题卡/导出
- 直接注册到 main.py：打破按领域分文件的约定

### D2: SSE 传输层 — fetch + ReadableStream vs EventSource

**决议**: 使用 `fetch()` + `ReadableStream` 读取 SSE 流，不用 `EventSource`。

**理由**:
- EventSource 只支持 GET，而 Agent 对话需要 POST（携带 message、thread_id、context）
- 已有 `api-client.js` 的 fetch 封装可复用 Bearer token 注入和 401 处理
- ReadableStream 提供 AbortController 取消能力（页面切换时中断流）

### D3: 前端模块拆分

**决议**: 新建两个共享 JS 模块，各页面通过 `<script>` 标签引入：

| 模块 | 路径 | 职责 |
|------|------|------|
| `ChemSSE` | `frontend/js/sse-client.js` | SSE 流解析、事件分发、连接生命周期管理 |
| `ChemAgentRender` | `frontend/js/agent-renderer.js` | 工具卡片 HTML 生成（题目卡、诊断图、学习计划等） |

**理由**:
- 分离"协议解析"和"UI 渲染"关注点，各自可独立测试
- Teacher 端未来也可复用相同的 SSE 客户端模块
- 保持 MPA 惯例：每个模块暴露一个全局命名空间对象

### D4: 工具结果渲染策略

**决议**: 采用"结构化 HTML 优先，纯文本兜底"策略。

每个工具在 `agent-renderer.js` 中注册一个渲染函数（函数名 = 工具名），`tool_result` 事件到达时按工具名查找渲染器。未注册的工具降级为 `<pre>` 文本块。

当前需要渲染的 Student 工具：
- `chemistry_tutor` → 文本气泡（含 LaTeX）
- `ionic_equation_tutor` → 四步卡片（判断可拆→写离子→删不变→查守恒）
- `stoichiometry_tutor` → 计算步骤卡片
- `redox_tutor` → 三步卡片（标化合价→找升降→电子守恒配平）
- `equilibrium_tutor` → 三段式表格卡片
- `periodic_law_tutor` → 位置→结构→性质推断卡片
- `simulate_experiment` → 实验报告卡片（目的/仪器/步骤/现象/方程式）

**替代方案**:
- 所有工具输出纯文本：丢失结构化视觉，苏格拉底式辅导的步骤感无法体现
- 每个工具一个独立 HTML 模板文件：MPA 下文件过多，维护负担重

### D5: 对话历史存储策略

**决议**: 双写策略 — 服务端 Checkpointer (SQLite) 为 Source of Truth，客户端 localStorage 做热缓存。

**流程**:
1. 打开抽屉 → GET `/api/v1/chat/conversations?prefix=s-` 获取服务端列表
2. 与 localStorage 缓存的本地列表合并（服务端优先）
3. 合并结果写回 localStorage
4. 切换对话 → GET `/api/v1/chat/history/{thread_id}` 从服务端加载完整消息
5. 消息渲染完毕后缓存到 localStorage

**理由**:
- 服务端 Checkpointer 保证跨设备/清缓存后对话不丢失
- 客户端缓存使冷启动（无网络时首次渲染）可显示上次对话摘要
- `prefix=s-` 过滤只返回学生对话，不混入教师/家长对话

### D6: KaTeX 渲染时机

**决议**: 延迟渲染 — 在 `text` 事件流完成后（`done` 事件前），对 AI 气泡全文执行一次 `ChemAPI.renderLatex()`。

**理由**:
- 流式文本到达时公式可能不完整（`$H_2SO` 截断为 `$H_2S`），逐 chunk 渲染会产生 KaTeX 报错
- 文本去重（spec §SSE connection lifecycle）在前端处理，去重完成后公式完整
- 单次批量渲染性能优于逐 chunk 触发 KaTeX 解析

### D7: 学生上下文注入

**决议**: 前端发送消息时携带 `context: {student_id, student_name, class_name}`，后端在 Agent 工厂函数中查询完整 Student Profile 并注入 System Message。

**理由**:
- 30号设计文档 §9.2 定义了消息组装顺序：System Message(学生档案) → System Message(情景记忆) → 历史对话 → 当前输入
- `app/agent/context.py` 已实现 `build_student_context()` 函数（查询班级名 + 指数衰减准确率）
- 前端只传轻量标识（避免每次查询全量 profile），后端按需查询 DB

## Risks / Trade-offs

- **[R1] SSE 连接中断无自动恢复** → SSE 协议本身不支持断线重连。策略：在 sse-client.js 的 `onerror` 回调中显示"重新发送"按钮，由用户手动触发重发。MVP 不实现自动重连。
- **[R2] 30 个工具中 Student 只用 7 个** → Persona 过滤机制（YAML 白名单 ∩ TOOL_META 注册表）已保证工具隔离，LLM 不会看到无权限工具。
- **[R3] 移动端弱网下 SSE 流可能卡顿** → 当前 SSE 适配器按事件粒度推送，非逐 token。`text` 事件本身是 chunked，首 Token 延迟 P95 < 3s 目标不变。弱网卡顿先记录不优化。
- **[R4] Tool call 限次耗尽后 Agent 可能卡死** → Guard 层 limit_exceeded 错误返回后，LLM 收到结构化错误并可选择其他工具或给文本回复。不会导致流中断。
- **[R5] 3 个页面共享 TabBar 但 HTML 是独立的** → TabBar 的 HTML + CSS 在每个页面中重复。修改 TabBar 时需同步 6 个文件（含已完工的 3 页）。接受此重复，不做模板抽取——MPA 的 trade-off。

## Open Questions

- 无。所有架构决策已在探索阶段与 21/22/30/40 号设计文档对齐确认。

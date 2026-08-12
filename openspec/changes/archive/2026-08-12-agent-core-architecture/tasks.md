# Agent 核心架构 — 实现任务

## 1. Persona YAML 配置

- [x] 1.1 创建 Teacher persona YAML：name/description/system_prompt/available_skills（8 工具白名单），`agent/prompts/teacher.yaml`
- [x] 1.2 创建 Student persona YAML：补齐 8 个 tutoring 工具 + memory_student_get + web_search，更新 `agent/prompts/student.yaml`
- [x] 1.3 创建 Tutor persona YAML：6 工具（chemistry_tutor + search_exam_bank + web_search + show_exam_workbench + simulate_experiment + balance_equation），`agent/prompts/tutor.yaml`
- [x] 1.4 创建 Parent persona YAML：2 工具（weekly_report + diagnose_barrier）+ data_access 权限定义，`agent/prompts/parent.yaml`
- [x] 1.5 实现 Persona YAML loader：读取 YAML → 验证 required fields → 返回 PersonaConfig 对象
- [x] 1.6 测试：YAML 加载成功、缺失字段报错、available_skills 非空

## 2. TOOL_META 注册 + 工具实现

- [x] 2.1 扩展 `@register_tool` 装饰器：新增 requires_approval、prerequisites 字段，更新 `agent/tools/tool_meta.py`
- [x] 2.2 实现编译时完整性验证：启动时检查 TOOL_META 中每个 func 存在、每条已注册工具有元数据
- [x] 2.3 实现出题工具（7 个）：search_exam_bank（三级搜索）、web_search（联网+摘要）、show_exam_workbench（面板触发）、save_to_bank（题库写入）、generate_questions（LLM出题+审核）、list_banks、delete_bank——调用已有 Service 层
- [x] 2.4 实现诊断工具（7 个）：diagnose_barrier、show_diagnosis、show_students、weekly_report、assign_adaptive_practice、generate_learning_plan、send_learning_plan——调用已有 Service 层
- [x] 2.5 实现辅导工具（2 个）：chemistry_tutor（教师800字/学生500字模式切换）、simulate_experiment（LLM生成实验报告）+ balance_equation（调用 parser engine）
- [x] 2.6 实现 6 个 Socratic 辅导工具：通过 tutoring_factory 生成 ionic_equation_tutor、stoichiometry_tutor、redox_tutor、equilibrium_tutor、periodic_law_tutor、organic_tutor
- [x] 2.7 实现 OCR/批改工具（3 个）：query_ocr_progress、grade_answer_sheets、save_grading_results
- [x] 2.8 实现记忆工具（2 个）：memory_student_get（读 Store）、memory_teacher_get（读教师偏好）
- [x] 2.9 实现家长报告工具（2 个）：generate_parent_report、send_report_to_parent
- [x] 2.10 注册 5 个浏览器工具：browse_navigate、browse_read、browse_click、browse_input、browse_screenshot（Playwright 封装，单实例+60s 空闲回收）
- [x] 2.11 测试：每个工具注册后有正确 metadata、Persona 过滤交集体现在最终工具集

## 3. chem_skills 辅导引擎（4 个新引擎）

- [x] 3.1 创建 `chem_skills/chemistry_equilibrium/engine/`：导出均衡态辅导函数 + 三段式表格数据模型
- [x] 3.2 创建 `chem_skills/chemistry_ionic/engine/`：导出离子反应辅导函数（四步法）
- [x] 3.3 创建 `chem_skills/chemistry_redox/engine/`：导出氧化还原辅导函数（三步法）
- [x] 3.4 创建 `chem_skills/chemistry_stoichiometry/engine/`：导出化学计量辅导函数（四步法）
- [x] 3.5 修复 `chem_skills/chemistry_memory/__init__.py`：导出 zpd_engine、spaced_repetition、variant_generator、strategy_matrix 的 7 个函数
- [x] 3.6 测试：每个引擎 __init__.py 有正确导出、引擎函数可独立调用

## 4. 模型工厂 + Provider 回退

- [x] 4.1 创建 `app/llm/model_factory.py`：get_model(provider, tools?) → ChatOpenAI 兼容实例，temperature=0.3, max_tokens=4096
- [x] 4.2 实现 Agent 推理模型工厂：get_agent_model(provider) — 带工具绑定
- [x] 4.3 实现工具系统模型工厂：get_tool_model(provider) — 不带工具绑定（用于 Planner、摘要等）
- [x] 4.4 实现三级回退 + 指数退避重试：3 次尝试 per provider，间隔 1s→2s→4s，MiMo→Qwen→DeepSeek
- [x] 4.5 实现熔断器（CircuitBreaker）：CLOSED→OPEN（连续失败3次）→HALF_OPEN（30s后放行1次）状态机，每 Provider 独立实例，进程内存维护
- [x] 4.6 测试：正常返回、Provider 不可用触发 fallback、重试耗尽抛出异常、熔断器 OPEN 后直接跳过、HALF_OPEN 成功恢复

## 5. Gateway（Provider 选择器）

- [x] 5.1 创建 `app/agent/gateway.py`：classify_provider(message) → "vision" | "default"
- [x] 5.2 实现视觉关键词匹配：消息含 图片/照片/图像/识别/OCR/上传 → MoMi
- [x] 5.3 集成到 Agent 对话流端点：消息进入时先过 Gateway 选 Provider，再创建 Agent
- [x] 5.4 测试：图片消息→vision、文本消息→default

## 6. Planner（目标拆解器）

- [x] 6.1 创建 `app/agent/planner.py`：PlanStep + Plan 数据类，generate() / validate() / single_step_fallback() / inject_dependencies()
- [x] 6.2 实现 PLAN_PROMPT 模板：含 {skills} 占位符，规则：最多 6 步、depends_on 引用前序、${step_N.field} 变量引用
- [x] 6.3 实现 validate()：检查 skill 名存在、无重复 step 编号、无自引用、≤6 步
- [x] 6.4 实现 inject_dependencies()：正则匹配 `${step_N.field}` → 从前序步骤结果取值替换
- [x] 6.5 集成到 Agent 对话流：每条消息先 Planner.generate() → steps 逐个送入 ReAct
- [x] 6.6 实现 Planner 独立超时：LLM 调用设 5s 超时（asyncio.wait_for），超时走 single_step_fallback，不阻塞主流程
- [x] 6.7 测试：复杂目标拆解、单意图 fallback、LLM 失败 fallback、超时 fallback、依赖注入替换正确

## 7. ReAct Agent 引擎

- [x] 7.1 创建 `app/agent/engine/`：agent_factory(persona, provider) → LangGraph create_react_agent
- [x] 7.2 实现 Persona 工具过滤：YAML available_skills ∩ TOOL_META[persona] → domain_tools，+5 浏览器工具
- [x] 7.3 实现 checkpointer 集成：AsyncSqliteSaver(checkpoint.db)，进程级单例
- [x] 7.4 实现 recursion_limit=12 + 耗尽时 SSE error 事件
- [x] 7.5 测试：Agent 创建、Persona 过滤正确、checkpoint 持久化/恢复

## 8. Guard 四层护栏

- [x] 8.1 创建 `app/agent/guard.py`：GuardState（请求级实例）+ check(tool_name, args) → GuardResult
- [x] 8.2 实现 L1 前置条件检查：从 TOOL_META.prerequisites 读取必填参数，校验非空/长度
- [x] 8.3 实现 L2 调用次数限制：从 TOOL_META.call_limit 读取，跟踪本轮各工具调用次数
- [x] 8.4 实现 L3 去重检查：工具名 + sorted(json.dumps(args)) 为 key，已执行则跳过
- [x] 8.5 实现 L4 审批门控：TOOL_META.requires_approval=True → 检查审批状态，未审批则中断等待
- [x] 8.6 实现 _component/_route 剥离：Guard 执行后从返回值提取到 GuardState，纯净结果返回 LLM
- [x] 8.7 测试：每层独立测试（前置失败、超限、重复、未审批）、审批通过后恢复

## 9. 上下文管理

- [x] 9.1 创建 `app/agent/context_trimmer.py`：trim(messages, max_messages=30, keep_recent=6) → trimmed list
- [x] 9.2 实现 Layer 1（保留最近 6 条）+ Layer 2（15 个关键词过滤："学生""诊断""障碍""考试""题目""知识点""分数""薄弱""学习计划""错题""成绩""练习""班级""教师""实验"）
- [x] 9.3 实现 Layer 3（丢弃 ≥ 10 条时 LLM 摘要 ≤ 200 字）+ 摘要缓存 per checkpoint
- [x] 9.4 集成到 Agent 调用前：每次 Agent.invoke() 前检查消息数 → 超阈值则裁剪
- [x] 9.5 增强 `app/agent/context.py`：支持 non-student persona 跳过注入、支持 parent persona 注入 {student_context}
- [x] 9.6 测试：未超阈值不裁剪、关键词消息保留、摘要生成与缓存、摘要失败不阻塞

## 10. SSE 适配器 v2

- [x] 10.1 创建 `app/agent/sse/adapter_v2.py`：langgraph_sse_v2 异步生成器，逐个事件 yield
- [x] 10.2 实现 10 种事件类型转换：phase → SSEPhaseEvent, tool_call → SSEToolCallEvent, tool_result → SSEToolResultEvent, text → SSETextEvent, component → SSEComponentEvent, navigate → SSEDoneEvent 等
- [x] 10.3 实现文本去重算法：上次工具输出 vs 当前 LLM 文本，重叠 > 70% 跳过，tutoring 工具 guidance/step 键自动标记完整
- [x] 10.4 实现特殊字段事件化：Guard 剥离的 _component → component 事件，_route → navigate 事件
- [x] 10.5 实现 SSE 背压保护：asyncio.Queue 上限 100 条，超限丢弃 text token 中间帧，保留 tool_call/tool_result/error/done 结构事件
- [x] 10.6 测试：SSE 事件序列正确、去重生效、component/navigate 正确发射、背压触发后结构事件不丢失

## 11. 审计日志

- [x] 11.1 创建 `app/agent/audit.py`：AuditLogger 单例，deque(maxlen=100) + JSONL 文件追加
- [x] 11.2 实现 audit_log()：timestamp/persona/skill_name/args(脱敏)/result_summary(200字截断)/duration_ms/error
- [x] 11.3 实现脱敏：password/phone/parent_phone/token/api_key/secret → "***"
- [x] 11.4 集成到 Guard 层：每个工具执行后自动记录
- [x] 11.5 测试：正常记录、脱敏生效、磁盘满不阻塞、缓冲区滚动

## 12. 依赖注入容器

- [x] 12.1 创建 `app/agent/dependency.py`：AgentContext(stuent_id, student_profile, persona, episodic, provider_name) 数据类
- [x] 12.2 集成到 agent_factory：创建 Agent 时注入 AgentContext 到工具函数
- [x] 12.3 测试：工具函数可通过上下文访问 student_id/persona/provider

## 13. Chat API 端点

- [x] 13.1 创建 `app/api/v1/chat.py`：chat_router，前缀 `/api/v1`
- [x] 13.2 实现 POST /chat/stream：接收 AgentChatRequest → Gateway 选 Provider → 组装 Persona → Planner → ReAct+Guard → SSE stream
- [x] 13.3 实现 GET /chat/conversations：prefix 过滤 → 从 checkpoint.db 查询 → 返回对话列表
- [x] 13.4 实现 GET /chat/history/{thread_id}：从 checkpoint 取消息 → 按 role 分类 → 返回
- [x] 13.5 实现 POST /chat/new：生成 `{prefix}-{Unix毫秒}` thread_id → 返回
- [x] 13.6 实现 DELETE /chat/conversations/{thread_id}：删除 checkpoint.db 中 writes + checkpoints
- [x] 13.7 实现 POST /chat/resume：读 checkpoint → 注入审批结果 → Agent 恢复执行 → 继续 SSE stream
- [x] 13.8 实现 POST /chat/reset：清空 thread_id 的 messages
- [x] 13.9 在 `app/main.py` 注册 chat_router
- [x] 13.10 测试：SSE stream 集成测试、CRUD 端点测试、审批 resume 流程

## 14. 教师端聊天前端

- [x] 14.1 在 `pages/index.html` 中加载 `sse-client.js` + `agent-renderer.js` + `auth.js` + `api-client.js`
- [x] 14.2 实现消息发送/接收循环：参考 `pages/m/index.html` 的消息管理逻辑
- [x] 14.3 实现教师工具渲染器：题目卡片（renderQuestionCards — 审核徽章+RAG来源+答案折叠）、诊断总览（renderBarrierOverview — CSS柱状图+Top5学生）、学生列表（renderStudentList）
- [x] 14.4 实现内联面板渲染：exam-workbench（4 Tab 出题工作台）、diagnosis（诊断图表面板）、student-list（班级学生列表）
- [x] 14.5 实现教师对话侧边栏：班级选择器、学生搜索、对话历史列表
- [x] 14.6 实现页面桥接：navigate→page store、populate→component target、action→动作执行
- [ ] 14.7 测试：发送消息→收到 SSE 事件→渲染卡片→内联面板可交互（需手动 QA）

## 15. 学生端/家长端迁移

- [x] 15.1 修改 `pages/m/index.html`：POST URL 切换到 `/api/v1/chat/stream`，body 加 `context: {role: "student", ...}`
- [x] 15.2 修改 `pages/m/parent.html`：所有 `/parent/agent/*` URL 切换到 `/api/v1/chat/*`，body 加 `context: {role: "parent", student_id: ...}`
- [ ] 15.3 验证：学生端对话流程（发送→SSE→渲染工具卡片→对话历史）完整可用（需手动 QA）
- [ ] 15.4 验证：家长端对话流程（发送→ReAct→SSE→家长语言→对话管理）完整可用（需手动 QA）

## 16. 集成测试与端到端验证

- [x] 16.1 Agent 工具注册完整性测试：get_all_tools() 返回 35 个（30 domain + 5 browser）
- [x] 16.2 Persona 过滤测试：各角色工具集与 30号定义一致
- [x] 16.3 Guard 四层集成测试：模拟 ReAct 循环中触发每层检查
- [x] 16.4 Planner → ReAct 串联测试：mock LLM 验证步骤按 plan 顺序执行
- [x] 16.5 SSE 事件流端到端测试：发送消息 → 验证事件序列 phase→tool_call→tool_result→text→done
- [x] 16.6 审批流程端到端测试：触发审批 → 前端确认 → resume → 工具继续执行
- [x] 16.7 上下文裁剪集成测试：构造 35 条消息 → 验证裁剪后格式
- [x] 16.8 Provider 回退集成测试：主 Provider 不可用 → 自动 fallback
- [ ] 16.9 evals Golden 回归测试：现有 100 条 golden 样本通过率不劣化 > 5%
- [ ] 16.10 运行全量测试套件（1399+ 新增测试）→ 100% 通过

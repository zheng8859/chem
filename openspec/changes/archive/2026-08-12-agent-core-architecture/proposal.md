# Agent 核心架构 — Phase 6

## Why

项目当前有 143 个 REST 端点覆盖全部业务能力（出题、诊断、题库、OCR、预警），但教师必须通过点按式 UI 操作，无法用自然语言驱动。设计文档（30号 + 41号 + 38号）定义了完整的 Agent 架构——单 ReAct 智能体 + 30 工具 + 4 Persona + Gateway + Guard + SSE——但引擎层代码为零。学生端和家长端虽然已有聊天 UI，但后端绕过 LangGraph 直接裸调 LLM，没有 ReAct、护栏、上下文管理。

Phase 6 的目标：把设计文档中的 Agent 引擎完整落地，让教师能用自然语言驱动所有业务能力。

## What Changes

- **新建 Agent 引擎核心**：Gateway（Provider 选择）→ Planner（目标拆解）→ ReAct Agent（LangGraph v2）→ Guard（四层护栏）→ SSE 适配器（10 种事件类型）
- **新建 30 个 Agent 工具**：基于已有 Service 层 + chem_skills 引擎注册，通过 `@register_tool` 声明元数据和护栏参数
- **新建 4 套 Persona 配置**：Teacher/Student/Tutor/Parent YAML，定义 system prompt + 工具白名单 + 数据权限
- **新建统一聊天 API**：`/api/v1/chat/stream`（SSE 对话流）+ `/api/v1/chat/conversations`（对话 CRUD），替代当前分散的家长裸 LLM 端点和学生端点
- **新建教师端聊天 UI**：基于现有 `pages/index.html` 骨架，接入 SSE 客户端 + 工具渲染器 + 内联可交互面板
- **新增 4 个辅导引擎**：化学平衡/离子反应/氧化还原/化学计量（现有 parser + diagnosis 引擎不变）
- **新增上下文管理**：三层裁剪策略（最近6条+关键词过滤+LLM摘要）+ 学生上下文注入
- **新增审计日志**：JSONL 格式，环形缓冲区 + 磁盘追加，记录所有工具执行
- **新增 LLM Provider 回退**：MiMo → 通义千问 → DeepSeek 三级 Fallback，指数退避重试
- **迁移**：学生端/家长端聊天从各自的裸端点迁移到统一 `/chat/` API（**BREAKING**：废弃 `/api/v1/parent/agent/chat` 和现有学生 SSE 端点）

## Capabilities

### New Capabilities

- `agent-engine-core`: ReAct 推理引擎（LangGraph create_react_agent v2）、Gateway Provider 选择器、Planner 目标拆解器、Guard 四层护栏、SSE 事件适配器
- `agent-tools`: 30 个工具的统一注册体系（@register_tool 装饰器 + TOOL_META 注册表），4 套 Persona YAML 配置与工具过滤机制
- `agent-chat-api`: 统一的 Agent 对话 REST 端点（SSE 流式对话、对话列表/历史/新建/删除/重置）和审批恢复端点
- `agent-context-management`: 三层对话上下文裁剪（最近6条+关键词过滤+LLM摘要），学生上下文 System Message 注入
- `agent-audit-log`: 环形缓冲区 + JSONL 文件审计日志，记录工具名/参数/耗时/结果/错误

### Modified Capabilities

- `student-agent-chat`: 从现有独立 SSE 端点迁移到统一 `/api/v1/chat/stream`（通过 `context.role="student"` 区分 Persona），**BREAKING** 废弃旧端点
- `parent-agent-chat`: 从现有裸 LLM 调用（`llm_chat_with_tools`）迁移到完整 ReAct Agent 引擎，**BREAKING** 废弃 `/api/v1/parent/agent/chat`
- `agent-chem-tutors`: 新增 4 个辅导工具（equilibrium_tutor / ionic_equation_tutor / redox_tutor / stoichiometry_tutor）及其对应的 chem_skills 引擎
- `agent-student-memory`: 集成上下文裁剪中的 LLM 摘要能力，长期记忆 Store 接入工具链

## Impact

- **新增文件**：`app/agent/engine/`（ReAct）、`app/agent/gateway.py`、`app/agent/guard.py`、`app/agent/planner.py`、`app/agent/sse/`（SSE 适配器）、`app/agent/audit.py`、`app/agent/context_trimmer.py`、`app/agent/dependency.py`（DI 容器）、`app/llm/model_factory.py`（Provider 工厂）
- **新增路由**：`app/api/v1/chat.py`（统一聊天端点 + 对话 CRUD）
- **新增工具**：`agent/tools/` 下 ~24 个工具文件，`agent/prompts/` 下 3 个 Persona YAML
- **新增引擎**：`chem_skills/chemistry_equilibrium/`、`chemistry_ionic/`、`chemistry_redox/`、`chemistry_stoichiometry/`
- **修改文件**：`app/main.py`（注册 chat router）、`app/api/v1/parent.py`（废弃 parent/agent/* 端点）、学生/家长前端页面（URL 迁移）
- **新增前端**：`pages/index.html` JavaScript 逻辑（SSE 客户端 + 渲染器集成）、4 个教师工具渲染器
- **测试**：每层独立测试（Guard 四层、Gateway 分类、Planner 拆解、SSE 事件序列化、工具注册完整性、上下文裁剪），Agent 集成测试（mock LLM 的 ReAct 循环）
- **依赖**：LangGraph ≥0.2（已有）、Playwright ≥1.40（已有）

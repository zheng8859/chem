## Why

学生端 6 个移动 Web 页面中，3 个（练习/错题/复习）已通过 `student-practice-frontend` 变更完成 API 接入，但剩下的 3 个核心页面——AI 助教对话（首页）、登录和个人中心——仍是静态 UI 原型，缺少前端 JS 逻辑。同时，已完工的 3 页 TabBar 中存在链接错误（指向 `profile.html` 而非 `report.html`）。

## What Changes

- **登录页接入真实认证**：表单提交 → `POST /api/v1/auth/login` → JWT 存储 → 学生端首页跳转
- **AI 助教聊天页接入 SSE 对话**：流式消息、7 种辅导工具卡片渲染、对话历史管理、快捷提问
- **个人中心页接入数据 API**：stats/learning-plan/diagnosis 实时数据，学习周报模态框，菜单入口导航
- **共享 JS 模块**：新建 `sse-client.js`（SSE 事件解析引擎）+ `agent-renderer.js`（工具结果富渲染）
- **TabBar 导航修复**：3 个已完工页面的 `profile.html` 链接修正为 `report.html`，确保 6 页导航一致性

## Scope

**本次范围为纯前端（UI）变更。** 后端 Agent SSE 聊天端点（`app/api/v1/chat.py`）为外部依赖，不在本变更范围内。前端 SSE 客户端模块可通过对 mock SSE 数据进行开发与单元验证。

## Capabilities

### New Capabilities

- `student-agent-chat`: 学生端 AI 辅导 SSE 聊天——前端 SSE 客户端（11 种事件解析、连接生命周期、工具卡片渲染、对话 CRUD、快捷提问、审批卡片）
- `student-mobile-entry`: 学生移动端入口页面——登录表单提交与 JWT 握手，个人中心（stats/plan/诊断数据展示 + 学习周报模态框），共享 TabBar 导航壳与认证守卫

### Modified Capabilities

（无——登录和 stats/plan 接口已存在于 `auth-system` 和 `student-stats-api`，变更仅消费现有 API）

## Impact

- **新建文件**: `frontend/js/sse-client.js`、`frontend/js/agent-renderer.js`
- **改造文件**: `frontend/pages/m/login.html`、`index.html`、`report.html`（3 个原型 → 功能页）
- **修复文件**: `frontend/pages/m/practice.html`、`wrong.html`、`review.html`（TabBar `profile.html` → `report.html`）
- **外部依赖**: 后端 `POST /api/v1/chat/stream` SSE 端点 + 对话 CRUD 端点（需另行实现）
- **零新增外部依赖**: 复用现有 `auth.js`、`api-client.js`、KaTeX CDN

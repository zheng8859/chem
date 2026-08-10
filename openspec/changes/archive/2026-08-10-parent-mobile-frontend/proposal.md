## Why

家长端后端 API 已全部就绪（绑定码管理、子女查询、周报、通知、Agent SSE 对话），但前端仅有 2 个静态 HTML 原型（`parent-login.html` 和 `parent.html`），没有任何 JS 业务逻辑，无法实际使用。需要在现有原型基础上接入后端 API，使家长能真正登录、绑定子女、查看学习数据、接收通知、使用 AI 助手。

## What Changes

- 将 `parent-login.html` 从静态原型改造为可交互的登录/注册双模式页面，接入 `POST /api/auth/login` 和 `POST /api/auth/register/parent`
- 将 `parent.html` 从硬编码 Demo 数据改造为接入真实 API 的三 Tab 主面板（概览/学习报告/消息）
- 实现子女选择器，从 `GET /api/v1/parent/children` 拉取数据，切换子女时联动刷新所有 Tab
- 实现浮动 AI 助手面板，通过 `ChemSSE` 接入 `POST /api/v1/parent/agent/chat` SSE 流式对话
- 实现绑定新子女的底部 Sheet（调用 `POST /api/v1/parent/bind`）
- 复用现有共享 JS 基础设施（`auth.js`、`api-client.js`、`sse-client.js`），不引入新框架

## Capabilities

### New Capabilities

- `parent-mobile-login`: 家长端登录/注册双模式页面（手机号 + 密码 + 绑定码），含表单验证、API 调用、错误处理、登录后自动跳转
- `parent-mobile-dashboard`: 家长端三 Tab 主面板（概览/学习报告/消息），含子女选择器、数据加载与渲染、加载态/空态/错误态处理、周报缓存与手动生成
- `parent-mobile-agent-chat`: 家长端浮动 AI 助手 SSE 流式对话面板，含快捷问题 chips、消息渲染、KimTeX 渲染、对话历史管理

### Modified Capabilities

<!-- 纯前端变更，不修改现有后端规格 -->

## Impact

- 修改文件：`chemai-backend/frontend/pages/m/parent.html`（静态 → 交互式）
- 修改文件：`chemai-backend/frontend/pages/m/parent-login.html`（静态 → 交互式）
- 依赖现有：`chemai-backend/frontend/js/auth.js`、`api-client.js`、`sse-client.js`（不修改）
- 依赖 API：`POST /api/auth/login`、`POST /api/auth/register/parent`、`GET/POST/DELETE /api/v1/parent/*`、`POST /api/v1/parent/agent/chat`
- 依赖样式：`parent-login.html` 和 `parent.html` 现有的内联 CSS Theme（不修改）

## Why

学生练习和复习是 ChemAI 的核心学生价值——自适应练习引擎、间隔复习、错题本三个后端系统（12个API端点，1178测试通过）已经就绪，但学生端目前只有 7/31 创建的静态原型（practice.html / review.html / wrong.html），不调用任何真实 API、无状态管理、无错误处理。需要用最小改动量对接后端，让这三个核心功能对学生可用。

## What Changes

- **practice.html** — 将静态 mockup 改造为对接到 `GET /api/v1/practice/student/{uid}/tasks` 和 `POST /api/v1/practice/submit` 的真实练习页，包括任务列表（待完成/已完成）、逐题答题、答案持久化、提交判分、结果展示
- **wrong.html** — 对接错题列表 API（分页 + 知识点筛选）、"已掌握"标记、"生成变式题"入口（跳转独立页）
- **variant.html**（新增）— 变式题训练独立页面：生成变式题 → 创建训练会话 → 逐题作答 → 提交 → 正确率 + 分级学习建议
- **review.html** — 对接待复习列表 API 和复习提交 API，展示 Level 0-5 级别标签、答题判定、掌握反馈
- **共享基础设施** — JWT 认证注入、fetch 封装、KaTeX 化学式渲染、加载/空/错误状态处理

## Capabilities

### New Capabilities
- `student-practice-frontend`: 学生练习页（任务列表 + 答题 + 结果）、错题本（列表 + 筛选 + 掌握标记）、变式题训练流程、复习中心（待复习列表 + 答题提交），含共享 API client、auth 注入和 KaTeX 渲染

### Modified Capabilities
<!-- 纯新增前端页面，不修改已有后端 spec -->

## Impact

- **修改文件**: `frontend/pages/m/practice.html`, `frontend/pages/m/wrong.html`, `frontend/pages/m/review.html`
- **新增文件**: `frontend/pages/m/variant.html`, `frontend/js/api-client.js`, `frontend/js/auth.js`
- **后端**: 不变（已有 API 全部就绪）
- **依赖**: KaTeX CDN（`$...$` 化学式渲染）、现有 CSS 设计令牌（内联 style，不改动）

## 1. parent-login.html — 登录/注册双模式页面

- [ ] 1.1 添加鉴权守卫：已登录用户自动跳转 `parent.html`
- [ ] 1.2 实现登录/注册模式切换 Tab（两个按钮，点击切换表单字段和提交按钮文案）
- [ ] 1.3 登录模式：手机号 + 密码 → `ChemAPI.apiPost("/auth/login", {phone, password})` → `ChemAuth.login(token)` 跳转
- [ ] 1.4 注册模式：手机号 + 密码 + 绑定码 → `POST /api/auth/register/parent` → 成功后同 1.3
- [ ] 1.5 表单验证（空字段检查、绑定码 6 位数字格式、密码 ≥6 位）
- [ ] 1.6 错误处理 Toast（绑定码无效、手机号已注册、密码错误、网络错误）
- [ ] 1.7 提交按钮 loading 态（防止重复提交）

## 2. parent.html — 页面 Shell：鉴权、子女选择器、Tab 框架

- [ ] 2.1 鉴权守卫：未登录跳转 `parent-login.html`，非 parent 角色拒绝访问
- [ ] 2.2 顶部退出按钮：`ChemAuth.logout()` 清 token 跳转登录页
- [ ] 2.3 加载子女列表：`GET /api/v1/parent/children` → 填充子女选择器（姓名、班级、学校）
- [ ] 2.4 子女选择器交互：左右箭头切换（单子女隐藏箭头）、选择后触发当前 Tab 数据刷新
- [ ] 2.5 无绑定子女空态："暂无绑定子女" + "绑定子女" CTA 按钮
- [ ] 2.6 Tab 切换框架：三个 Tab 按钮控制 `tab-content` 显示/隐藏，首次切到某 Tab 时触发懒加载

## 3. parent.html — Tab 1：概览

- [ ] 3.1 调用 `GET /api/v1/parent/child/{student_id}/report` 获取概览数据
- [ ] 3.2 渲染 stats-grid 四卡片：本周练习次数、正确率（加权）、薄弱知识点 chips、最近学习时间
- [ ] 3.3 渲染障碍分析条：从 `characteristics` 提取 barrier_type 比例 → 三色障碍条 + 图例
- [ ] 3.4 渲染学习特点描述文本 + 连续学习天数 streak_days
- [ ] 3.5 概览无数据空态（新绑定学生从未练习过）
- [ ] 3.6 加载态骨架屏 + 错误态重试按钮

## 4. parent.html — Tab 2：学习报告

- [ ] 4.1 调用 `GET /api/v1/parent/child/{student_id}/timeline?weeks=12` 获取周列表，填充周选择器
- [ ] 4.2 当周数据：`GET /api/v1/parent/child/{student_id}/weekly` → 渲染 summary/detail/advice
- [ ] 4.3 404 处理：周报未生成时显示"本周周报尚未生成" + "生成周报"按钮
- [ ] 4.4 手动生成周报：`POST .../weekly/generate` + loading 态 → 刷新当周数据
- [ ] 4.5 历史周：从 timeline 数据渲染简化卡片（练习次数、正确率、主题）
- [ ] 4.6 知识点掌握条：从 timeline/overview 数据渲染 kp-item 列表
- [ ] 4.7 周选择器左右箭头交互 + 当前周标识
- [ ] 4.8 加载态、空态、错误态处理

## 5. parent.html — Tab 3：消息

- [ ] 5.1 调用 `GET /api/v1/parent/notifications` 加载通知列表（分页）
- [ ] 5.2 渲染消息卡片：通知类型图标、标题、预览正文、发送时间、未读蓝点
- [ ] 5.3 点击消息：展开完整内容 + `PUT /notifications/{id}/read` 标记已读 + 移除蓝点
- [ ] 5.4 滚动分页：滚动到底部时自动加载下一页
- [ ] 5.5 空态："暂无消息" + 加载态 + 错误态

## 6. parent.html — 浮动 AI 助手面板

- [ ] 6.1 浮动按钮 + 底部 Sheet 打开/关闭动画（overlay + slide-up）
- [ ] 6.2 快捷问题 chips：点击 chip 自动作为消息发送
- [ ] 6.3 输入框 + 发送按钮：输入文字、回车发送、空消息拦截
- [ ] 6.4 `ChemSSE.connect("/api/v1/parent/agent/chat", {message, thread_id, student_id})` 流式对话
- [ ] 6.5 SSE 事件处理：`phase` 显示状态、`text` 逐条追加回复气泡、`tool_call` 显示"正在查询..."、`done` 保存 thread_id、`error` 错误提示
- [ ] 6.6 回复气泡中的 KaTeX 渲染（`ChemAPI.renderLatex`）
- [ ] 6.7 用户消息即时显示 + AI 回复流式追加
- [ ] 6.8 发送中禁用输入框和发送按钮，完成后恢复
- [ ] 6.9 对话历史管理：历史按钮 → 对话列表（`GET /agent/conversations`）、点击切换（`GET /agent/history/{tid}`）、新建（`POST /agent/new`）、删除（`DELETE /agent/conversations/{tid}`）
- [ ] 6.10 AI 面板关闭时重置新消息（下次打开默认新建对话）

## 7. 集成验证

- [ ] 7.1 完整流程回归：注册 → 登录 → 子女列表 → 三个 Tab 数据加载 → AI 对话 → 通知已读 → 解绑
- [ ] 7.2 边界场景：token 过期 401 自动跳转登录、网络断开、后端 500
- [ ] 7.3 在 390px 移动端视口下手动验证所有交互和样式

## 阶段 1：共享模块 + 登录页 + AI 对话页

### 1.1 SSE 客户端模块（`frontend/js/sse-client.js`）

- [x] 1.1.1 实现 `ChemSSE.connect(url, body, handlers)` — fetch + ReadableStream + AbortController，自动注入 Bearer token
- [x] 1.1.2 实现 SSE 帧解析器：按 `\n\n` 分割，提取 `event:` / `data:` 字段，分派到 `handlers[eventType]`
- [x] 1.1.3 实现发送锁（`_sending` flag）和连接状态机（idle → connecting → streaming → done/error）
- [x] 1.1.4 实现 `error` 事件通用处理：显示"连接失败，请重试"消息气泡 + 重试按钮（重新 `connect` 携带相同 body）
- [x] 1.1.5 实现 `navigate` 事件通用处理：`location.href` 跳转到目标页面
- [x] 1.1.6 实现 `done` 事件通用处理：关闭流、释放 AbortController、触发 `onDone` 回调

### 1.2 Agent 工具渲染模块（`frontend/js/agent-renderer.js`）

- [x] 1.2.1 实现 `ChemAgentRender` 命名空间，暴露 `render(toolName, result) → HTML string` 统一入口
- [x] 1.2.2 实现 `chemistry_tutor` 渲染器：通用辅导文本气泡（含 LaTeX 公式支持）
- [x] 1.2.3 实现 `ionic_equation_tutor` 渲染器：苏格拉底四步卡片（判断可拆物质 → 写成离子 → 删不变离子 → 检查守恒）
- [x] 1.2.4 实现 `stoichiometry_tutor` 渲染器：计算步骤卡片（提取已知量 → 选公式 → 列关系式 → 分步计算）
- [x] 1.2.5 实现 `redox_tutor` 渲染器：三步卡片（标化合价 → 找升降 → 电子守恒配平）
- [x] 1.2.6 实现 `equilibrium_tutor` 渲染器：三段式表格卡片（初始/变化/平衡浓度）
- [x] 1.2.7 实现 `periodic_law_tutor` 渲染器：位置→结构→性质推断卡片
- [x] 1.2.8 实现 `simulate_experiment` 渲染器：实验报告卡片（目的/仪器/步骤/现象/方程式/考点）
- [x] 1.2.9 实现通用兜底渲染器（未注册工具降级为 `<pre>` 文本块 + 工具名标题）

### 1.3 登录页改造（`login.html`）

- [x] 1.3.1 引入 `<script src="../../js/auth.js">` 和 `<script src="../../js/api-client.js">`
- [x] 1.3.2 登录按钮绑定 click 事件：收集 `school_id`/`phone` + `password` → `POST /api/v1/auth/login` → 成功后 `ChemAuth.login(token)` → `location.href = "index.html"`
- [x] 1.3.3 错误处理：401 → 按钮下方显示 "学号或密码错误"；网络错误 → "网络连接失败，请重试"
- [x] 1.3.4 提交中状态：按钮 disabled + 文字变为 "登录中..."；完成后恢复

### 1.4 AI 助教聊天页改造（`index.html`）

- [x] 1.4.1 引入 `auth.js`、`api-client.js`、`sse-client.js`、`agent-renderer.js`、KaTeX CDN（如未引入）
- [x] 1.4.2 实现 `init()`：认证守卫（未登录 → login.html），从 JWT 提取 student_name、class_name，渲染侧边栏个人资料
- [x] 1.4.3 实现消息发送：Enter 键 / 发送按钮 → 创建用户气泡 → 调用 `ChemSSE.connect('/api/v1/chat/stream', {message, thread_id, context: {student_id, student_name, class_name}}, handlers)`
- [x] 1.4.4 实现 `phase` 事件处理：状态栏实时切换（thinking→"分析中..."、executing→"执行中..."+ 秒表计时器、reply→"回复中..."、awaiting_approval→"等待确认"）
- [x] 1.4.5 实现 `text` 事件处理：流式追加/更新 AI 气泡内容（增量拼接），流完成后对气泡 DOM 调用 `ChemAPI.renderLatex()`
- [x] 1.4.6 实现文本去重：LLM 输出与上一条 `tool_result` 内容重叠 > 70% 时跳过渲染
- [x] 1.4.7 实现 `tool_call` 事件处理：插入工具调用卡片（"⚡ <工具中文名>" 标题 + 实时计时器，JetBrains Mono 红色等宽字体）
- [x] 1.4.8 实现 `tool_result` 事件处理：停止计时器 → `ChemAgentRender.render(toolName, result)` 渲染结构化 HTML 到卡片
- [x] 1.4.9 实现 5 个快捷选择项（Chips）：点击后填入输入框并自动发送
- [x] 1.4.10 实现侧边抽屉对话列表：打开时 `GET /api/v1/chat/conversations?prefix=s-` → 渲染列表项（title + time + message_count）
- [x] 1.4.11 实现对话切换：点击历史对话项 → `GET /api/v1/chat/history/{thread_id}` → 渲染完整消息历史到聊天区
- [x] 1.4.12 实现新建对话："+" 按钮 → `POST /api/v1/chat/new` → 清空聊天区 → 更新 `thread_id`
- [x] 1.4.13 实现删除对话：长按对话项 → 确认后 `DELETE /api/v1/chat/conversations/{thread_id}` → 从列表移除
- [x] 1.4.14 实现 `awaiting_approval` 审批卡片：黄色边框确认/取消卡片，确认后 POST 恢复执行
- [x] 1.4.15 实现退出登录：侧边栏 "退出登录" → `ChemAuth.logout()` → `location.href = "login.html"`
- [x] 1.4.16 实现 TabBar 导航：4 标签页点击跳转对应 HTML 页，当前页（AI 助教）高亮

---

## 阶段 2：练习页 + 错题本

### 2.1 练习页（`practice.html`）TabBar 修复

- [x] 2.1.1 TabBar "我的" 链接：`profile.html` → `report.html`
- [x] 2.1.2 验证 TabBar 4 标签页均正确跳转（AI 助教 → index.html / 练习(active) / 错题 → wrong.html / 我的 → report.html）

### 2.2 错题本（`wrong.html`）TabBar 修复

- [x] 2.2.1 TabBar "我的" 链接：`profile.html` → `report.html`
- [x] 2.2.2 验证 TabBar 4 标签页均正确跳转（AI 助教 → index.html / 练习 → practice.html / 错题(active) / 我的 → report.html）

### 2.3 练习→错题流程验证

- [x] 2.3.1 端到端验证：练习页答题提交 → TabBar 切换到错题本 → 确认新错题出现在列表中
- [x] 2.3.2 验证错题本 "生成变式题" → variant.html 携带正确 question_id 参数

---

## 阶段 3：复习中心 + 个人报告页

### 3.1 复习中心（`review.html`）TabBar 修复

- [x] 3.1.1 TabBar "我的" 链接：`profile.html` → `report.html`
- [x] 3.1.2 验证 TabBar 4 标签页均正确跳转

### 3.2 个人中心页改造（`report.html`）

- [x] 3.2.1 引入 `auth.js`、`api-client.js`、KaTeX CDN（如未引入）
- [x] 3.2.2 实现 `init()`：认证守卫、从 JWT 提取 student_name + class_name + binding_code，渲染个人资料卡片
- [x] 3.2.3 实现 stats 数据接入：`GET /api/v1/student/{user_id}/stats` → 渲染完成练习数、正确率、连续打卡天数三组数字
- [x] 3.2.4 实现 stats 加载失败降级：显示 "--" + 灰色文字 + Toast "加载失败"
- [x] 3.2.5 实现 "学习报告" 入口：打开底部弹出模态框 → 从已有 stats + diagnosis 数据组装练习次数、正确率、知识点进度条、教师评语
- [x] 3.2.6 实现 "学习计划" 入口：`GET /api/v1/learning-plan/{student_id}` → 渲染计划内容（每日任务列表）
- [x] 3.2.7 实现 "我的错题本" 和 "复习中心" 入口徽章数：`GET /api/v1/practice/wrong/list` count + `GET /api/v1/review/student/{id}/due` count → 实时数字徽章
- [x] 3.2.8 实现 "个人设置" 入口：Toast "设置功能即将上线"（占位）
- [x] 3.2.9 实现退出登录："退出登录" 按钮 → `ChemAuth.logout()` → `location.href = "login.html"`
- [x] 3.2.10 实现 TabBar 导航：4 标签页点击跳转 + "我的" 高亮
- [x] 3.2.11 验证个人中心 → 复习中心导航：点击 "复习中心" 入口 → review.html → 提交复习 → 返回个人中心查看更新后数据

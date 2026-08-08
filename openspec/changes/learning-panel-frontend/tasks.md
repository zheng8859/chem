## 1. 共享基础设施

- [ ] 1.1 在 `js/charts.js` 新增 SVG 折线图工具函数 `renderTrendChart(containerId, data, options)`，支持单数据点和空数组兜底
- [ ] 1.2 在 `js/api-client.js` 新增 `apiPatch` 方法，支持 PATCH 请求
- [ ] 1.3 提取预警类型/严重度的中文标签映射和颜色常量到共享 JS 模块

## 2. 班级学情面板（teacher.html 重写）

- [ ] 2.1 接入 `/panel/classes` API，实现班级选择器（默认选第一个，切换重新加载）
- [ ] 2.2 接入 `/panel/class/{class_id}` API，实现 4 张 KPI 概要卡片（考试次数、需关注学生、班级人数、加权均分），含加载态和数据为 null 的"--"占位
- [ ] 2.3 实现知识点错误率 Top 5 CSS 柱状图（柔性柱宽，含"暂无知识点数据"空态）
- [ ] 2.4 实现障碍类型 CSS conic-gradient 环形图（三扇区 + 底部图例，含"暂无诊断数据"空态）
- [ ] 2.5 接入 `/panel/class/{class_id}/exam-trend` API，调用 `renderTrendChart` 绘制 SVG 成绩趋势折线图（含"暂无考试数据"空态）
- [ ] 2.6 实现关注学生横向滚动卡片横条（展示预警类型标签、严重度颜色标记、预警数量；无关注学生时隐藏模块）
- [ ] 2.7 "需关注学生"KPI 卡片点击跳转 `warnings.html?class_id=X`
- [ ] 2.8 各模块独立错误态（错误提示 + 重试按钮，单模块失败不影响其他模块）

## 3. 预警管理页面（warnings.html 新建）

- [ ] 3.1 新建 `pages/warnings.html`，复用 teacher.html 的 header+breadcrumb+CSS 变量，面包屑"对话 / 预警中心"
- [ ] 3.2 接入 `/warning/stats` API，实现统计摘要条（severe/warning/info/total 四个数字，含颜色标记）
- [ ] 3.3 实现筛选工具栏（班级、类型、严重度、状态下拉框），支持 URL 参数 `class_id` 自动预选班级
- [ ] 3.4 接入 `/warning/list` API，实现预警列表表格（严重度色标 + 学生名 + 班级 + 类型标签 + 标题 + 时间 + 状态），含分页控件
- [ ] 3.5 实现预警详情抽屉（480px 右侧滑入），展示完整预警信息 + JSON 数据快照格式化
- [ ] 3.6 实现状态操作按钮（pending/processing → "标记已解决"+"标记误报"；resolved/dismissed → 隐藏操作按钮），调 `PATCH /warning/{id}/status`
- [ ] 3.7 实现"手动检测"按钮（调 `POST /warning/check`，显示 Toast，429 时提示"已有检测任务运行中"）
- [ ] 3.8 空列表态："暂无预警记录"

## 4. 学生管理页面（students.html 重写）

- [ ] 4.1 改造统计栏为动态数据（总人数/活跃/关注/均分从 API 聚合计算）
- [ ] 4.2 接入学生列表 API（分页），实现学生卡片网格（姓名 + 班级 + 障碍分布水平条三色段 + 详情按钮），含分页控件
- [ ] 4.3 实现搜索框实时过滤 + 障碍类型筛选 chip（概念/审题/表述）
- [ ] 4.4 接入 `/panel/class/{class_id}/student/{student_id}` API，实现 480px 详情抽屉（基本信息 + 障碍水平条 + SVG 正确率趋势迷你折线图 + 薄弱知识点标签云含 trend 颜色）
- [ ] 4.5 实现跨页面跳转支持：URL 参数 `?focus=SID` 自动打开指定学生详情抽屉
- [ ] 4.6 抽屉关闭交互：遮罩层点击 / 关闭按钮 / ESC 键

## 5. 跨页面导航与验证

- [ ] 5.1 teacher.html 导航栏新增"学生管理""预警中心"链接
- [ ] 5.2 students.html 导航栏与 teacher.html 保持一致
- [ ] 5.3 所有页面添加 JWT 登录校验（未登录跳转 login.html），复用 `auth.js` 的 `isAuthenticated()`
- [ ] 5.4 所有页面角色校验（仅 teacher/admin 角色可访问，学生/家长角色跳转对应页面），复用 `auth.js` 的 `getUserRole()`
- [ ] 5.5 端到端验证：启动后端 → 登录教师账号 → 验证三个页面的数据加载、交互、空态和错误态

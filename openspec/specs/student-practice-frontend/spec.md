## Purpose

学生端练习与复习前端页面，对接自适应练习引擎、间隔复习和错题训练后端 API，提供任务列表、逐题作答、自动判分、错题管理和复习跟踪的完整移动端体验。

## Requirements

### Requirement: 练习任务列表

练习页 SHALL 从 `GET /api/v1/practice/student/{uid}/tasks` 加载练习任务，按 status 分为"待完成"和"已完成"两组展示，每组带数量角标。

#### Scenario: 加载任务列表
- **WHEN** 学生进入练习页
- **THEN** 系统查询任务 API，按状态分组渲染任务卡片，每个卡片显示标题、知识点标签、进度条和操作按钮

#### Scenario: 待完成任务为空
- **WHEN** 待完成任务列表为空
- **THEN** 显示"暂无练习任务"空态文字

#### Scenario: 加载失败
- **WHEN** API 请求失败
- **THEN** 显示"加载失败"和重试按钮

### Requirement: 逐题作答

点击待完成任务卡片后，系统 SHALL 进入答题界面，逐题展示题目内容和选项，学生选择答案后 SHALL 自动推进到下一题，并保留已选答案状态。

#### Scenario: 展示选择题
- **WHEN** 题目类型为选择题且包含 options 字段
- **THEN** 渲染 A/B/C/D 四个选项按钮，点击后选中态为 Oxford Blue 边框

#### Scenario: 展示填空题
- **WHEN** 题目类型为填空题或 options 字段为空
- **THEN** 渲染文本输入框供学生输入答案

#### Scenario: 答案持久化
- **WHEN** 学生在第 2 题选择答案后点击"上一题"回到第 1 题
- **THEN** 第 1 题之前选择的答案保持选中状态

#### Scenario: 最后一题切换提交按钮
- **WHEN** 学生浏览到最后一题
- **THEN** 底部导航按钮从"下一题"切换为"提交"

#### Scenario: 第一题禁用上一题
- **WHEN** 学生在第 1 题
- **THEN** "上一题"按钮为禁用态

### Requirement: 提交答案和判分

学生完成全部题目后点击"提交"，系统 SHALL 调用 `POST /api/v1/practice/submit` 提交所有答案，SHALL 展示判分结果。

#### Scenario: 提交成功展示结果
- **WHEN** 提交 API 返回成功
- **THEN** 进入结果页，大号字体展示得分和正确率（如 "4/5 — 80%"），逐题展示判定（正确/错误）、正确答案和解析

#### Scenario: 重复提交
- **WHEN** 提交 API 返回 409 DUPLICATE_SUBMIT
- **THEN** 显示"该练习已提交"提示，跳回任务列表

#### Scenario: 提交失败
- **WHEN** 提交 API 返回其他错误或网络超时
- **THEN** 显示"提交失败，请重试"，保留已选答案，允许再次提交

### Requirement: 错题本列表

错题本 SHALL 从 `GET /api/v1/practice/wrong/list` 加载错题列表，按错误次数降序排列，支持知识点筛选和分页。

#### Scenario: 展示错题手风琴卡片
- **WHEN** 加载到错题数据
- **THEN** 每道错题渲染为可展开/折叠的卡片，折叠态显示题目摘要和障碍类型标签，展开态显示题目内容、学生错误答案（红色）、正确答案（绿色）、解析和操作按钮

#### Scenario: 知识点筛选
- **WHEN** 学生从筛选下拉框选择一个知识点
- **THEN** 系统以 `kp_filter` 参数重新请求 API，列表仅显示该知识点的错题

#### Scenario: 翻页
- **WHEN** 学生滚动到列表底部
- **THEN** 自动加载下一页数据追加到列表

#### Scenario: 无错题
- **WHEN** 错题列表为空
- **THEN** 显示绿色对勾图标和"暂无错题，继续保持！"

### Requirement: 标记已掌握

在错题卡片上点击"已掌握"，系统 SHALL 调用 `POST /api/v1/practice/wrong/{question_id}/master`，SHALL 将该题从列表中移除。

#### Scenario: 标记成功
- **WHEN** API 返回成功
- **THEN** 该错题卡片淡出并移除，统计数字更新

#### Scenario: 标记失败
- **WHEN** API 返回错误
- **THEN** 显示 Toast 提示"操作失败，请重试"

### Requirement: 变式题训练入口

错题卡片的"生成变式题"按钮 SHALL 跳转到变式题训练页面 `variant.html`，传递原题 ID 和数量（3 道）作为 URL 参数。

#### Scenario: 点击生成变式题
- **WHEN** 学生在错题卡片上点击"生成变式题"
- **THEN** 页面跳转到 `variant.html?question_id={id}&count=3`

### Requirement: 变式题生成与训练

变式题页面 SHALL 先调用 `POST /api/v1/practice/wrong-topic/variant/generate` 生成 3 道变式题，再调用 `POST /api/v1/practice/wrong-topic/training/create` 创建训练会话，学生在逐题作答后可调用 `POST /api/v1/practice/wrong-topic/training/submit` 提交。

#### Scenario: 生成变式题加载
- **WHEN** 页面加载且检测到 URL 参数 question_id
- **THEN** 自动调用变式题生成 API，按钮显示"正在生成变式题..."并禁用

#### Scenario: 生成成功进入答题
- **WHEN** 生成 API 返回 3 道变式题
- **THEN** 创建训练会话，进入逐题答题界面

#### Scenario: 生成失败
- **WHEN** 生成 API 返回错误
- **THEN** 按钮文字变为"生成失败，点击重试"，允许重试

#### Scenario: 训练提交展示结果
- **WHEN** 训练提交 API 返回成功
- **THEN** 展示正确率百分比、逐题判定结果和分级学习建议

### Requirement: 复习中心待复习列表

复习中心 SHALL 从 `GET /api/v1/review/student/{id}/due` 加载待复习任务列表，按 next_review_at 升序排列（最紧急排最前）。

#### Scenario: 展示待复习卡片
- **WHEN** 加载到待复习任务
- **THEN** 每道任务渲染为卡片，显示题目摘要、Level 徽章（0-5 不同颜色）、下次复习日期和"开始复习"按钮

#### Scenario: 区分逾期任务
- **WHEN** 某任务的 next_review_at 已过当前时间
- **THEN** 该卡片用红色强调标记"已逾期"

#### Scenario: 无待复习任务
- **WHEN** 待复习列表为空
- **THEN** 显示"暂无待复习题目"

### Requirement: 复习答题与提交

学生点击"开始复习"后，系统 SHALL 展示题目和选项，学生作答后点击"答对"或"答错"按钮，调用 `POST /api/v1/review/submit` 提交结果。

#### Scenario: 提交答对
- **WHEN** 学生点击"答对"并 API 返回成功
- **THEN** 展示新的复习级别和下次复习日期，若到达 Level 5 则显示"恭喜！已掌握"并将卡片变为半透明

#### Scenario: 提交答错
- **WHEN** 学生点击"答错"并 API 返回成功
- **THEN** 复习级别回退，展示新的下次复习日期

#### Scenario: 提交失败
- **WHEN** API 返回错误
- **THEN** 保留当前选择，显示重试提示

### Requirement: JWT 认证注入

所有 API 请求 SHALL 自动携带 JWT token。若收到 401 响应，SHALL 重定向到登录页。

#### Scenario: 无 token 访问页面
- **WHEN** 页面加载时 localStorage 中无 JWT token
- **THEN** 重定向到 `login.html`

#### Scenario: token 过期
- **WHEN** API 返回 401
- **THEN** 清除存储的 token 并重定向到 `login.html`

### Requirement: KaTeX 化学式渲染

题目内容中的 `$...$` 包裹的 LaTeX 化学式 SHALL 通过 KaTeX mhchem 扩展渲染为正确的化学方程式。

#### Scenario: 渲染化学方程式
- **WHEN** 题目 content 包含 `$2Fe + 3Cl_2 \rightarrow 2FeCl_3$`
- **THEN** 渲染为带有正确上下标和箭头的化学方程式

#### Scenario: 渲染 mhchem 语法
- **WHEN** 题目 content 包含 `$\ce{Na2CO3 + 2HCl -> 2NaCl + H2O + CO2}$`
- **THEN** 渲染为正确的化学方程式

### Requirement: 组件状态处理

所有数据加载组件 SHALL 处理加载态、空态和错误态三种状态。

#### Scenario: 加载态 — 骨架屏
- **WHEN** 数据正在请求中且超过 300ms
- **THEN** 显示骨架屏（灰色占位卡片）或加载文字

#### Scenario: 错误态 — 重试
- **WHEN** API 请求失败
- **THEN** 显示错误描述和重试按钮

### Requirement: 跨页导航

学生端底部 TabBar SHALL 在 4 个页面中保持一致：AI 助教、练习、错题、我的，当前页 Tab 为 Oxford Blue 高亮态。

#### Scenario: TabBar 导航
- **WHEN** 学生点击 TabBar 中的"练习" Tab
- **THEN** 跳转到 `practice.html`

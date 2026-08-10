## 1. 共享基础设施

- [x] 1.1 创建 `frontend/js/auth.js`：JWT token 存取（localStorage）、`getCurrentUser()` 从 JWT payload 解码用户 ID 和角色、`redirectToLogin()` 跳转登录页
- [x] 1.2 创建 `frontend/js/api-client.js`：`apiGet(url, params)` / `apiPost(url, body)` 封装 fetch，自动注入 `Authorization: Bearer <token>`、统一处理 401 → 跳转登录、4xx/5xx 错误解析
- [x] 1.3 在 `api-client.js` 中实现 `renderLatex(containerEl)` 工具函数，通过 KaTeX + mhchem CDN 渲染 `$...$` 内的化学式，并提供降级方案（CDN 失败时保留原始文本）

## 2. 练习页 practice.html

- [x] 2.1 引入 `auth.js` 和 `api-client.js`，页面加载时检查 token，无 token 跳转登录页
- [x] 2.2 实现 Task List View：调用 `GET /api/v1/practice/student/{uid}/tasks`，按 status 分"待完成"/"已完成"两组渲染任务卡片，含标题、知识点标签、进度条、操作按钮
- [x] 2.3 实现 Quiz View：点击"继续练习"后，根据 PracticeSession 数据渲染题目列表，支持选择题（A/B/C/D 选项按钮）和填空题（文本输入框）
- [x] 2.4 实现答案持久化：`selectedAnswers` map 存储每题的选中答案，切换题目时保留并恢复选中状态
- [x] 2.5 实现底部导航：第一题禁用"上一题"，最后一题显示"提交"按钮，中间题显示"上一题"/"下一题"
- [x] 2.6 实现 Result View：调用 `POST /api/v1/practice/submit`，解析返回的 score/total/accuracy/逐题判定，渲染大号分数 + 正确率 + 逐题正确/错误/解析
- [x] 2.7 实现状态处理：任务列表加载中骨架屏、空态"暂无练习任务"、提交失败保留答案 + 重试、重复提交 409 提示并回列表
- [x] 2.8 KaTeX 渲染集成：题目 content 和解析中的 `$...$` 化学式渲染

## 3. 错题本 wrong.html

- [x] 3.1 引入 `auth.js` 和 `api-client.js`，页面加载时检查 token
- [x] 3.2 对接到错题 API：`GET /api/v1/practice/wrong/list?student_id={id}&limit=20&offset=0`，替换现有 3 张静态卡片
- [x] 3.3 实现知识点筛选：调用 `GET /api/v1/practice/wrong-topic/knowledge-points` 获取筛选选项，下拉选择后以 `kp_filter` 参数重新请求
- [x] 3.4 实现分页加载：滚动到底部自动加载下一页（offset += limit），追加到列表
- [x] 3.5 实现"已掌握"按钮：调用 `POST /api/v1/practice/wrong/{qid}/master`，成功后卡片淡出移除，统计数字更新
- [x] 3.6 "生成变式题"按钮改为跳转：`location.href = 'variant.html?question_id={id}&count=3'`
- [x] 3.7 实现状态处理：加载中骨架屏、空态绿色对勾 + "暂无错题，继续保持！"、API 失败内联错误 + 重试
- [x] 3.8 KaTeX 渲染集成：错题 content 和解析中的 `$...$` 化学式渲染

## 4. 变式题训练 variant.html（新页面）

- [x] 4.1 创建 `variant.html`：基于现有页面骨架复用 CSS 设计令牌和 TabBar 布局
- [x] 4.2 从 URL 读取 `question_id` 和 `count` 参数，无参数时显示错误提示
- [x] 4.3 实现变式题生成流程：调用 `POST /api/v1/practice/wrong-topic/variant/generate`（传入 question_id, count=3），生成中 loading 态，失败时"重试"按钮
- [x] 4.4 实现训练答题流程：生成成功后调用 `POST /api/v1/practice/wrong-topic/training/create` 创建训练会话，进入逐题答题界面
- [x] 4.5 实现训练提交与结果：调用 `POST /api/v1/practice/wrong-topic/training/submit`，展示正确率、逐题判定和分级学习建议（≥90%/≥70%/≥50%/<50% 四档）
- [x] 4.6 KaTeX 渲染集成

## 5. 复习中心 review.html

- [x] 5.1 引入 `auth.js` 和 `api-client.js`，页面加载时检查 token
- [x] 5.2 对接到复习 API：`GET /api/v1/review/student/{id}/due` 加载待复习任务，按 next_review_at 升序排列
- [x] 5.3 渲染复习卡片：Level 0-5 徽章（各级别不同颜色）、题目摘要、下次复习日期、逾期红色强调、"开始复习"按钮
- [x] 5.4 实现复习答题交互：展示题目 + 选项，底部"答对"/"答错"两个按钮
- [x] 5.5 实现提交复习：调用 `POST /api/v1/review/submit`，更新级别显示和下次复习日期，Level 5 展示"恭喜！已掌握"并变半透明
- [x] 5.6 实现统计区动态数据：从到期任务列表计算"待复习"/"今日已复习"/"已掌握"三个数字
- [x] 5.7 实现状态处理：加载中统计数字闪烁 + 骨架卡片、空态"暂无待复习题目"、提交错误保留选择 + 重试
- [x] 5.8 KaTeX 渲染集成

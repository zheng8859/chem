## 1. 基础架构搭建

- [x] 1.1 在 `exam-v2.html` 中引入 Vue 3 CDN + KaTeX + mhchem CDN，替换 vanilla JS 脚本
- [x] 1.2 创建 API 层（`api` 对象）：封装 `get/post/patch/del` 方法，统一 base URL `/api/v1`、auth token 注入、错误处理、30s 超时
- [x] 1.3 创建全局响应式状态（`reactive`）：`currentTab`、`questions`、`folders`、`exams`、`historicalExams`、`modal`
- [x] 1.4 创建 Vue 应用并挂载到 `#app`，配置全局错误处理

## 2. Tab 导航与页面框架

- [x] 2.1 将四个 Tab 面板从 `display:none` 迁移为 Vue `v-show` 控制切换
- [x] 2.2 Tab 按钮点击事件绑定，切换 `currentTab` 状态，active 样式绑定
- [x] 2.3 保留原型顶部 header（品牌 + 面包屑 + 用户头像），不做功能变更

## 3. API 接入 — Tab 1 出题工作台（AI 生成）

- [x] 3.1 题型 chip 改为多选模式（`v-for` 渲染 chip 列表，点击切换 `selected` 态）
- [x] 3.2 选中题型后显示数量微调控件（`-` / 数字 / `+`），绑定每种题型的生成数量
- [x] 3.3 知识点搜索框接入 `GET /api/v1/knowledge-points?keyword=`，搜索结果以下拉列表展示，支持多选 chip
- [x] 3.4 变体模式复选框 + 蓝本题选择器（打开蓝本题浏览弹窗，从历史真题 API 加载）
- [x] 3.5 "生成题目"按钮绑定 `POST /api/v1/questions/generate`，实现 loading 态（禁用 + 旋转图标）和错误态（Toast 提示）
- [x] 3.6 生成结果以题目卡片列表渲染（`v-for`），每张卡片包含：KaTeX 渲染的题目内容、选项、四维审核徽章

## 4. KaTeX 化学式渲染

- [x] 4.1 编写 `v-katex` 自定义指令：扫描元素文本中的 `$...$` 公式，调用 `katex.renderToString()` 渲染
- [x] 4.2 KaTeX 配置 mhchem 扩展，支持 `\ce{...}` 语法
- [ ] 4.3 验证两类语法渲染正确：LLM 输出的 `$...$` 和用户输入的 `\ce{...}`

## 5. 四维审核徽章与题目操作

- [x] 5.1 审核徽章组件：根据 `auditReport` 数据显示 passed=绿/warning=黄/blocked=红 三种状态
- [x] 5.2 陷阱提示折叠面板：根据题目 `knowledge_point_tags` 匹配教学提示并展示
- [x] 5.3 RAG 来源标识：当题目含 `rag_mark` 时显示来源标签（如"基于全国卷2024 T7 变体生成"）
- [x] 5.4 题目操作按钮：编辑（打开编辑弹窗）、收藏（调用 API 保存到题库）、加入考试（打开考试选择弹窗）

## 6. API 接入 — Tab 1 子模式（手动录入 + OCR 导入）

- [x] 6.1 模式切换按钮改为三态（AI 生成 / 手动录入 / OCR 导入），用 `v-if` 切换表单内容
- [x] 6.2 手动录入表单：题目正文（textarea）、动态选项行（`+/-` 按钮）、正确答案、知识点选择器、难度下拉、解析、提交按钮调用 `POST /api/v1/questions/import`
- [x] 6.3 OCR 上传区域：拖拽上传 + 点击选择文件，支持 JPG/PNG/PDF，调用 `POST /api/v1/ocr/sessions`
- [x] 6.4 OCR 进度轮询：上传后轮询 `GET /api/v1/ocr/sessions/{id}/tasks`（5s 间隔），展示进度条
- [x] 6.5 OCR 识别结果预览表格：展示学号/姓名/答案摘要/状态，支持编辑修正
- [x] 6.6 OCR 确认批量入库：调用 `POST /api/v1/questions/import` 批量保存

## 7. API 接入 — Tab 2 题库管理

- [x] 7.1 左侧文件夹列表接入 `GET /api/v1/question-sets`，选中态切换
- [x] 7.2 右侧题目卡片网格接入文件夹详情，支持 `v-for` 渲染
- [x] 7.3 滚动加载分页：`IntersectionObserver` 监听底部哨兵元素，触底加载下一页
- [x] 7.4 新建文件夹按钮 + prompt 弹窗，调用 `POST /api/v1/question-sets`

## 8. API 接入 — Tab 3 历史真题库

- [x] 8.1 地区/年份筛选下拉框绑定 `GET /api/v1/historical-exams?source=&year=`
- [x] 8.2 关键词搜索框（300ms 防抖），绑定 `GET /api/v1/historical-exams?knowledge_point=`
- [x] 8.3 真题卡片列表渲染（地区标签 + 年份标签 + 题目数），滚动加载分页
- [x] 8.4 "设为蓝本题"按钮：将选中的真题 ID 传回 Tab 1 变体模式

## 9. API 接入 — Tab 4 考试列表

- [x] 9.1 考试列表接入 `GET /api/v1/exams`，状态标签（草稿/进行中/已结束）颜色区分
- [x] 9.2 创建考试：prompt 弹窗（名称 + 班级选择），调用 `POST /api/v1/exams`
- [x] 9.3 发布考试：确认弹窗 → 调用 `POST /api/v1/exams/{id}/publish` → 状态更新
- [x] 9.4 传统分页控件（上一页/下一页/页码），切换后重新加载

## 10. 弹窗系统

- [x] 10.1 全局弹窗容器（`<Teleport to="body">`），绑定 `modal` 响应式状态
- [x] 10.2 Confirm 弹窗：标题 + 消息 + 取消/确认按钮，返回 Promise<boolean>
- [x] 10.3 Prompt 弹窗：标题 + 输入框 + 取消/确认按钮，返回 Promise<string|null>
- [x] 10.4 Select 弹窗：标题 + 列表选项（如选择目标考试/题库文件夹），返回 Promise<selected>
- [x] 10.5 Preview 弹窗：大内容区展示题目详情（含 KaTeX 渲染）
- [x] 10.6 Variant Browser 弹窗：从历史真题 API 加载列表，单选蓝本题

## 11. 组件状态处理

- [x] 11.1 加载态骨架屏：为题目卡片列表、文件夹列表、考试列表、真题列表编写骨架屏
- [x] 11.2 空态引导：题库为空、无考试、无真题、无生成结果四种空态
- [x] 11.3 错误态重试：API 失败时显示错误描述 + 重试按钮
- [x] 11.4 Toast 通知组件：成功/错误/警告三种，右上角浮出，3s 自动消失

## 12. 跨 Tab 数据同步

- [x] 12.1 Tab 1 生成题目"加入题库"后，刷新 Tab 2 的共享 `folders` 状态
- [x] 12.2 Tab 2/3 选题"加入考试"后，刷新 Tab 4 的考试题目列表
- [x] 12.3 Tab 切换时不丢失未保存的表单状态（`v-show` 保活已满足）

## 13. 验证与收尾

- [x] 13.1 检查所有 API 端点路径与后端实际路径一致（对照 `app/api/v1/` 路由定义）
- [ ] 13.2 验证四 Tab 切换 + 三 Mode 切换全部正常
- [ ] 13.3 验证 KaTeX 渲染：LLM 生成题目、手动录入化学式、真题内容三种场景
- [ ] 13.4 验证审核徽章：passed/warning/blocked 三种状态正确展示
- [ ] 13.5 验证错误处理：断开后端后各组件显示重试态
- [ ] 13.6 在 1280px 视口下检查无溢出、无布局错乱

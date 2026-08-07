## Purpose

出题工作台前端页面 — 教师通过四 Tab 单页应用完成 AI 出题、题库管理、真题浏览和考试管理，支持三种出题模式（AI 生成/手动录入/OCR 导入）和化学式 KaTeX 渲染。

## ADDED Requirements

### Requirement: 四 Tab 导航

页面 SHALL 提供四个 Tab（出题工作台、题库管理、历史真题库、考试列表）供教师切换。Tab 切换 SHALL 不触发页面导航，仅切换内容区显示。

#### Scenario: 默认激活第一个 Tab
- **WHEN** 页面首次加载
- **THEN** "出题工作台" Tab 为激活态，下划线指示，其内容面板可见

#### Scenario: 点击切换 Tab
- **WHEN** 教师点击"题库管理" Tab
- **THEN** 该 Tab 显示激活态，出题工作台面板隐藏，题库管理面板显示

### Requirement: AI 生成出题配置

出题工作台 SHALL 提供 AI 生成出题模式，教师可配置题型、难度、知识点、变体模式和目标题库文件夹。

#### Scenario: 配置题型和数量
- **WHEN** 教师点击题型 chip（选择题/填空题/计算题/方程式配平/实验探究）
- **THEN** chip 切换选中态，允许多选，每种选中题型可配置生成数量

#### Scenario: 选择难度
- **WHEN** 教师从难度下拉框选择"困难"
- **THEN** 难度值更新为 `hard`，传递给生成 API

#### Scenario: 搜索并选择知识点
- **WHEN** 教师在知识点搜索框输入"氧化"
- **THEN** 系统调用 `GET /api/v1/knowledge-points?keyword=氧化`，显示匹配的知识点列表供多选

#### Scenario: 勾选变体模式
- **WHEN** 教师勾选"基于真题变体"复选框
- **THEN** "选择蓝本题"按钮变为可用态，点击后打开蓝本题浏览弹窗，从 Tab 3 选择真题作为变体蓝本

### Requirement: AI 生成题目与展示

教师点击"生成题目"按钮后，系统 SHALL 调用后端生成接口，展示生成进度和结果卡片。

#### Scenario: 生成中状态
- **WHEN** 教师点击"生成题目"按钮且参数有效
- **THEN** 按钮变为 loading 态（禁用 + 旋转图标），显示"生成中..."

#### Scenario: 生成成功展示题目卡片
- **WHEN** `POST /api/v1/questions/generate` 返回成功
- **THEN** 每道题目渲染为一张卡片，包含：KaTeX 渲染的题目内容、选项（选择题）、四维审核徽章（配平/条件/产物/结构，passed=绿/warning=黄/blocked=红）、RAG 来源标识、陷阱提示折叠面板、操作按钮（编辑/收藏/加入考试/加入题库）

#### Scenario: 生成失败
- **WHEN** API 返回错误或超时
- **THEN** 生成按钮恢复可用，Toast 显示错误原因，已生成的部分题目（如有）保留在列表中

### Requirement: 四维审核徽章

每道 AI 生成的题目卡片 SHALL 展示四维审核徽章（配平、条件、产物、结构），徽章颜色反映审核状态。

#### Scenario: 全部通过
- **WHEN** 四个维度审核状态均为 `passed`
- **THEN** 四个徽章均为绿色背景 + 深绿文字，显示 ✓ 图标

#### Scenario: 部分警告
- **WHEN** 条件维度返回 `warning`
- **THEN** 对应徽章为黄色背景 + 深棕文字，显示 ⚠ 图标

#### Scenario: 审核阻断
- **WHEN** 任一维度返回 `blocked`
- **THEN** 对应徽章为红色背景 + 深红文字，显示 ✗ 图标，该题目卡片底部标注"审核未通过，不会下发给学生"

### Requirement: 手动录入出题

出题工作台 SHALL 提供手动录入模式，教师填写表单后提交保存题目。

#### Scenario: 填写手动录入表单
- **WHEN** 教师切换到"手动录入"模式
- **THEN** 显示表单：题目正文（textarea）、选项（动态 +/- 行，仅选择题）、正确答案、知识点选择器、难度下拉框、解析（可选）

#### Scenario: 提交手动录入
- **WHEN** 教师点击"保存题目"按钮
- **THEN** 调用 `POST /api/v1/questions/import`，成功后 Toast 提示"题目已保存"，表单清空

### Requirement: OCR 扫描导入

出题工作台 SHALL 提供 OCR 导入模式，教师上传答题卡或试卷图片后进行识别、预览和确认入库。

#### Scenario: 拖拽上传
- **WHEN** 教师拖拽 JPG/PNG/PDF 文件到上传区域
- **THEN** 文件上传到 `POST /api/v1/ocr/sessions`，上传区显示进度

#### Scenario: OCR 识别预览
- **WHEN** 上传完成
- **THEN** 轮询 `GET /api/v1/ocr/sessions/{id}/tasks` 获取识别进度，完成后展示识别结果预览表格

#### Scenario: 确认入库
- **WHEN** 教师在预览表格中确认识别结果并点击"批量保存"
- **THEN** 调用 `POST /api/v1/questions/import` 批量保存，成功后 Toast 提示

### Requirement: 题库管理

题库管理 Tab SHALL 展示教师创建的题库文件夹列表和对应题目网格，支持滚动加载分页。

#### Scenario: 浏览文件夹
- **WHEN** 教师切换到"题库管理" Tab
- **THEN** 调用 `GET /api/v1/question-sets` 加载文件夹列表到左侧栏

#### Scenario: 查看文件夹题目
- **WHEN** 教师点击一个文件夹
- **THEN** 右侧显示该文件夹的题目卡片网格，每张卡片包含题目类型、预览内容、题目数量

#### Scenario: 滚动加载更多
- **WHEN** 教师滚动到题目网格底部
- **THEN** 自动加载下一页题目数据（offset += limit），追加到网格末尾

### Requirement: 历史真题库

历史真题库 Tab SHALL 提供真题的按条件筛选和关键词搜索。

#### Scenario: 地区筛选
- **WHEN** 教师从地区下拉框选择"北京"
- **THEN** 调用 `GET /api/v1/historical-exams?source=北京`，列表刷新

#### Scenario: 年份筛选
- **WHEN** 教师从年份下拉框选择"2024"
- **THEN** 调用 `GET /api/v1/historical-exams?year=2024`，列表刷新

#### Scenario: 关键词搜索
- **WHEN** 教师在搜索框输入"氧化还原"并按回车或延迟 300ms
- **THEN** 调用 `GET /api/v1/historical-exams?knowledge_point=氧化还原`，列表刷新

### Requirement: 真题卡片加入考试

Tab 3 历史真题库的每张真题卡片 SHALL 提供"加入考试"按钮。点击后 SHALL 弹出 checklist 弹窗列出所有可用考试，教师选择目标考试后 SHALL 调用 `POST /api/v1/exams/{id}/questions` 将真题关联到考试。真题从 HistoricalExam 复制时 source 设为 `manual`。

#### Scenario: 将真题加入考试
- **WHEN** 教师在真题卡片上点击"加入考试"并选择目标考试
- **THEN** 真题被添加到该考试，Toast 提示"已加入考试"

#### Scenario: 无考试可选时提示
- **WHEN** 教师点击"加入考试"但考试列表为空
- **THEN** Toast 提示"暂无可用考试，请先创建考试"

### Requirement: 考试列表管理

考试列表 Tab SHALL 展示考试记录、支持创建考试、发布和状态流转。

#### Scenario: 查看考试列表
- **WHEN** 教师切换到"考试列表" Tab
- **THEN** 调用 `GET /api/v1/exams` 加载考试记录，每条显示名称、日期、题数、人数、状态标签

#### Scenario: 创建考试
- **WHEN** 教师点击"创建考试"按钮
- **THEN** 弹出输入弹窗（考试名称 + 班级选择 + 日期），确认后调用 `POST /api/v1/exams`，新考试出现在列表

#### Scenario: 发布考试
- **WHEN** 教师在草稿态考试上点击"发布"
- **THEN** 调用 `POST /api/v1/exams/{id}/publish`，成功后状态标签变为"进行中"

### Requirement: KaTeX 化学式渲染

前端 SHALL 通过 KaTeX + mhchem 渲染题目内容中的化学式，同时支持 `$...$` 包裹的 LaTeX 公式和 `\ce{...}` mhchem 语法。

#### Scenario: 渲染 LLM 生成的 LaTeX 公式
- **WHEN** 题目 content 字段包含 `$2H_2 + O_2 \rightarrow 2H_2O$`
- **THEN** 渲染为正确上下标和箭头的化学方程式

#### Scenario: 渲染用户输入的 mhchem 语法
- **WHEN** 手动录入 textarea 中输入 `\ce{CH4 + 2O2 -> CO2 + 2H2O}`
- **THEN** 渲染为正确的化学方程式

### Requirement: 弹窗系统

页面 SHALL 提供全局弹窗系统，支持确认、输入、选择、预览、管理和蓝本题浏览六种类型。

#### Scenario: 确认弹窗
- **WHEN** 教师点击删除题库
- **THEN** 弹出确认弹窗："确定要删除【化学】题库吗？"，底部"取消"+"删除"按钮

#### Scenario: 输入弹窗
- **WHEN** 教师点击"新建文件夹"
- **THEN** 弹出输入弹窗：文本输入框 + "取消"+"确认"按钮

### Requirement: 组件状态处理

所有数据加载组件 SHALL 处理加载态、空态和错误态。

#### Scenario: 加载态 — 骨架屏
- **WHEN** 数据正在请求中（> 200ms）
- **THEN** 显示骨架屏（灰色占位条/卡片），而非空白区域

#### Scenario: 空态 — 引导文字
- **WHEN** 题库文件夹列表为空
- **THEN** 显示"暂无题库，请先在出题工作台创建题目"引导文字 + 创建按钮

#### Scenario: 错误态 — 重试
- **WHEN** API 请求失败（网络错误或 5xx）
- **THEN** 对应区域显示错误描述 + "重试"按钮，点击后重新请求

### Requirement: 跨 Tab 数据共享

不同 Tab 之间 SHALL 共享题目和考试数据，避免切换 Tab 时不必要的重新加载。

#### Scenario: 生成题目后切换到题库管理
- **WHEN** 教师在 Tab 1 生成题目并点击"加入题库"
- **THEN** 切换到 Tab 2 时，新加入的题目出现在对应文件夹中（通过共享状态或触发重新加载）

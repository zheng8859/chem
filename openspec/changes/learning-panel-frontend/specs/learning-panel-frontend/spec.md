## Purpose

为教师提供交互式班级学情仪表盘，通过消费 `/api/v1/panel/*` 后端 API 实现数据驱动的 KPI 概览、三维图表可视化和重点关注学生识别，替代静态 HTML 原型。

## ADDED Requirements

### Requirement: 班级选择与数据加载

教师进入学情面板页面 SHALL 自动加载所教班级列表，默认选中第一个班级并展示其学情数据。

#### Scenario: 教师仅有单个班级
- **WHEN** 教师仅任教 1 个班级
- **THEN** 班级选择器显示该班级名称且不可切换，面板自动展示该班级数据

#### Scenario: 教师任教多个班级
- **WHEN** 教师任教多个班级
- **THEN** 班级选择器列出所有班级，默认选中第一个，切换班级后重新加载面板数据

#### Scenario: 无任教班级
- **WHEN** 教师无任教班级（如 admin 角色）
- **THEN** 班级选择器显示空态提示"暂无任教班级"

### Requirement: KPI 概要卡片

班级学情面板 SHALL 在顶部以 4 列网格展示 KPI 概要卡片。

#### Scenario: 正常展示
- **WHEN** 班级有考试和练习数据
- **THEN** 展示四张卡片：考试次数、需关注学生数（预警未处理人数）、班级人数、班级加权均分，数据来自 `GET /api/v1/panel/class/{class_id}`

#### Scenario: 无数据班级
- **WHEN** 班级无任何考试记录
- **THEN** 考试次数显示 0，均分显示"--"，需关注学生显示 0

#### Scenario: 关注学生卡片点击跳转
- **WHEN** 教师点击"需关注学生"KPI 卡片
- **THEN** 跳转至预警管理页面（`warnings.html`），携带 `class_id` 参数预筛选当前班级

### Requirement: 知识点错误率柱状图

面板 SHALL 展示班级知识点错误率 Top 5 的柱状图。

#### Scenario: 正常展示
- **WHEN** 班级有考试或练习数据
- **THEN** 以 CSS 柱状图展示前 5 个高错误率知识点，每柱显示知识点名称和错误率百分比，按错误率降序排列

#### Scenario: 无数据
- **WHEN** `knowledge_points` 为空数组
- **THEN** 图表区域显示"暂无知识点数据"

### Requirement: 障碍类型环形图

面板 SHALL 展示班级障碍类型分布环形图。

#### Scenario: 正常展示
- **WHEN** 班级有已诊断学生
- **THEN** 以 CSS conic-gradient 环形图展示三种障碍类型（concept 紫色、reading 蓝色、expression 青色）占比，图例置于底部

#### Scenario: 无数据
- **WHEN** `barrier_distribution` 为空数组
- **THEN** 图表区域显示"暂无诊断数据"

### Requirement: 成绩趋势折线图

面板 SHALL 展示班级历次考试的均分变化趋势。

#### Scenario: 正常展示
- **WHEN** 班级有 2 次及以上考试记录
- **THEN** 以 SVG polyline 折线图展示班级均分趋势，X 轴为考试名称，Y 轴为均分（百分制），单线无图例

#### Scenario: 仅一次考试
- **WHEN** 班级仅有 1 次考试记录
- **THEN** 折线图显示单个数据点，无连线

#### Scenario: 无数据
- **WHEN** `exam-trend` 返回空数组
- **THEN** 图表区域显示"暂无考试数据"

### Requirement: 关注学生横条

面板底部 SHALL 展示预警未处理的学生卡片横条。

#### Scenario: 有未处理预警
- **WHEN** 班级存在未处理预警的学生
- **THEN** 以横向滚动横条展示关注学生卡片，每张卡片含姓名首字头像、姓名、预警类型标签（配色按类型区分）、预警严重度颜色标记、预警数量

#### Scenario: 无关注学生
- **WHEN** 班级无未处理预警
- **THEN** 隐藏该模块

### Requirement: 加载与空态处理

面板所有模块 SHALL 正确处理加载中和无数据状态。

#### Scenario: API 请求中
- **WHEN** 面板数据正在加载
- **THEN** KPI 卡片显示占位文本，图表区显示加载指示器

#### Scenario: API 请求失败
- **WHEN** 任一 API 返回 4xx/5xx 或网络错误
- **THEN** 对应模块显示错误提示和重试按钮，其他模块正常展示

### Requirement: 页面导航

学情面板 SHALL 与后端教师页面保持一致的导航结构。

#### Scenario: 顶部导航
- **WHEN** 教师在学情面板页面
- **THEN** 顶部导航栏包含品牌标识、面包屑导航（对话 / 班级学情）、教师姓名和头像，导航项含"对话""班级学情""学生管理""预警中心"

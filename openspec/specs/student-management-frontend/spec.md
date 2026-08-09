## Purpose

为教师提供交互式学生管理页面，支持搜索筛选、分页浏览和右侧详情抽屉（含学生画像、障碍分布、成绩趋势和薄弱知识点），消费 `/api/v1/panel/class/{id}/student/{sid}` 等后端 API。

## ADDED Requirements

### Requirement: 统计栏

学生管理页面顶部 SHALL 展示班级级统计数字。

#### Scenario: 正常展示
- **WHEN** 教师进入学生管理页面且当前班级有学生
- **THEN** 展示四项统计：总人数、活跃学生数（最近 7 天有练习记录）、关注学生数（有未处理预警）、班级均分

#### Scenario: 班级切换
- **WHEN** 教师切换班级筛选
- **THEN** 统计栏和学生卡片网格同步更新

### Requirement: 搜索与筛选

学生管理页面 SHALL 提供搜索框和筛选 chip。

#### Scenario: 姓名搜索
- **WHEN** 教师在搜索框输入学生姓名
- **THEN** 学生卡片网格实时过滤，仅显示姓名匹配的学生

#### Scenario: 障碍类型筛选
- **WHEN** 教师点击障碍类型筛选 chip（概念/审题/表述）
- **THEN** 仅显示主导障碍为该类型的学生

### Requirement: 学生卡片网格

学生管理页面 SHALL 以卡片网格展示学生列表。

#### Scenario: 正常展示
- **WHEN** 学生列表加载完成
- **THEN** 以 3 列网格展示学生卡片，每张卡片含：姓名、班级、障碍分布水平条（concept 紫 / reading 蓝 / expression 青三段）、"详情"按钮

#### Scenario: 分页
- **WHEN** 学生总数超过单页条数（默认 20）
- **THEN** 底部分页控件显示

#### Scenario: 空列表
- **WHEN** 无匹配学生
- **THEN** 网格区显示"未找到匹配的学生"

### Requirement: 学生详情抽屉

点击学生卡片 SHALL 打开 480px 右侧滑出抽屉展示学生详情。

#### Scenario: 基本信息
- **WHEN** 抽屉打开
- **THEN** 顶部展示学生姓名、学号、班级

#### Scenario: 障碍分布水平条
- **WHEN** 学生有障碍画像数据
- **THEN** 展示三种障碍类型的水平进度条（concept 紫 / reading 蓝 / expression 青），含百分比数值

#### Scenario: 成绩趋势迷你折线图
- **WHEN** 学生有正确率趋势数据（`accuracy_trend` 非空）
- **THEN** 以 SVG polyline 展示正确率变化趋势，X 轴为日期，Y 轴为正确率

#### Scenario: 薄弱知识点标签云
- **WHEN** 学生有薄弱知识点数据（`weak_knowledge_points` 非空）
- **THEN** 以标签云展示薄弱知识点，每个标签含知识点名称、错误率，trend 为 "up" 时标记绿色、trend 为 "down" 时标记红色

#### Scenario: 关闭抽屉
- **WHEN** 教师点击遮罩层、关闭按钮或按 ESC 键
- **THEN** 抽屉滑出关闭

#### Scenario: 数据加载失败
- **WHEN** 学生详情 API 返回错误
- **THEN** 抽屉内显示"加载失败，请关闭后重试"

### Requirement: 跨页面跳转支持

学生管理页面 SHALL 支持从学情面板或预警页面跳转打开指定学生详情。

#### Scenario: 从关注学生卡片跳转
- **WHEN** 教师在学情面板点击某个关注学生的卡片
- **THEN** 跳转至 `students.html`，自动选中对应班级，自动打开该学生的详情抽屉

#### Scenario: 从预警详情跳转
- **WHEN** 教师在预警详情抽屉中点击学生姓名
- **THEN** 跳转至 `students.html`，自动打开该学生的详情抽屉

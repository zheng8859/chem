## Purpose

为教师提供交互式预警管理中心，通过消费 `/api/v1/warning/*` 后端 API 实现预警列表（筛选+分页）、统计摘要、预警详情查看和状态操作。

## ADDED Requirements

### Requirement: 统计摘要条

预警管理页面顶部 SHALL 展示预警统计摘要。

#### Scenario: 正常展示
- **WHEN** 教师进入预警管理页面且存在预警记录
- **THEN** 展示四个统计数字：严重（severe 计数，红色）、警告（warning 计数，黄色）、提示（info 计数，蓝色）、总计（灰色），数据来自 `GET /api/v1/warning/stats`

#### Scenario: 无预警
- **WHEN** 不存在任何预警记录
- **THEN** 四个统计数字均为 0

#### Scenario: 班级筛选联动
- **WHEN** 页面 URL 携带 `class_id` 参数
- **THEN** 统计摘要按该班级筛选，筛选工具栏的班级下拉框自动选中对应班级

### Requirement: 预警列表

预警管理页面 SHALL 以表格形式展示预警列表，支持筛选和分页。

#### Scenario: 默认排序
- **WHEN** 预警列表加载且无排序参数
- **THEN** 按严重度降序（severe > warning > info），同严重度按创建时间倒序排列

#### Scenario: 筛选
- **WHEN** 教师选择班级、类型、严重度或状态筛选条件
- **THEN** 列表按所选条件过滤，重新加载数据

#### Scenario: 分页
- **WHEN** 预警总数超过单页条数（默认 20）
- **THEN** 底部分页控件显示页码，教师可切换页面

#### Scenario: 空列表
- **WHEN** 筛选条件下无匹配预警
- **THEN** 表格区显示"暂无预警记录"

### Requirement: 预警详情抽屉

预警管理页面 SHALL 通过右侧滑出抽屉展示预警详情。

#### Scenario: 打开详情
- **WHEN** 教师点击预警列表中的某一行
- **THEN** 从右侧滑入 480px 宽抽屉，展示：学生姓名和班级、预警类型标签、严重度颜色标记、标题、详细描述、数据快照（JSON 格式化）、当前状态、创建时间

#### Scenario: 关闭详情
- **WHEN** 教师点击遮罩层、关闭按钮或按 ESC 键
- **THEN** 抽屉滑出关闭

### Requirement: 预警状态操作

预警详情抽屉 SHALL 提供状态操作按钮。

#### Scenario: 标记已解决
- **WHEN** 教师在 pending 或 processing 状态的预警上点击"标记已解决"
- **THEN** 调用 `PATCH /api/v1/warning/{id}/status`，状态更新为 `resolved`，关闭抽屉，刷新列表

#### Scenario: 标记误报
- **WHEN** 教师在 pending 状态的预警上点击"标记误报"
- **THEN** 调用 `PATCH /api/v1/warning/{id}/status`，状态更新为 `dismissed`，关闭抽屉，刷新列表

#### Scenario: 已关闭预警不可操作
- **WHEN** 预警状态已为 `resolved` 或 `dismissed`
- **THEN** 详情抽屉仅展示信息，不显示状态操作按钮

#### Scenario: 操作失败
- **WHEN** 状态更新 API 返回 422 或其他错误
- **THEN** 显示 Toast 提示错误信息，抽屉保持打开，按钮恢复可用

### Requirement: 手动检测

预警管理页面 SHALL 提供手动触发预警检测功能。

#### Scenario: 手动触发
- **WHEN** 教师点击"手动检测"按钮
- **THEN** 调用 `POST /api/v1/warning/check`，显示 Toast"检测任务已提交"，按钮临时禁用

#### Scenario: 检测运行中
- **WHEN** 前一次手动检测尚未完成（API 返回 429）
- **THEN** 显示 Toast"已有检测任务运行中，请稍后再试"

### Requirement: 页面导航

预警管理页面 SHALL 与后端教师页面保持一致的导航结构。

#### Scenario: 导航入口
- **WHEN** 教师在预警管理页面
- **THEN** 顶部导航栏与学情面板一致，面包屑显示"对话 / 预警中心"，"预警中心"为当前激活项

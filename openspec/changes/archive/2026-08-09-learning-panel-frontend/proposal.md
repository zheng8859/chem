## Why

后端学情面板 API（7 端点）和预警引擎 API（5 端点）已完成实现并通过测试，但前端仅有静态 HTML 原型（`teacher.html`、`students.html`）含硬编码数据，且预警管理页完全缺失。教师无法在真实环境中查看班级学情数据和预警信息。需要构建数据驱动的可视化前端页面，将后端 API 转化为教师可用的交互式仪表盘。

## What Changes

- **重写 `teacher.html`**（班级学情面板）：接入 `/panel/*` API，动态渲染 KPI 卡片、三个图表（知识点错误率柱状图、障碍类型环形图、成绩趋势折线图）、关注学生横条
- **重写 `students.html`**（学生管理）：接入学生列表 API 和 `/panel/class/{id}/student/{sid}` 详情 API，动态渲染学生卡片网格和右侧详情抽屉
- **新建 `warnings.html`**（预警中心）：完整预警管理页面，含统计摘要条、筛选工具栏、预警列表表格、右侧详情抽屉、状态操作按钮
- 纯 CSS + 内联 SVG 图表方案，零外部依赖，复用项目现有 `api-client.js` + `auth.js`
- 删除原型工具栏中后端不支持的"时间范围"下拉框

## Capabilities

### New Capabilities

- `learning-panel-frontend`: 教师端学情面板前端页面——班级聚合视图（4 KPI + 3 图表 + 关注学生横条）、学生详情抽屉、班级选择器，消费 `/panel/*` API
- `warning-frontend`: 教师端预警管理前端页面——预警列表（筛选+分页）、统计摘要、详情抽屉、状态操作（已解决/误报），消费 `/warning/*` API
- `student-management-frontend`: 教师端学生管理前端页面——学生卡片网格（含障碍分布条）、搜索筛选、分页、详情抽屉（障碍画像+趋势图+薄弱知识点），消费 `/panel/class/{id}/student/{sid}` API

### Modified Capabilities

无。本变更仅构建前端消费层，不修改后端 API 规格行为。

## Impact

- Affected code: `chemai-backend/frontend/pages/teacher.html`（重写）、`students.html`（重写）、`warnings.html`（新建）
- 可能影响: `chemai-backend/frontend/js/api-client.js`（如需要新增图表工具函数）
- 依赖: 后端 `panel.py`、`warning.py` API 端点（已实现），`api-client.js`、`auth.js`（已就绪）
- 无新依赖: 纯 Vanilla JS + CSS + SVG，不引入第三方图表库

## Context

后端 `/api/v1/panel/*`（7 端点）和 `/api/v1/warning/*`（5 端点）已完成实现，数据模型和权限校验全部就绪。前端现有两类资产：
- **静态原型**：`teacher.html`（班级学情面板）、`students.html`（学生管理），数据全部硬编码
- **JS 基础设施**：`api-client.js`（fetch 封装 + KaTeX + Toast）、`auth.js`（JWT 管理）

项目前端栈为 Vanilla JS + Vue 3 CDN，所有现有图表使用纯 CSS 或内联 SVG 实现，零外部图表依赖。

## Goals / Non-Goals

**Goals:**
- 将两个静态原型 + 一个全新页面改造为数据驱动的交互式前端
- 复用 `api-client.js` + `auth.js`，零新增外部依赖
- CSS + 内联 SVG 图表方案，与项目现有模式一致
- 所有三页面共享统一的视觉设计系统（颜色/字体/间距复用原型 CSS 变量）

**Non-Goals:**
- 不引入新的 JavaScript 框架或图表库
- 不修改后端 API 规格（`student_info` 补入学时间字段除外）
- 不实现年级基准线对比（等待后端补端点）
- 不实现时间范围筛选（后端不支持学期参数）

## Decisions

### D1: 图表渲染方案 — CSS + 内联 SVG

| 图表 | 方案 | 理由 |
|------|------|------|
| 知识点错误率柱状图 | CSS div 高度 | 柱状图本质是长方形，CSS 足够，和原型一致 |
| 障碍类型环形图 | CSS conic-gradient | `diagnosis.html` 已有成熟实现，直接复用 |
| 成绩趋势折线图 | JS 动态生成 SVG polyline | 数据点数量可变，SVG 天然适配，比 CSS rotate 手工算像素稳健 |

**替代方案**: Chart.js CDN 引入 → 拒绝，与项目零依赖原则冲突。

### D2: 三页面架构

```
pages/
├── teacher.html    → 班级学情面板（重写）
├── students.html   → 学生管理页面（重写）
└── warnings.html   → 预警管理页面（新建）

js/
├── auth.js         → 不变
├── api-client.js   → 可能新增图表工具函数
└── (可能) charts.js → SVG 图表生成工具模块
```

页面间通过导航栏 + URL 参数跳转（`warnings.html?class_id=X`，`students.html?class_id=X&focus=SID`）。

### D3: 数据加载策略

- **teacher.html**: 页面加载时并行请求 3 个端点：
  1. `GET /panel/classes`（获取班级列表）
  2. `GET /panel/class/{class_id}`（班级聚合视图）
  3. `GET /panel/class/{class_id}/exam-trend`（考试趋势，图表三专用）
- **students.html**: 先加载学生列表（分页），点击卡片时请求 `GET /panel/class/{class_id}/student/{student_id}`
- **warnings.html**: 页面加载时请求 `GET /warning/stats` + `GET /warning/list`，点击行时请求 `GET /warning/{id}`

每个模块独立处理加载态/错误态，一个 API 失败不影响其他模块渲染。

### D4: 状态处理策略

| 状态 | 处理方式 |
|------|---------|
| 加载中 | KPI 数字显示"--"占位，图表区显示 CSS spinner |
| 空数据 | 根据 spec 各模块独立判断（0 是有效值，null 是空）|
| API 错误 | 对应模块显示错误文本 + 重试按钮（重新调用同一端点）|
| 网络离线 | 无法触发（教师端 PC 页面，非移动端） |

不做演示模式/静态数据降级（原型已有静态数据，Phase 2 需要时再加）。

### D5: 图表数据映射

**班级聚合视图 → KPI 卡片**:
```
API ClassOverview              前端卡片
─────────────────────────────────────────
exam_count                 →   考试次数
concern_students.length    →   需关注学生（可点击跳预警）
student_count              →   班级人数
avg_score                  →   班级均分（null → "--"）
```

**班级聚合视图 → 柱状图**: `knowledge_points[]` → Top 5 柱（`name` 标签 + `error_rate` 高度）

**班级聚合视图 → 环形图**: `barrier_distribution[]` → 三扇区（concept 紫/reading 蓝/expression 青），占比 `percentage`

**考试趋势 → 折线图**: `exam-trend[]` → X 轴 `exam_name`，Y 轴 `avg_score`；仅 1 个数据点时画点不连线

**关注学生 → 横条**: `concern_students[]` → 每卡片展示 `latest_warning_type`（映射为中文标签+颜色）、`warning_count`、严重度色标

### D6: 预警卡片类型颜色映射

| 预警类型枚举值 | 中文标签 | 标签颜色 |
|---------------|---------|---------|
| `consecutive_absence` | 未登录 | 灰色 |
| `score_drop` | 成绩下滑 | 橙色 |
| `high_error_rate` | 高错误率 | 红色 |
| `new_barrier` | 障碍迁移 | 紫色 |

### D7: 预警严重度颜色映射

| 严重度 | 颜色 |
|--------|------|
| `severe` | 红色 `#ef4444` |
| `warning` | 黄色 `#f59e0b` |
| `info` | 蓝色 `#3b82f6` |

## Risks / Trade-offs

- **CSS 柱状图响应式**: 柱体宽度固定 36px，柱间距靠 flex 自动分配，班级数量变化不控制宽度 → 可接受，面板为 PC 固定 1280px 视口
- **conic-gradient 兼容性**: IE 不支持，目标用户为国内高中教师（Chrome/Edge 为主）→ 低风险
- **SVG polyline 单点场景**: 需要特殊处理（画圆不画线），避免 `points` 属性含单点导致渲染为空
- **关注学生卡片预警类型映射**: 前端需要维护类型标签映射表，后端新增类型时需同步更新 → 低频率（4 类固定），可接受

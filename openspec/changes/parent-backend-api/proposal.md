## Why

家长端是 ChemAI 三端架构中的"低频但高价值触点"——家长月均使用 2-4 次，但需要了解子女学习状态。当前代码基中数据模型（Parent, StudentParentBinding, ParentNotification）和认证（`POST /api/auth/register/parent`）已就绪，但缺少完整的后端 API 服务层：绑定码流程缺失学生端发送环节、无子女数据查询端点、无周报生成能力、无家长 Agent SSE 对话通道。前端 `pages/m/parent.html` 和 `pages/m/parent-login.html` 原型已完成，需后端服务支撑。

## What Changes

- 新建 `app/api/v1/parent.py` 统一家长端路由（前缀 `/api/v1/parent`），承接从 `homework.py` 迁移的绑定/通知路由
- 新建 `app/services/parent_service.py` 子女数据聚合服务 + `app/services/weekly_report_service.py` 周报 LLM 生成服务
- 新建 `app/schemas/parent.py` 请求/响应 Schema
- 新增家长端 Agent SSE 端点，复用现有 v2 ReAct engine + Parent Persona（30号文档已定义工具集）
- 新增 `require_parent_binding()` 权限校验依赖（deps.py）
- `NotificationType` 枚举从 3 种扩充至 5 种（对齐 33号设计文档 §九）
- 新建 `WeeklyReport` 模型（student_id + week_start/end + summary/detail/advice）
- `ParentNotification` 字段对齐：`is_read: bool` → `read_at: datetime`，新增 `related_id`，90 天保留
- 学生端绑码发送端点 `POST /api/v1/parent/bind-code/{student_id}`
- **BREAKING**: 删除 `homework.py` 中的 `POST/GET/DELETE /bindings` 和 `GET/POST /notifications` 路由（零前端调用，迁移至 `parent.py`）
- `homework.py` 瘦身为仅保留 `POST /reports/send-to-students/{exam_id}`

## Capabilities

### New Capabilities

- `parent-bind-code`: 学生端生成/发送 6 位绑码至后端，家长验证绑码完成绑定，支持解绑和查询已绑定子女列表
- `parent-child-query`: 家长查询已绑定子女的学习概览（本周练习量、正确率、连续学习天数、累计练习量）、学习特点（障碍分布通俗解读）、学习动态时间线
- `parent-weekly-report`: 周报 LLM 生成（Prompt 工程设计含术语通俗转换、家庭建议）、DB 缓存去重（同一学生同一周仅生成一份）、手动触发 + Cron 周一 08:00 自动触发
- `parent-notification-api`: 家长通知 CRUD（列表分页、标记已读），5 种通知类型（weekly_report / score_alert / learning_plan / reminder / daily_report），90 天保留
- `parent-agent-chat`: 家长端 AI 助手 SSE 流式对话端点，复用现有 ReAct Agent engine + Parent Persona，预设 5 个提示词（子女知识概览、薄弱点分析、家庭建议、学习状态、预警检查）

### Modified Capabilities

- `data-model`: `NotificationType` 枚举从 3 种扩充至 5 种；新增 `WeeklyReport` 模型；`ParentNotification` 字段调整（read_at 替代 is_read，新增 related_id）
- `auth-system`: 新增学生端绑码发送端点（Student.bind_code 写入通道）
- `rbac-permissions`: 新增家长绑定权限校验依赖 `require_parent_binding()`，所有子女数据查询前置验证绑定关系

## Impact

| 层级 | 文件 | 操作 |
|------|------|------|
| API 路由 | `app/api/v1/parent.py` | 新增 |
| API 路由 | `app/api/v1/homework.py` | 瘦身（删除绑定/通知路由） |
| 服务层 | `app/services/parent_service.py` | 新增 |
| 服务层 | `app/services/weekly_report_service.py` | 新增 |
| Schema | `app/schemas/parent.py` | 新增 |
| Schema | `app/schemas/homework.py` | 修改（新增 WeeklyReportRead） |
| 模型 | `app/models/homework.py` | 修改（新增 WeeklyReport，调整 ParentNotification） |
| 枚举 | `app/core/enums.py` | 修改（NotificationType 扩充） |
| 权限 | `app/api/deps.py` | 修改（新增 require_parent_binding） |
| Agent | `app/api/v1/parent.py` 内 SSE 端点 | 新增 |
| 调度器 | `app/infrastructure/scheduler.py` | 修改（追加周报 Cron） |
| 路由注册 | `app/main.py` | 修改（include parent_router） |
| 说明文档 | `app/models/homework.py` 注释 | 修改 |

## 1. 枚举与数据模型

- [x] 1.1 扩充 `NotificationType` 枚举：新增 `weekly_report`、`score_alert`、`learning_plan`、`reminder`、`daily_report` 五个值，保留现有 `learning_report`、`warning_alert`、`teacher_message`（`app/core/enums.py`）
- [x] 1.2 新建 `WeeklyReport` 模型：字段 `id`、`student_id` (FK)、`week_start` (date)、`week_end` (date)、`summary` (String 200)、`detail` (Text)、`advice` (Text)、`no_data` (Boolean)、`generated_at` (DateTime)、`generated_by` (String 20)，唯一约束 `(student_id, week_start)`（`app/models/homework.py`）
- [x] 1.3 调整 `ParentNotification` 模型：`is_read: bool` → `read_at: DateTime | None`，新增 `related_id: int | None`，`sent_at` 保留（`app/models/homework.py`）
- [x] 1.4 创建 Alembic 迁移脚本：`ParentNotification` 字段变更（is_read → read_at 数据迁移）+ `WeeklyReport` 新表（`alembic revision --autogenerate`）
- [x] 1.5 更新模型 `__init__.py` 导出 `WeeklyReport`（`app/models/__init__.py`）

## 2. Schema 层

- [x] 2.1 新建 `app/schemas/parent.py`：定义 `BindCodeRequest`、`BindRequest`、`ChildOverviewResponse`、`ChildTimelineResponse`、`WeeklyReportResponse`、`WeeklyReportGenerateRequest`、`ParentNotificationResponse`、`ParentAgentRequest`
- [x] 2.2 修改 `app/schemas/homework.py`：更新 `ParentNotificationRead`（`is_read` → `read_at`，新增 `related_id`），新增 `WeeklyReportRead`

## 3. 权限校验层

- [x] 3.1 新增 `require_parent_binding()` 依赖工厂

## 4. Service 层

- [x] 4.1 新建 `app/services/parent_service.py` — `ParentService` 类：
  - `get_child_overview(db, student_id)` — 聚合本周练习数、正确率、连续学习天数、累计练习量
  - `get_child_timeline(db, student_id, weeks=4)` — 近 4 周每周练习统计
  - `get_child_characteristics(db, student_id)` — 从 Student.barrier_profile 生成通俗语言描述
  - `list_bound_children(db, parent_id)` — 查询已绑定子女列表
  - `create_binding(db, data)` — 从 HomeworkService 迁移
  - `delete_binding(db, binding_id)` — 从 HomeworkService 迁移
  - `get_parent_notifications(db, parent_id, limit, offset)` — 从 HomeworkService 迁移，90 天过滤
  - `mark_notification_read(db, notification_id)` — 从 HomeworkService 迁移
- [x] 4.2 新建 `app/services/weekly_report_service.py` — `WeeklyReportService` 类：
  - `generate_report(db, student_id, generated_by)` — 聚合数据 → 构造 system + user prompt → LLM → 解析 JSON → 存储 WeeklyReport → 返回
  - `get_report(db, student_id, week_start)` — 查询缓存
  - `generate_and_notify(db, student_id)` — 生成报告 + 创建 ParentNotification
  - `run_weekly_cron(db)` — Cron 入口：查所有有活跃绑定的学生 → 逐个生成周报 → 通知家长
- [x] 4.3 迁移 `HomeworkService` 中绑定/通知方法至 `ParentService`，原方法标记 deprecated 并委托给 ParentService（渐进式迁移）

## 5. API 路由层

- [x] 5.1 新建 `app/api/v1/parent.py`，挂载 `APIRouter(prefix="/parent", tags=["parent"])`：
  - `POST /bind-code/{student_id}` — 学生发送绑码（require_student_self）
  - `POST /bind` — 家长提交绑定
  - `GET /children` — 已绑定子女列表
  - `DELETE /bind/{binding_id}` — 解绑
  - `GET /child/{student_id}/report` — 子女报告（require_parent_binding）
  - `GET /child/{student_id}/timeline` — 子女学习时间线（require_parent_binding）
  - `GET /child/{student_id}/weekly` — 获取当周周报（require_parent_binding）
  - `POST /child/{student_id}/weekly/generate` — 手动生成周报（require_parent_binding）
  - `GET /notifications` — 家长通知列表
  - `PUT /notifications/{notification_id}/read` — 标记已读
- [x] 5.2 从 `app/api/v1/homework.py` 删除已被迁移的路由：`POST /bindings`、`GET /bindings`、`DELETE /bindings/{id}`、`GET /notifications`、`POST /notifications/{id}/read`，仅保留 `POST /reports/send-to-students/{exam_id}`
- [x] 5.3 在 `app/main.py` 中 `include_router(parent_router)`

## 6. Agent 集成

- [x] 6.1 在 `app/api/v1/parent.py` 新增 `POST /agent/chat` SSE 端点：组装 Parent persona Agent（复用现有 engine 工厂），注入 `{student_context}`，流式返回 SSE 事件
- [x] 6.2 新增 `GET /agent/conversations`、`GET /agent/history/{thread_id}`、`POST /agent/new`、`DELETE /agent/conversations/{thread_id}` 对话管理端点（过滤前缀 "p-"）

## 7. 调度器

- [x] 7.1 在 `app/infrastructure/scheduler.py` 新增 `_run_weekly_report()` Cron job：周一 08:00 (Asia/Shanghai) 调用 `WeeklyReportService.run_weekly_cron()`
- [x] 7.2 更新 `register_jobs()` 注册新 job

## 8. 测试

- [x] 8.1 新建 `tests/unit/test_parent_service.py`：ParentService 纯函数单元测试
- [x] 8.2 新建 `tests/unit/test_weekly_report_service.py`：WeeklyReportService mock LLM 单元测试
- [x] 8.3 新建 `tests/integration/test_parent_api.py`：完整 API 集成测试（绑码流程、绑定/解绑、子女数据查询、周报生成、通知 CRUD）
- [x] 8.4 更新 `tests/integration/test_homework_api.py`：删除旧路由测试，迁移到 `test_parent_api.py`
- [x] 8.5 更新 `tests/unit/test_schemas_homework.py`：适配 `ParentNotification` 字段变更

## 9. 清理与验证

- [x] 9.1 运行全量测试：`pytest tests/unit tests/integration -v` 确保无回归
- [x] 9.2 运行 `openspec validate --change parent-backend-api` 确保规格完整性
- [x] 9.3 更新 `chemai-backend/CONTEXT.md` 领域词汇表（如有新术语）

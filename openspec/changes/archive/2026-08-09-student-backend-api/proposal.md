## Why

学生端前端页面（练习、错题、复习中心、AI助教、我的）已完成 UI 原型，但"我的"页面的数据全部为静态硬编码，且 Agent 对话缺少学生个性化上下文。教师端已具备诊断、统计、学情面板等完整后端能力，学生端对应的数据自查看能力缺失。本期补齐学生端后端 API，使"我的"页面数据化、Agent 对话个性化、学习计划可管理、消息通知可触达。

## What Changes

### 新增 API 端点（10 个）

- **练习统计聚合**：`GET /api/v1/student/{id}/stats` — 累计练习次数、加权正确率、连续打卡天数、错题存量、今日待复习数
- **学生自查看诊断**：`GET /api/v1/diagnosis/student/{student_id}` — 障碍画像、主导障碍类型、Top 5 薄弱知识点
- **学习计划 CRUD**：`GET/POST/PUT /api/v1/learning-plan/*` + `PATCH .../tasks/{id}/complete` — 教师创建/更新，学生只读+标记完成
- **消息通知**：`GET /api/v1/notifications/student/{student_id}` + `POST .../{id}/read` — 自动通知（教师操作触发），学生拉取
- **Agent 工具补全**：注册 `periodic_law_tutor` + `organic_tutor` 两个辅导工具
- **Agent 学生上下文**：诊断完成时写入 LangGraph Store，学生对话时自动注入障碍画像 + 学习计划 + 练习统计到 System Message

### 修改现有端点

- `POST /api/v1/practice/assign` — 布置练习后自动写入通知
- `POST /api/v1/learning-plan` — 创建计划后自动写入通知
- `POST /api/v1/diagnosis/run-llm` — LLM 诊断完成后写入诊断历史到 Store

### 新增基础设施

- **2 个数据表**：`LearningPlan` + `LearningPlanTask`、`Notification`
- **2 个 Service**：`LearningPlanService`、`NotificationService`
- **1 个权限依赖**：`require_student_self` — 统一校验学生只能访问自身数据

## Capabilities

### New Capabilities

- `student-stats-api`: 学生练习统计聚合端点，为"我的"页三指标卡片提供累计练习次数、加权正确率、连续打卡天数、错题存量、待复习数
- `student-diagnosis-self-api`: 学生自查看障碍诊断端点，返回个体障碍画像、主导障碍类型和 Top 5 薄弱知识点
- `learning-plan-api`: 学生学习计划 CRUD 端点，教师通过 Agent 创建/更新，学生只读+标记任务完成，一个学生同时只有一份活跃计划
- `student-notification-api`: 学生消息通知系统，教师操作（布置练习、发送计划）时自动触发通知写入，学生拉取列表
- `agent-student-memory`: Agent 学生记忆与上下文注入，LLM 诊断完成后写入 Store，学生对话时自动注入障碍画像 + 学习计划 + 统计到 System Message
- `agent-chem-tutors`: 注册 `periodic_law_tutor`（周期律辅导）和 `organic_tutor`（有机推断辅导）两个苏格拉底式化学辅导工具

### Modified Capabilities

- `practice-review-api`: 教师布置练习（`POST /practice/assign`）时自动触发通知写入
- `diagnosis-engine`: LLM 诊断完成后写入诊断历史到 LangGraph Store

## Impact

- **新增文件**：`app/api/v1/stats.py`、`app/services/learning_plan_service.py`、`app/services/notification_service.py`、`app/models/learning_plan.py`、`app/models/notification.py`、学习计划 Schemas、通知 Schemas、Agent 工具注册配置
- **修改文件**：`app/main.py`（注册新路由）、`app/api/deps.py`（新增 require_student_self）、`app/services/adaptive_practice_service.py`（通知钩子）、`app/services/diagnosis_service.py`（Store 写入钩子）、Agent 工厂函数（Student persona System Message 注入）、`agent/tools/`（工具元数据注册）
- **数据库**：2 个新表（`learning_plans`、`learning_plan_tasks`、`notifications`），Alembic 迁移
- **依赖**：无新增外部依赖

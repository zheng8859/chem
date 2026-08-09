## 1. 基础设施：数据模型与权限

- [ ] 1.1 创建 `app/models/learning_plan.py` — LearningPlan + LearningPlanTask 两个 SQLAlchemy 模型
- [ ] 1.2 创建 `app/models/notification.py` — Notification SQLAlchemy 模型
- [ ] 1.3 在 `app/models/__init__.py` 中注册新模型
- [ ] 1.4 生成 Alembic 迁移脚本并执行 `alembic upgrade head`
- [ ] 1.5 在 `app/api/deps.py` 中新增 `require_student_self` 依赖函数

## 2. 学生练习统计 API (A 组)

- [ ] 2.1 创建 `app/services/stats_service.py` — 实现统计聚合查询（累计练习数、加权正确率、连续打卡天数、错题存量、待复习数）
- [ ] 2.2 创建 `app/schemas/stats.py` — StudentStatsResponse Pydantic 模型
- [ ] 2.3 创建 `app/api/v1/stats.py` — GET /api/v1/student/{id}/stats 端点，使用 require_student_self

## 3. 学生自查看诊断 API (B 组)

- [ ] 3.1 在 `app/services/diagnosis_service.py` 中新增 `get_student_diagnosis` 方法 — 返回障碍画像、主导类型、Top 5 薄弱知识点、趋势计算
- [ ] 3.2 创建 `app/schemas/diagnosis.py` 的 StudentDiagnosisResponse（如不存在）
- [ ] 3.3 在 `app/api/v1/diagnosis.py` 中新增 GET /api/v1/diagnosis/student/{student_id} 端点

## 4. 学习计划 API (C 组)

- [ ] 4.1 创建 `app/schemas/learning_plan.py` — LearningPlanCreate、LearningPlanUpdate、LearningPlanResponse 等 Pydantic 模型
- [ ] 4.2 创建 `app/services/learning_plan_service.py` — 创建计划（自动归档旧计划）、更新计划、获取活跃计划、标记任务完成
- [ ] 4.3 创建 `app/api/v1/learning_plan.py` — 4 个端点：GET/POST/PUT/PATCH，区分教师/学生权限

## 5. 消息通知 API (D 组)

- [ ] 5.1 创建 `app/schemas/notification.py` — NotificationResponse Pydantic 模型
- [ ] 5.2 创建 `app/services/notification_service.py` — 创建通知（类型枚举：practice_assigned, plan_updated）、获取学生通知列表（分页，30天过滤）、标记已读
- [ ] 5.3 创建 `app/api/v1/notification.py` — 2 个端点：GET /notifications/student/{student_id}、POST /notifications/{id}/read
- [ ] 5.4 在 `app/services/adaptive_practice_service.py` 的 `create_practice` 方法中增加通知写入钩子（best-effort）
- [ ] 5.5 在 `app/services/learning_plan_service.py` 的创建/更新方法中增加通知写入钩子（best-effort）

## 6. Agent 工具注册 (E1 组)

- [ ] 6.1 在 `agent/tools/` 中为 `periodic_law_tutor` 注册工具元数据（persona=["student"], call_limit=5）
- [ ] 6.2 在 `agent/tools/` 中为 `organic_tutor` 注册工具元数据（persona=["student"], call_limit=5）
- [ ] 6.3 在 Student persona YAML 的 `available_skills` 中添加 `periodic_law_tutor` 和 `organic_tutor`

## 7. Agent Store 写入 (E2 组)

- [ ] 7.1 在 `app/services/diagnosis_service.py` 的 LLM 诊断完成后增加 LangGraph Store 写入（best-effort，写入障碍画像 + 时间戳）
- [ ] 7.2 在 `app/services/learning_plan_service.py` 的创建/更新方法中增加 Store 写入（best-effort，写入计划摘要）
- [ ] 7.3 更新 `app/agent/tools/memory_student_get` 工具实现，从 Store 读取诊断历史（最近5条）和学习计划

## 8. Agent 学生上下文注入 (E3 组)

- [ ] 8.1 在 Agent 工厂函数中，当 persona="student" 时，从数据库查询学生障碍画像、学习计划、练习统计
- [ ] 8.2 将查询结果格式化为结构化 System Message 块，注入到 Agent 的 system prompt 前面
- [ ] 8.3 确保非 student persona（teacher/tutor/parent）不受影响

## 9. 路由注册与集成

- [ ] 9.1 在 `app/main.py` 中注册新的 API 路由（stats、learning_plan、notification）
- [ ] 9.2 验证新端点出现在 FastAPI Swagger `/docs` 中

## 10. 测试

- [ ] 10.1 学生统计 API 单元测试 + 集成测试（正常数据、空数据、跨学生访问被拒）
- [ ] 10.2 学生诊断 API 集成测试（有诊断数据、无诊断数据、趋势计算正确性）
- [ ] 10.3 学习计划 API 集成测试（创建/更新/获取/标记完成、旧计划自动归档、跨学生访问被拒）
- [ ] 10.4 通知 API 集成测试（列表分页、标记已读、30天过滤）
- [ ] 10.5 通知自动触发测试（布置练习→通知写入、创建计划→通知写入）
- [ ] 10.6 Agent 工具注册验证（工厂函数为 Student persona 构建工具集时包含新工具）
- [ ] 10.7 Agent Store 写入测试（诊断完成后 Store 有数据、计划创建后 Store 有数据）
- [ ] 10.8 Agent System Message 注入测试（Student persona 包含学生档案、非 Student persona 不包含）
- [ ] 10.9 运行全量回归测试，确保存量测试全部通过

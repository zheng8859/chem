## 1. 数据模型与迁移

- [x] 1.1 新增 `BarrierProfileHistory` 模型（student_id, snapshot_at, profile JSON, dominant_barrier），写入 `app/models/barrier_profile_history.py`
- [x] 1.2 丰富 `WarningLog` 模型（title, data JSON, status 默认 pending, processed_by FK, processed_at, note），更新 `app/models/diagnosis.py`
- [x] 1.3 生成 Alembic 迁移脚本并执行 `alembic upgrade head`
- [x] 1.4 创建 `app/schemas/panel.py` — Panel API 全部请求/响应 Pydantic 模型
- [x] 1.5 创建 `app/schemas/warning.py` — Warning API 全部请求/响应 Pydantic 模型

## 2. PanelService 聚合计算

- [x] 2.1 创建 `app/services/panel_service.py`，实现 `get_teacher_classes(teacher_id)` 方法
- [x] 2.2 实现 `get_class_overview(class_id)` — 加权均分 + 知识点 Top 5 + 障碍分布 + 进步/退步 Top 3 + 关注学生 + 考试次数
- [x] 2.3 实现 `get_student_detail(class_id, student_id)` — 正确率趋势 + 薄弱知识点（含 trend）+ 障碍画像历史
- [x] 2.4 实现 `get_knowledge_points(class_id, limit, offset)` — 全量知识点错误率排行分页
- [x] 2.5 实现 `get_barriers(class_id)` — 障碍类型分布统计
- [x] 2.6 实现 `get_concern_students(class_id)` — 预警未处理学生列表
- [x] 2.7 实现 `get_exam_trend(class_id)` — 班级历次考试均分序列
- [x] 2.8 实现内部 helper：`_weighted_avg()`（指数衰减）、`_error_rate()`、`_barrier_distribution()`、`_top_improvers_declining()`

## 3. EarlyWarningService 预警引擎

- [x] 3.1 创建 `app/services/early_warning_service.py`，定义 `WarningResult` dataclass
- [x] 3.2 实现 `check_consecutive_absence(student_id)` — 连续未登录 ≥ 3 天
- [x] 3.3 实现 `check_score_drop(student_id)` — 最近两次考试正确率降幅 ≥ 10%
- [x] 3.4 实现 `check_high_error_rate(student_id)` — 知识点错误率 ≥ 50%（warning）/ ≥ 70%（severe）
- [x] 3.5 实现 `check_new_barrier(student_id)` — 主导障碍归一化得分变化 ≥ 30%
- [x] 3.6 实现 `run_all_checks()` orchestrator — 遍历活跃学生、去重、批量写入 WarningLog + 更新 BarrierProfileHistory
- [x] 3.7 实现 `run_async_check()` — 异步后台任务包装器（供手动触发使用）

## 4. Panel API 路由

- [x] 4.1 创建 `app/api/v1/panel.py`，注册 router（prefix="/panel", tags=["panel"]）
- [x] 4.2 实现 `GET /panel/classes` — 教师 Dashboard 班级列表
- [x] 4.3 实现 `GET /panel/class/{class_id}` — 班级聚合视图
- [x] 4.4 实现 `GET /panel/class/{class_id}/student/{student_id}` — 学生详情
- [x] 4.5 实现 `GET /panel/class/{class_id}/knowledge-points` — 知识点维度展开
- [x] 4.6 实现 `GET /panel/class/{class_id}/barriers` — 障碍类型维度展开
- [x] 4.7 实现 `GET /panel/class/{class_id}/concern-students` — 重点关注学生
- [x] 4.8 实现 `GET /panel/class/{class_id}/exam-trend` — 考试趋势
- [x] 4.9 教师权限校验（仅 teacher 角色 + 仅本人所教班级）

## 5. Warning API 路由

- [x] 5.1 创建 `app/api/v1/warning.py`，注册 router（prefix="/warning", tags=["warning"]）
- [x] 5.2 实现 `GET /warning/list` — 预警列表（按班级/严重度/类型/状态筛选 + 分页）
- [x] 5.3 实现 `GET /warning/{id}` — 预警详情（含 JSON 数据快照）
- [x] 5.4 实现 `PATCH /warning/{id}/status` — 更新预警状态（pending → processing / resolved / dismissed，含状态机校验）
- [x] 5.5 实现 `GET /warning/stats` — 预警统计摘要（by_type + by_severity + total）
- [x] 5.6 实现 `POST /warning/check` — 手动触发检测（异步后台任务 + 429 防重）
- [x] 5.7 教师权限校验（仅 teacher 角色访问）

## 6. 调度器集成

- [x] 6.1 在 `app/infrastructure/scheduler.py` 新增 `warning_check` cron job（每天 00:00 Asia/Shanghai）
- [x] 6.2 实现 `warning_check_job()` — 调用 `EarlyWarningService.run_all_checks()`，带错误日志和异常隔离

## 7. 路由注册

- [x] 7.1 在 `app/main.py` 注册 panel_router 和 warning_router
- [x] 7.2 验证 Swagger docs（`/docs`）可看到新增端点

## 8. 测试

- [x] 8.1 PanelService 单元测试：加权均分计算、错误率公式、障碍分布、进步/退步 Top 3
- [x] 8.2 EarlyWarningService 单元测试：四类规则各自的正例/负例/边界场景
- [x] 8.3 Panel API 集成测试：12 个端点（7 panel + 5 warning）的 200/403/404/422 响应
- [x] 8.4 预警状态机测试：合法转换（pending→processing→resolved, pending→dismissed）+ 非法转换（resolved→pending）返回 422
- [x] 8.5 调度器测试：cron 注册正确、job 函数异常隔离不中断其他 job
- [x] 8.6 运行全量回归测试（pytest）确保存量 1178 测试保持通过

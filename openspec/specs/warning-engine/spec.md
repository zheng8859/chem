## Purpose

通过四类自动检测规则及时发现学生异常状态，生成分级预警并追踪完整处理生命周期，支持定时自动检测和手动触发。

## ADDED Requirements

### Requirement: 连续未登录检测

系统 SHALL 在预警检测时检查 `Student.last_practice_time`，若距今 ≥ 3 天则生成 `consecutive_absence` 类型预警，严重度为 `info`。

#### Scenario: 检测到连续未登录
- **WHEN** 预警检测执行且某学生 `last_practice_time` 距今 ≥ 3 天
- **THEN** 生成一条 `consecutive_absence` + `info` 预警记录

#### Scenario: 重复检测不重复生成
- **WHEN** 某学生已存在一条未处理的 `consecutive_absence` 预警
- **THEN** 下次检测不重复生成同类型预警

#### Scenario: 恢复后不再预警
- **WHEN** 学生恢复练习且 `last_practice_time` 距今 < 3 天
- **THEN** 不生成新的 `consecutive_absence` 预警

### Requirement: 成绩下滑检测

系统 SHALL 在学生有至少两次考试记录时，比较最近两次考试的个人正确率，若降幅 ≥ 10% 则生成 `score_drop` 类型预警，严重度为 `warning`。

#### Scenario: 检测到成绩下滑
- **WHEN** 最近一次考试个人正确率 < 前一次考试个人正确率，且降幅 ≥ 10%
- **THEN** 生成 `score_drop` + `warning` 预警，`data` 字段包含两次考试的正确率和考试 ID

#### Scenario: 仅一次考试不检测
- **WHEN** 学生仅有 1 次考试记录
- **THEN** 不生成 `score_drop` 预警

#### Scenario: 成绩上升不预警
- **WHEN** 最近考试正确率 ≥ 前一次考试正确率
- **THEN** 不生成 `score_drop` 预警

#### Scenario: 降幅不足阈值
- **WHEN** 最近考试正确率下降但降幅 < 10%
- **THEN** 不生成 `score_drop` 预警

### Requirement: 高错误率检测

系统 SHALL 在预警检测时计算各知识点的错误率 `E(kp) = errors(kp) / total(kp)`，对错误率 ≥ 50% 的知识点生成 `high_error_rate` 预警。

#### Scenario: 错误率 ≥ 70% 为严重
- **WHEN** 某知识点错误率 ≥ 70%
- **THEN** 生成 `high_error_rate` + `severe` 预警

#### Scenario: 错误率 50%-70% 为警告
- **WHEN** 某知识点错误率在 [50%, 70%) 区间
- **THEN** 生成 `high_error_rate` + `warning` 预警

#### Scenario: 错误率 < 50% 不预警
- **WHEN** 所有知识点错误率均 < 50%
- **THEN** 不生成 `high_error_rate` 预警

#### Scenario: 同一知识点不重复预警
- **WHEN** 某学生的某知识点已存在未处理的 `high_error_rate` 预警
- **THEN** 不重复生成同知识点同类型预警

### Requirement: 新障碍出现检测

系统 SHALL 对比当前障碍画像与 `BarrierProfileHistory` 中最近一次快照，若主导障碍类型归一化得分变化 ≥ 30%，生成 `new_barrier` 类型预警，严重度为 `severe`。

#### Scenario: 主导障碍转移
- **WHEN** `S_normalized = S_raw / max(S_raw_barriers_in_class)`，且当前主导障碍类型的归一化得分变化 ≥ 30%
- **THEN** 生成 `new_barrier` + `severe` 预警，`data` 字段包含变化前后的障碍分布

#### Scenario: 无历史快照不检测
- **WHEN** 学生在 `BarrierProfileHistory` 中无历史记录
- **THEN** 跳过 `new_barrier` 检测，同时将当前障碍画像写入历史快照作为基线

#### Scenario: 障碍变化但未达阈值
- **WHEN** 主导障碍归一化得分变化 < 30%
- **THEN** 不生成预警，但更新 `BarrierProfileHistory` 快照

### Requirement: 预警列表与筛选

教师端 SHALL 通过 `GET /api/v1/warning/list` 获取预警列表，支持按班级、严重度、类型、状态筛选。

#### Scenario: 分页筛选
- **WHEN** 请求含 `class_id`、`severity`、`type`、`status`、`limit`、`offset` 等查询参数
- **THEN** 返回 `{data: [...], total, limit, offset}，每项含 `id`、`student_id`、`student_name`、`class_name`、`type`、`severity`、`title`、`status`、`created_at`

#### Scenario: 默认排序
- **WHEN** 无排序参数
- **THEN** 按严重度降序（severe > warning > info），同严重度按创建时间倒序

### Requirement: 预警详情

系统 SHALL 通过 `GET /api/v1/warning/{id}` 返回预警完整信息，含 JSON 数据快照。

#### Scenario: 查看详情
- **WHEN** 教师请求预警详情
- **THEN** 返回完整预警记录，含 `data` 字段（JSON 快照，内容因预警类型而异）、`processed_by`、`processed_at`、`note`

### Requirement: 预警状态管理

教师 SHALL 通过 `PATCH /api/v1/warning/{id}/status` 更新预警状态，状态机遵循 `pending → processing → resolved` 或 `pending → dismissed`。

#### Scenario: 标记处理中
- **WHEN** 教师将预警状态改为 `processing`
- **THEN** 状态更新为 `processing`，不设置 `processed_by` 和 `processed_at`

#### Scenario: 标记已解决
- **WHEN** 教师将预警状态改为 `resolved`
- **THEN** 状态更新为 `resolved`，自动设置 `processed_by`（当前教师 ID）和 `processed_at`（当前时间）

#### Scenario: 标记误报
- **WHEN** 教师将预警状态改为 `dismissed`
- **THEN** 状态更新为 `dismissed`，自动设置 `processed_by` 和 `processed_at`

#### Scenario: 非法状态转换
- **WHEN** 尝试将 `resolved` 或 `dismissed` 状态的预警改为 `pending`
- **THEN** 返回 422

### Requirement: 预警统计摘要

系统 SHALL 通过 `GET /api/v1/warning/stats` 返回预警统计摘要，按类型和按严重度分别计数。

#### Scenario: 统计摘要
- **WHEN** 教师请求预警统计（可选 `class_id` 筛选）
- **THEN** 返回 `by_type`（`{consecutive_absence, score_drop, high_error_rate, new_barrier}` 各计数）、`by_severity`（`{info, warning, severe}` 各计数）、`total`

### Requirement: 手动触发检测

教师 SHALL 可通过 `POST /api/v1/warning/check` 手动触发预警检测，系统异步执行并返回 task_id。

#### Scenario: 手动触发成功
- **WHEN** 教师调用手动触发端点
- **THEN** 返回 `{task_id, status: "scheduled"}`，检测在后台异步执行

#### Scenario: 已有检测任务运行中
- **WHEN** 前一次手动检测尚未完成
- **THEN** 返回 429

### Requirement: 定时自动检测

系统 SHALL 通过 APScheduler 每天 00:00（Asia/Shanghai）自动执行全量预警检测。

#### Scenario: 定时执行
- **WHEN** 每天 00:00 到达
- **THEN** 遍历所有活跃学生，依次运行四类检测规则，新预警写入 `WarningLog`

#### Scenario: 检测容错
- **WHEN** 某学生的某条检测规则执行异常
- **THEN** 记录错误日志，继续处理下一个学生/下一条规则，不中断整体检测流程

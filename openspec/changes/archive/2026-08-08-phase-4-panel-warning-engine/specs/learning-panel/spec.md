## Purpose

为教师提供班级维度的学情聚合视图，支持从班级概览下钻到学生详情，通过知识点×学生×时间三维分析模型呈现学情数据。

## ADDED Requirements

### Requirement: 教师 Dashboard 班级列表

教师端首页 SHALL 展示所教班级列表，每班一行简要指标。

#### Scenario: 加载班级列表
- **WHEN** 教师请求 `GET /api/v1/panel/classes`
- **THEN** 返回班级数组，每项含 `class_id`、`class_name`、`student_count`、`recent_avg_score`（最近一次考试班级均分）、`concern_count`（预警未处理学生数）、`last_exam_date`

#### Scenario: 无考试记录
- **WHEN** 某班级尚无任何考试记录
- **THEN** `recent_avg_score` 为 `null`，`last_exam_date` 为 `null`

### Requirement: 班级聚合视图

班级聚合视图 SHALL 通过 `GET /api/v1/panel/class/{class_id}` 返回班级学情快照，所有数据按需实时聚合。

#### Scenario: 完整班级快照
- **WHEN** 教师请求班级聚合视图
- **THEN** 返回 JSON 包含：`avg_score`（加权指数衰减均分）、`knowledge_points`（错误率 Top 5，每项 `{name, error_rate}`）、`barrier_distribution`（`[{barrier_type, count, percentage}]`）、`top_improvers`（最近两次考试个人正确率提升 Top 3）、`top_declining`（退步 Top 3）、`concern_students`（预警未处理学生列表）、`exam_count`

#### Scenario: 班级均分加权衰减
- **WHEN** 班级有多次考试记录
- **THEN** `avg_score` 采用公式 `w_i = exp(-λ × (t_now - t_i) / T_week)`（λ = ln(2) ≈ 0.693）计算加权平均，近期考试权重高

#### Scenario: 班级无数据
- **WHEN** 班级无任何考试或练习记录
- **THEN** `avg_score` 为 `null`，`knowledge_points` 为空数组，`barrier_distribution` 为空数组，`top_improvers` 和 `top_declining` 为空数组

### Requirement: 学生详情

学生详情 SHALL 通过 `GET /api/v1/panel/class/{class_id}/student/{student_id}` 返回个人学情，含正确率趋势、薄弱知识点和障碍画像变化历史。

#### Scenario: 完整学生详情
- **WHEN** 教师请求学生详情
- **THEN** 返回 `student_info`（姓名、班级）、`accuracy_trend`（历次考试/练习正确率序列，含日期和类型标签）、`weak_knowledge_points`（薄弱知识点列表，每项 `{name, error_rate, trend}`，trend 为 `"up"` / `"down"` / `"stable"`）、`barrier_profile_history`（障碍画像历史快照列表，按时间倒序）

#### Scenario: 学生不存在
- **WHEN** student_id 不属于该 class_id
- **THEN** 返回 404

### Requirement: 知识点维度展开

知识点维度 SHALL 通过 `GET /api/v1/panel/class/{class_id}/knowledge-points` 返回全量知识点错误率排行，支持分页。

#### Scenario: 知识点排行分页
- **WHEN** 请求含 `limit` 和 `offset` 参数
- **THEN** 返回 `{data: [{name, error_rate}], total, limit, offset}`，按错误率降序排列

#### Scenario: 错误率计算
- **WHEN** 聚合计���知识点错误率
- **THEN** 使用公式 `E(kp, c) = errors(kp, c) / total(kp, c)`，数据来源包含 `ExamRecord` 和 `PracticeSession`

### Requirement: 障碍类型维度展开

障碍类型维度 SHALL 通过 `GET /api/v1/panel/class/{class_id}/barriers` 返回全班障碍类型分布。

#### Scenario: 障碍分布统计
- **WHEN** 教师请求障碍分布
- **THEN** 返回 `[{barrier_type, count, percentage}]`，percentage = count / 班级总人数 × 100

### Requirement: 重点关注学生列表

重点关注学生列表 SHALL 通过 `GET /api/v1/panel/class/{class_id}/concern-students` 返回预警未处理的学生。

#### Scenario: 关注学生列表
- **WHEN** 教师请求关注学生列表
- **THEN** 返回学生数组，每项含 `student_id`、`name`、`warning_count`（未处理预警数）、`latest_warning_type`、`latest_warning_severity`、`last_practice_time`

#### Scenario: 无关注学生
- **WHEN** 班级无未处理预警
- **THEN** 返回空数组

### Requirement: 考试趋势

考试趋势 SHALL 通过 `GET /api/v1/panel/class/{class_id}/exam-trend` 返回班级历次考试均分序列。

#### Scenario: 考试趋势数据
- **WHEN** 教师请求考试趋势
- **THEN** 返回 `[{exam_id, exam_name, exam_date, avg_score, participant_count}]`，按考试日期升序排列

#### Scenario: 无考试记录
- **WHEN** 班级无考试记录
- **THEN** 返回空数组

### Requirement: 权限控制

面板所有端点 SHALL 仅允许教师角色访问，且仅返回该教师所教班级的数据。

#### Scenario: 学生角色访问被拒
- **WHEN** 学生 token 请求面板端点
- **THEN** 返回 403

#### Scenario: 教师跨班访问被拒
- **WHEN** 教师请求非本人所教班级的面板数据
- **THEN** 返回 403

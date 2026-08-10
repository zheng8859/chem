## ADDED Requirements

### Requirement: 考试删除安全策略

`DELETE /exams/{id}` SHALL 校验考试状态。`in_progress` 和 `grading` 状态的考试 SHALL 禁止删除，返回 403 Forbidden。`pending` 和 `completed` 状态的考试 SHALL 允许删除。

#### Scenario: 删除进行中的考试被拒绝
- **WHEN** 教师尝试删除 status=`in_progress` 的考试
- **THEN** 返回 403，detail 包含"进行中的考试不可删除"

#### Scenario: 删除草稿考试成功
- **WHEN** 教师删除 status=`pending` 的考试
- **THEN** 考试记录、题目关联、答题记录被级联删除，返回 204

#### Scenario: 删除已完成考试成功
- **WHEN** 教师删除 status=`completed` 的考试
- **THEN** 考试记录被删除，返回 204

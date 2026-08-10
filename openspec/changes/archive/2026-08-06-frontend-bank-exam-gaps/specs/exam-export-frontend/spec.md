## Purpose

考试 Word 导出前端入口 — 考试卡片上的导出按钮，触发浏览器下载 .docx 文件。

## ADDED Requirements

### Requirement: 考试卡片导出按钮

Tab 4 考试列表中的每张考试卡片 SHALL 提供"导出"按钮。点击后 SHALL 调用 `GET /api/v1/exams/{id}/export?format=docx&with_answers=false` 并触发浏览器文件下载。

#### Scenario: 导出学生版试卷
- **WHEN** 教师点击考试卡片上的"导出"按钮
- **THEN** 浏览器下载学生版 .docx 文件，文件名为 `试卷{id}_学生版.docx`

### Requirement: 导出按钮按状态显示

导出按钮 SHALL 对 `completed` 状态的考试始终可见。`pending` 和 `in_progress` 状态 SHALL 不显示导出按钮（考试尚未完成，无导出意义）。

#### Scenario: 已完成考试显示导出按钮
- **WHEN** 考试 status=`completed`
- **THEN** 导出按钮可见

#### Scenario: 草稿考试不显示导出按钮
- **WHEN** 考试 status=`pending`
- **THEN** 导出按钮不可见

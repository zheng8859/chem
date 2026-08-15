## Purpose

定义 OCR 批改工具组（30 号文档 §3.5、24 号文档 §8 的 3 个工具）的行为契约：教师通过 Agent 对话完成「进度查询 → 批量批改 → 确认保存」三阶段流程，将 OCR 管道状态机封装为对话式操作。

## Requirements

### Requirement: query_ocr_progress 进度查询

系统 SHALL 提供 `query_ocr_progress` 工具，接受 `teacher_id` 与可选的 `session_id`，查询该教师（或指定批次）的 OCR 任务状态分布，返回各状态（pending/processing/done/failed）任务数量、总进度百分比与聚合状态。该工具 SHALL 只读数据库，不修改任务状态。

#### Scenario: 查询指定批次进度
- **WHEN** 教师以 `teacher_id` 和 `session_id` 调用 query_ocr_progress，且该批次存在 done 与 processing 状态的任务
- **THEN** 返回各状态任务数量、`progress_pct`（done/total 的百分比）与聚合状态（processing）

#### Scenario: 查询教师全部任务
- **WHEN** 教师以 `teacher_id` 调用 query_ocr_progress 且不传 `session_id`
- **THEN** 返回该教师名下所有 OCR 任务的状态分布

#### Scenario: 全部完成
- **WHEN** 某批次所有任务状态均为 done
- **THEN** 返回 `progress_pct=100` 且聚合状态为 completed

### Requirement: grade_answer_sheets 批量批改

系统 SHALL 提供 `grade_answer_sheets` 工具，对已 OCR 完成（status=done）的答题卡执行批量批改。工具 SHALL 先解析答案来源（题库匹配 → 教师录入 → LLM 自判三级优先级），再逐份比对判定，返回每份的得分与需人工复核标记。无可用已完成任务时 SHALL 返回结构化错误信息而非抛异常，保证对话不中断。

#### Scenario: 批改已完成 OCR 的任务
- **WHEN** 教师以 `session_id` 调用 grade_answer_sheets，且该批次存在 status=done 的任务
- **THEN** 逐份执行批改，返回批改份数、失败份数与每份的 `total_score` 与 `needs_review` 标记

#### Scenario: 答案来源按优先级解析
- **WHEN** 教师同时提供 `exam_paper_id`（题库匹配）与 `teacher_answers`（教师录入）
- **THEN** 优先采用教师录入的答案作为批改标准

#### Scenario: 空批次不中断对话
- **WHEN** 教师调用 grade_answer_sheets 且不存在 status=done 的任务
- **THEN** 返回含错误原因与批次标识的结构化信息，不抛出异常

### Requirement: save_grading_results 确认保存并触发诊断

系统 SHALL 提供 `save_grading_results` 工具，将批改结果写入学生作答记录并触发障碍诊断管线。该工具 SHALL 触发审批门控（教师确认后执行），且在保存时跳过学号未在系统中注册的学生记录，避免脏数据进入学情分析链路。

#### Scenario: 保存并触发诊断
- **WHEN** 教师确认后调用 save_grading_results，且存在已批改任务
- **THEN** 写入学生作答记录，返回 `saved_count`、`skipped_count` 与 `diagnosis_triggered`，并异步触发障碍诊断

#### Scenario: 需审批门控
- **WHEN** 教师调用 save_grading_results 且尚未通过审批
- **THEN** 工具 SHALL NOT 执行保存，等待教师确认

#### Scenario: 未注册学号跳过
- **WHEN** 批改结果中存在学号不在 students 表中的记录
- **THEN** 该记录 SHALL 被静默跳过，计入 `skipped_count`，不阻塞其余记录保存

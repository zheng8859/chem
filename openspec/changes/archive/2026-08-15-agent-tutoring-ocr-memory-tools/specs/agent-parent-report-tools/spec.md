## Purpose

定义家长报告工具组（30 号文档 §3.7 的 2 个工具）的行为契约：生成通俗语言的家长学习报告并推送到家长端，且通过内容过滤机制保证家长仅可见子女学习薄弱点摘要、不可见具体错题内容。

## ADDED Requirements

### Requirement: generate_parent_report 生成家长报告

系统 SHALL 提供 `generate_parent_report` 工具，接受 `student_id`，返回该学生的家长版学习报告，包含练习统计、薄弱知识点、学习进度与教师建议，并使用通俗语言（非专业术语）表述。

#### Scenario: 生成家长报告
- **WHEN** 家长请求某学生的家长报告，且该学生存在练习与诊断数据
- **THEN** 返回含练习统计、薄弱知识点摘要、学习进度与教师建议的报告，语言通俗

#### Scenario: 学生无数据
- **WHEN** 学生无练习或诊断数据
- **THEN** 返回「暂无足够数据」的说明，不生成虚假报告

### Requirement: 家长报告内容过滤

系统 SHALL 在家长报告中执行内容过滤：仅展示知识薄弱点摘要（知识点名称与掌握程度），不暴露子女的具体错题内容、原始作答或逐题答案。过滤 SHALL 在报告生成时完成，家长无法通过报告反推具体题目内容。

#### Scenario: 报告不包含具体错题
- **WHEN** 家长报告展示某学生的薄弱知识点
- **THEN** 报告 SHALL 仅含知识点名称与掌握程度摘要，不含具体题目正文、学生原始作答或逐题正确答案

#### Scenario: 教师端不受过滤影响
- **WHEN** 教师查看同一学生的详细诊断数据
- **THEN** 教师 SHALL 可见完整错题内容（过滤仅作用于家长报告）

### Requirement: send_report_to_parent 推送报告

系统 SHALL 提供 `send_report_to_parent` 工具，接受 `student_id`，将已生成的报告推送到家长端通知。该工具 SHALL 触发审批门控（确认后发送）。

#### Scenario: 推送报告通知
- **WHEN** 家长确认后调用 send_report_to_parent
- **THEN** 向家长端发送「学习报告已生成」通知，返回发送状态

#### Scenario: 需确认后发送
- **WHEN** 调用 send_report_to_parent 且尚未确认
- **THEN** 工具 SHALL NOT 发送，等待确认

## Purpose

试卷 Word 导出能力 — A4 排版、密封线、五种题型分类渲染、学生版/教师版双模式。

## ADDED Requirements

### Requirement: Word 文档导出

系统 SHALL 提供 `GET /api/v1/exams/{id}/export?format=docx&with_answers={true|false}` 端点，返回 `.docx` 文件下载。

#### Scenario: 导出学生版试卷
- **WHEN** 调用 `GET /exams/{id}/export?format=docx&with_answers=false`
- **THEN** 返回 Word 文件，页面 A4（210×297mm），上/下/左/右边距 2.5/2.0/2.5/2.0cm，正文字体 SimSun 11pt，标题 16pt 加粗居中，密封线含姓名/班级/得分区，不含答案和解析

#### Scenario: 导出教师版试卷
- **WHEN** 调用 `GET /exams/{id}/export?format=docx&with_answers=true`
- **THEN** 返回 Word 文件，页面规格同学生版，答案红色标注，解析绿色标注，底部标记"（含答案版）"

### Requirement: 题型分类渲染

试卷 SHALL 按题型分组排列，每种题型独立标题区。

#### Scenario: 选择题渲染
- **WHEN** 导出含选择题的考试
- **THEN** 标题"一、选择题"，每题显示题号 + 题干 + 缩进选项（A/B/C/D）

#### Scenario: 填空题渲染
- **WHEN** 导出含填空题的考试
- **THEN** 标题"二、填空题"，题干保留 `___` 标记

#### Scenario: 计算题渲染
- **WHEN** 导出含计算题的考试
- **THEN** 标题"三、计算题"，每题后留答题空白区

#### Scenario: 实验题和推断题渲染
- **WHEN** 导出含实验题或推断题的考试
- **THEN** 分别以"四、实验题"和"五、推断题"分组

### Requirement: 格式兜底

当考试不含某题型时，该题型标题区 SHALL 不出现。当导出的 docx 格式不可用时，系统 SHALL 返回 400 错误。

#### Scenario: 缺少某题型不显示标题
- **WHEN** 考试只含选择题
- **THEN** 仅渲染"一、选择题"，不显示填空/计算/实验/推断题标题

#### Scenario: 不支持的格式
- **WHEN** 请求 `format=pdf`
- **THEN** 返回 400，detail 包含"仅支持 docx 格式"

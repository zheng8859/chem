## Why

Tab 2/3/4 与 40号前端规格存在三个功能缺口：考试卡片缺导出入口、题库管理缺批量操作、真题卡片缺"加入考试"按钮。后端对应 API 均已就绪，只需前端接线。

## What Changes

- **Tab 4 考试导出**：考试卡片加"导出"按钮，调用 `GET /api/v1/exams/{id}/export?format=docx&with_answers=false` 触发浏览器下载
- **Tab 2 批量操作**：题库卡片加 checkbox 多选 + 底部批量删除栏
- **Tab 3 加入考试**：真题卡片加"加入考试"按钮 → checklist 弹窗选择目标考试 → `POST /exams/{id}/questions`

## Capabilities

### New Capabilities
- `exam-export-frontend`: 考试 Word 导出前端入口
- `bank-batch-ops`: 题库批量操作（多选 + 批量删除）

### Modified Capabilities
- `exam-workbench-frontend`: Tab 3 真题卡片加"加入考试"操作，Tab 4 加导出按钮

## Impact

- `frontend/pages/exam-v2.html` — Tab 2/3/4 模板 + JS 函数
- 零后端变更

## Why

题库管理和考试生命周期是 25 号文档 §5-§6 定义的核心后端能力。当前实现完成了基础 CRUD，但缺：系统预设文件夹保护、考试题目计数、考试状态机缺 grading/archived 状态转换、向量检索服务已写代码但未接通 ChromaDB、试卷 Word 导出完全未实现。本变更补齐这些能力。

## What Changes

- **QuestionSet 模型**：新增 `is_system` 字段，删除文件夹时校验非系统预设
- **考试列表**：`list_exams_by_class` 加子查询统计题目数
- **考试删除保护**：in_progress 状态禁止删除
- **向量检索服务**：接通 ChromaDB 真实嵌入方案，替代当前纯关键词匹配的 `_rag_search`
- **试卷导出**：`GET /api/v1/exams/{id}/export?format=docx&with_answers=true` 生成 Word 文档
- **QuestionSetItem 移除端点**：修复 400 错误

## Capabilities

### New Capabilities
- `exam-bank-backend`: 题库管理后端 — 系统预设保护、考试题目计数、删除安全策略、ChromaDB 向量检索 RAG 接入
- `exam-export`: 试卷 Word 导出 — A4 排版、五种题型分类渲染、学生版/教师版双模式

### Modified Capabilities
- `exam-lifecycle`: 考试删除策略 — in_progress 状态禁止删除，仅 pending/completed 可删

## Impact

- `app/models/question_bank.py` — QuestionSet 加 `is_system`
- `app/services/question_bank_service.py` — 删除时校验 `is_system`
- `app/services/teaching_service.py` — `list_exams_by_class` 加题目计数
- `app/services/question_generation_service.py` — `_rag_search` 改为 ChromaDB 向量检索
- `app/services/exam_export_service.py` — 新文件，Word 导出服务
- `app/api/v1/teaching.py` — 加导出端点 + 删除保护
- `app/api/v1/question_bank.py` — 删除时校验
- `app/schemas/teaching.py` — 导出请求 Schema
- 零数据库迁移（`is_system` 为非空布尔默认 false）

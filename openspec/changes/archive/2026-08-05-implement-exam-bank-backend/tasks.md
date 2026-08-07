## 1. QuestionSet 系统预设保护

- [x] 1.1 `QuestionSet` 模型加 `is_system` 列（Boolean, default=False）
- [x] 1.2 `QuestionSetRead` schema 加 `is_system: bool = False`
- [x] 1.3 `delete_question_set` service 加 `is_system` 校验，抛出 `QuestionBankError`
- [x] 1.4 `DELETE /question-sets/{id}` router 捕获 403 错误

## 2. 考试题目计数与删除保护

- [x] 2.1 `list_exams_by_class` service 加子查询统计 `question_count`
- [x] 2.2 `delete_exam` service 加状态校验（`in_progress` → 403）
- [x] 2.3 `DELETE /exams/{id}` router 捕获 `TeachingError` → 403

## 3. 向量检索 ChromaDB 接通

- [x] 3.1 新建 `app/services/vector_search_service.py` — `VectorSearchService` 类
- [x] 3.2 实现 `search_similar(keyword, knowledge_points, limit)` → ChromaDB 向量检索
- [x] 3.3 实现 embedding 调用封装（`_get_embedding` → dashscope text-embedding-v3）
- [x] 3.4 实现降级逻辑：ChromaDB 不可用 → 纯关键词匹配
- [x] 3.5 `question_generation_service._rag_search` 改为调用 `VectorSearchService`
- [x] 3.6 添加启动时索引检查：维度不匹配 → 清空重建

## 4. 试卷 Word 导出

- [x] 4.1 新建 `app/services/exam_export_service.py` — `ExamExportService` 类
- [x] 4.2 添加 `python-docx` 依赖到 `requirements.txt`
- [x] 4.3 实现 `export_to_docx(exam_id, with_answers)` — A4 排版 + 边距 + 密封线
- [x] 4.4 实现题型分组渲染：选择题/填空题/计算题/实验题/推断题
- [x] 4.5 实现双模式：学生版（无答案）和教师版（红色答案 + 绿色解析）
- [x] 4.6 添加 `GET /api/v1/exams/{id}/export` 端点，返回 `StreamingResponse`
- [x] 4.7 添加 `ExamExportRequest` schema（`format`/`with_answers` 参数校验）

## 5. 验证与收尾

- [x] 5.1 向量检索：验证 ChromaDB 检索返回与关键词重叠但不同的结果
- [x] 5.2 Word 导出：验证生成的 .docx 文件在 Word 中正常打开
- [x] 5.3 删除保护：验证 `in_progress` 考试返回 403
- [x] 5.4 跑一遍基础回归（test_regression.py）

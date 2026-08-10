## Context

Phase 3 REST API 已完成题库基础 CRUD 和考试生命周期端点。See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- QuestionSet 加 `is_system` 保护，防止误删种子数据
- 考试列表返回 `question_count`
- 考试删除加状态校验
- 接通 ChromaDB 向量检索替代纯关键词 RAG
- 实现 Word 试卷导出（学生版 + 教师版）

**Non-Goals:**
- 不实现 grading/archived 状态转换（后续章节）
- 不实现全班结果总览和学生详情 API（后续章节）
- 不实现 PDF 导出（仅 docx）
- 不重构现有 `ExamManagementService` 架构

## Decisions

### 1. `is_system` 字段：Boolean 默认 false，无迁移

**选择:** SQLAlchemy `mapped_column(Boolean, default=False)`，不写 migration。

**理由:** SQLite 加列不需要 migration 脚本自动化（Alembic 可 autogenerate），默认值 `false` 兼容现有所有记录。

### 2. 考试题目计数：子查询，不存持久化字段

**选择:** `select(func.count(ExamPaperQuestion.id)).where(ExamPaperQuestion.exam_paper_id == ExamRecord.exam_paper_id).correlate(ExamRecord).scalar_subquery()`。

**理由:** 题目数是派生数据，不冗余存储。和 QuestionSet 的 `question_count` 实现一致。单次查询开销量可忽略（考试记录数 <100）。

### 3. 删除保护：service 层校验，不是 middleware

**选择:** `TeachingService.delete_exam` 内部检查 `exam.status`，`in_progress` → raise `TeachingError`。

**理由:** 删除逻辑已经在 service 层，新增强校验不应改变 router 层接口。router 捕获 `TeachingError` → `HTTPException(403)`。

### 4. 向量检索：VSS 服务类，非函数内联

**选择:** 新建 `app/services/vector_search_service.py`，暴露 `search_similar(question_ids, knowledge_points, limit)` 方法。

**理由:** 当前 `_rag_search` 是 `question_generation_service.py` 中的模块级函数，直接查 HistoricalExam 表。改为调用 VSS 服务，服务内部封装 ChromaDB 客户端、embedding 调用和降级逻辑。

### 5. Word 导出：python-docx 流式构建，不依赖模板文件

**选择:** `ExamExportService.export_to_docx(exam_id, with_answers)` 用 python-docx API 动态构建 Document 对象。

**理由:** 不需要维护 .docx 模板文件，题型分组逻辑纯代码控制。导出结果写入 `io.BytesIO` → StreamingResponse。

**排版实现:**
- 页面设置：`doc.sections[0].page_width/height` = A4
- 边距：`section.top_margin` 等 = Cm(2.5/2.0/2.5/2.0)
- 字体：`run.font.name = 'SimSun'`，大小 `Pt(11)` / `Pt(16)`
- 密封线：左侧 textbox 含姓名/班级/得分
- 答案标注：`run.font.color.rgb = RGBColor(0xB4, 0x3C, 0x28)` (error red)
- 解析标注：`run.font.color.rgb = RGBColor(0x2C, 0x6E, 0x49)` (success green)

## Risks / Trade-offs

- **[Risk] python-docx 中文支持依赖系统字体** → Mitigation: `font.name = 'SimSun'` 在 Windows dev 环境保证；部署文档注明 Linux 需装 `fonts-wqy-zenhei`
- **[Risk] ChromaDB embedding 调用增加出题延迟** → Mitigation: embedding 调用异步化，embedding 模型不可用时降级关键词匹配不阻塞出题
- **[Risk] 考试含大量题目时 docx 生成耗时长** → Mitigation: 第一期同步生成（<50 题 <2s 可接受）；后续可改为后台任务 + 轮询

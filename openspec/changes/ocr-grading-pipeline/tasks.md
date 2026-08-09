## 1. P0-1: ORM 字段补齐

- [ ] 1.1 `models/ocr.py` — UploadSession 新增 10 字段：original_filename, mime_type, file_path, detected_type, ocr_result_json, grading_result_json, total_pages, completed_pages, fallback_used, version, error_message
- [ ] 1.2 `models/ocr.py` — OCRTask 新增 9 字段：teacher_id (FK), image_path, title, student_id_raw, student_name_raw, progress, confirmed, error_message, completed_at
- [ ] 1.3 `schemas/ocr.py` — 新增 OCRTaskCreate, OCRTaskUpdate schema；更新 OCRTaskRead, UploadSessionRead 包含新字段
- [ ] 1.4 生成 Alembic migration `alembic revision --autogenerate -m "补齐OCR模型字段"` 并验证 upgrade/downgrade
- [ ] 1.5 更新 `tests/unit/test_schemas_ocr.py` 覆盖新字段
- [ ] 1.6 更新 `tests/integration/test_ocr_api.py` 适配 schema 变更

## 2. P0-2: 文件上传 + 存储

- [ ] 2.1 `config.py` — 新增 OCR_UPLOAD_DIR, OCR_MAX_FILE_SIZE_MB, OCR_ALLOWED_EXTENSIONS, OCR_MAX_BATCH_SIZE
- [ ] 2.2 `api/v1/ocr.py` — batch_upload 端点从 JSON body 重写为 multipart/form-data（files + Form fields）
- [ ] 2.3 `services/ocr_service.py` — batch_upload_stub() → batch_upload()：文件校验（类型/大小/批量上限）→ 写磁盘 → 创建 UploadSession + OCRTask → 自动创建 ExamRecord
- [ ] 2.4 文件校验逻辑：MIME 白名单 → 扩展名白名单 → 大小检查 → 返回对应 HTTP 错误码（400/413/415）
- [ ] 2.5 文件存储：`{OCR_UPLOAD_DIR}/{teacher_id}/{YYYY-MM-DD}/{uuid}.{ext}`，UUID 防碰撞，存相对路径
- [ ] 2.6 `schemas/ocr.py` — 更新 BatchUploadResponse 对齐新字段
- [ ] 2.7 `tests/integration/test_ocr_api.py` — 新增真实文件上传测试（正常上传/空文件/错误类型/超大文件）

## 3. P1: 百度 OCR 引擎

- [ ] 3.1 `services/ocr_engine.py` — BaiduTokenManager：OAuth 2.0 token 内存缓存 + 300s 安全边距 + 自动刷新
- [ ] 3.2 `services/ocr_engine.py` — BaiduOCREngine.recognize()：读文件 → base64 → POST doc_analysis API (handprint_mix + recg_formula + CHN_ENG) → 解析响应
- [ ] 3.3 `services/ocr_engine.py` — OCRResult 数据类：raw_text, confidence, words_result, student_id_raw, student_name_raw, is_partial, engine, error
- [ ] 3.4 `services/ocr_engine.py` — 学生信息提取：_extract_student_id() + _extract_student_name()，百度引擎正则（标签格式 + 202[4-9] 回退 + 通用回退）
- [ ] 3.5 `services/ocr_engine.py` — 错误处理：API 业务错误 → status=failed；HTTP 异常 → status=failed；raw_text<10 字符 → is_partial=True
- [ ] 3.6 `api/v1/ocr.py` — GET /ocr/services/status 返回三个引擎可用性

## 4. P1: APScheduler 调度器

- [ ] 4.1 `infrastructure/scheduler.py` — 新增 _run_ocr_processor() job wrapper + ocr_processor IntervalTrigger(5s) 注册
- [ ] 4.2 `services/ocr_service.py` — claim_next_pending_tasks(limit=5)：SELECT pending tasks ORDER BY created_at → UPDATE status=processing, progress=10 → return tasks
- [ ] 4.3 `services/ocr_service.py` — process_ocr_task()：调用 EngineRouter.route() → 成功则 status=done/progress=100/填充结果 → 失败则 status=failed/error_message
- [ ] 4.4 并发控制：asyncio.Semaphore(5) 在 BaiduOCREngine 中，process_ocr_task() 用 asyncio.create_task 发射不阻塞后续 tick
- [ ] 4.5 `api/v1/ocr.py` — POST /ocr/tasks/{task_id}/retry：status→pending，清空 error_message 和 ocr_raw_result

## 5. P2: 答案解析器

- [ ] 5.1 `services/answer_parser.py` — parse_answers_from_text(raw_text, question_count)：预处理 → 选择题正则提取 → 非选择题 LLM 辅助提取 → 合并校验
- [ ] 5.2 `services/answer_parser.py` — _parse_choice_answers()：纯正则 `/(\d+)\.\s*([A-Da-d])/`，零 LLM 调用
- [ ] 5.3 `services/answer_parser.py` — _parse_complex_answers()：定位题号 → 构建 LLM prompt → 批量提取非选择题答案
- [ ] 5.4 `tests/unit/test_answer_parser.py` — 选择题正则测试（正常/噪音/边界）+ LLM mock 测试

## 6. P2: 答案来源选择 + 批改引擎

- [ ] 6.1 `services/grading_service.py` — resolve_answer_source()：三种模式按优先级——题库匹配（ExamPaper→Question.answer）→ 教师录入 → LLM 自判
- [ ] 6.2 `services/grading_service.py` — AnswerKey 数据类：source_mode, question_count, questions dict
- [ ] 6.3 `services/ocr_engine.py` — BaiduOCREngine.grade_via_correct_edu()：创建批改任务 → 3s 轮询（最长 120s）→ 解析 correctResult 编码（0/1/2/3）
- [ ] 6.4 `services/grading_service.py` — _grade_via_llm()：答案解析 → 选择题字符串比较 → 非选择题 LLM 化学等价判断 → 构建 GradingResult
- [ ] 6.5 `services/grading_service.py` — _compare_choice_answer()：strip + upper + exact match + empty/AUTO 处理
- [ ] 6.6 `services/grading_service.py` — _compare_chemical_answer()：LLM 语义等价（下标归一 H2O≡H₂O，箭头等价 →≡=）
- [ ] 6.7 `schemas/ocr.py` — GradingResult, QuestionGrading, GradingSummary schema
- [ ] 6.8 `api/v1/ocr.py` — POST /grading/run：接收 task_ids + 可选 exam_paper_id/teacher_answers → 逐个执行批改
- [ ] 6.9 `api/v1/ocr.py` — GET /grading/results/{batch_id}：查询批次批改结果
- [ ] 6.10 `tests/unit/test_answer_comparison.py` — 字符串比较 + LLM mock 化学等价测试
- [ ] 6.11 `tests/integration/test_grading_api.py` — grading/run + grading/results E2E

## 7. P3: MinerU 引擎 + VLM 降级 + 引擎路由

- [ ] 7.1 `services/ocr_engine.py` — MinerUEngine：is_available()（检查模型目录/CLI）、parse()（子进程调用 mineru parse，120s timeout）→ MinerUResult
- [ ] 7.2 `services/ocr_engine.py` — _extract_student_mineru()：MinerU 专用正则（标签格式 + 通用 8-10 位数字回退）
- [ ] 7.3 `llm/providers/openai_compat.py` — chat() 的 messages 类型 `list[dict[str, str]]` → `list[dict[str, Any]]` 支持多模态
- [ ] 7.4 `llm/router.py` — 新增 llm_vision_chat() + 注册智谱 GLM-4V provider
- [ ] 7.5 `services/ocr_engine.py` — VLMFallbackEngine.recognize()：base64 图片 + 结构化提取 prompt → JSON 解析 → OCRResult(fallback_used=True)
- [ ] 7.6 `services/ocr_engine.py` — EngineRouter.route(image_path, detected_type)：IMAGE 路径（Baidu→VLM→partial）/ PDF 路径（MinerU→PDF转图→Baidu→VLM→partial）
- [ ] 7.7 `config.py` — 新增 ZHIPU_BASE_URL, ZHIPU_VISION_MODEL
- [ ] 7.8 调度器 process_ocr_task() 改为调用 EngineRouter.route() 而非直接调 BaiduOCREngine
- [ ] 7.9 `tests/unit/test_engine_router.py` — 路由选择 + 降级触发测试

## 8. P3: 障碍诊断联动 + 保存结果

- [ ] 8.1 `services/grading_service.py` — save_results()：查询已完成批改的 task → 校验 student_id_raw → 双写 StudentSubmission + StudentAnswer → confirmed=True
- [ ] 8.2 `services/grading_service.py` — 脏数据保护：student_id_raw 不在 students 表中 → 跳过 + 记录 skip_reason
- [ ] 8.3 `services/grading_service.py` — _post_save_pipeline()：asyncio.create_task 异步执行 诊断→统计→报告 链
- [ ] 8.4 `services/grading_service.py` — Pipeline 各步独立 try/catch，前一步失败不阻塞后续
- [ ] 8.5 `api/v1/ocr.py` — POST /grading/save：接收 task_ids → save_results() → 返回 saved_count + skipped_count + diagnosis_triggered
- [ ] 8.6 `tests/integration/test_grading_save.py` — 正常保存/学号不存在跳过/重复保存幂等/诊断触发

## 9. P3: Agent 工具（第二批）

- [ ] 9.1 `agent/tools/ocr_progress.py` — Tool 1: 查询 OCR 进度（teacher_id, batch_id → 批次摘要）
- [ ] 9.2 `agent/tools/grading_trigger.py` — Tool 2: 触发批改（teacher_id, batch_id, exam_paper_id → 逐题判定）
- [ ] 9.3 `agent/tools/grading_save.py` — Tool 3: 保存结果（teacher_id, batch_id → saved_count + 诊断触发）

## 10. P4: 班级统计 + LLM 报告

- [ ] 10.1 `services/ocr_service.py` — compute_exam_statistics(exam_record_id)：参与人数/平均分/分数分布/逐题错误率/障碍分布 → 写入 ExamRecord.error_stats + status→completed
- [ ] 10.2 `services/ocr_service.py` — generate_class_report(exam_record_id)：LLM prompt 注入考试数据 → 300-500 字中文分析报告（整体表现/薄弱知识点/障碍诊断/改进建议）
- [ ] 10.3 `api/v1/ocr.py` — POST /ocr/stats：接收 exam_record_id → compute_exam_statistics + generate_class_report

## 11. P4: 前端 ocr-v2.html

- [ ] 11.1 `frontend/pages/ocr-v2.html` — Vue 3 CDN 单页骨架：牛津蓝+深青+暖纸色，Cormorant Garamond+IBM Plex Sans
- [ ] 11.2 上传区：拖拽+点击双通道，文件类型/大小前端校验，multipart 上传 → POST /ocr/tasks/batch
- [ ] 11.3 进度区：5s 轮询 GET /ocr/sessions/{id}/tasks → 渲染状态卡片（done=绿/processing=黄/failed=红/pending=灰），失败任务附重试按钮
- [ ] 11.4 批改预览：OCR 全部完成后显示"开始批改"按钮 → POST /grading/run → 渲染结果表格（学号/姓名/总分/逐题判定/状态）
- [ ] 11.5 确认保存：底部操作栏（平均分/最高分/最低分）+ [确认保存][导出成绩][开始诊断] 按钮 → POST /grading/save
- [ ] 11.6 状态流转：全流程单页完成（上传→进度→批改→确认），不跳页

## 12. P4: E2E 管线测试

- [ ] 12.1 `tests/golden/test_ocr_pipeline.py` — test_full_pipeline_choice：上传→等待 OCR→批改→保存→诊断（使用预制备选答案题卡图片）
- [ ] 12.2 `tests/golden/test_ocr_pipeline.py` — test_engine_fallback：mock 百度 OCR 不可用 → VLM 降级路径
- [ ] 12.3 `tests/golden/test_ocr_pipeline.py` — test_unreadable_image：模糊图片 → is_partial=True → 教师手动录入

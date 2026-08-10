## Why

教师批改答题卡是 ChemAI 工具链的最高频入口场景。当前系统只有 OCR 模块的模型骨架（UploadSession + OCRTask 的 ORM 模型和基础 CRUD API），但文件上传、OCR 识别引擎、批改执行、诊断联动全部缺失——`batch_upload_stub` 硬编码 3 个假任务，整条管线无法跑通。本次变更实现设计文档《24-答题卡OCR批改系统设计》规定的完整 10 步管线，使教师能真正通过拍照上传完成从答题卡到诊断报告的端到端流程。

## What Changes

- **补齐 ORM 字段**：UploadSession 新增 10 个字段（文件信息、进度追踪、降级标记、乐观锁），OCRTask 新增 9 个字段（图片路径、学生信息、进度、确认标记、错误信息），对齐设计文档 §三.3 和 §六.1
- **实现文件上传**：`POST /ocr/tasks/batch` 从 JSON stub 重写为 multipart 文件上传，包含类型校验（JPG/PNG/BMP/WEBP/PDF）、大小限制（10MB）、自动文件存储（`data/ocr_uploads/{teacher_id}/{date}/{uuid}.ext`）
- **实现三引擎 OCR**：百度 OCR（`doc_analysis`，手写中文识别主力）、MinerU（PDF 本地解析）、VLM 多模态降级（GLM-4V/MiMo），含引擎路由器（EngineRouter）按文件类型自动选择 + 完整降级链，含 OAuth 2.0 Token 管理（300s 安全边距 + 30 天有效期）
- **实现 APScheduler 调度器**：5 秒间隔 IntervalTrigger，每 tick 拾取最多 5 个 pending 任务，`asyncio.Semaphore(5)` 控制 API 并发，含学生信息正则提取（学号 + 姓名，百度引擎和 MinerU 引擎各一套正则规则）
- **实现答案来源选择**：三种模式按优先级——题库匹配（从 ExamPaper → Question.answer）、教师录入（前端表单）、LLM 自判（标记需教师复核）
- **实现 LLM 批改引擎**：双路径——百度 `correct_edu` 异步批改（创建任务 → 3s 轮询，最长 120s）优先，LLM 语义批改降级（答案解析器：纯正则提取选择题 + LLM 辅助提取非选择题；化学等价判断：非选择题走 LLM 语义比较，含下标归一化和箭头等价）
- **实现障碍诊断联动**：保存结果时写入 `StudentAnswer` 表并异步触发 `DiagnosisService.run_llm_diagnosis()`，串行执行诊断→统计→报告的后处理链
- **实现班级统计与报告**：考试后聚合计算平均分、分数分布、逐题错误率、障碍分布，LLM 生成自然语言班级分析报告
- **新增 `ocr-v2.html`**：Vue 3 CDN 单页应用，覆盖上传→OCR 进度轮询→批改预览→确认保存全流程，对接 12 个 REST API 端点
- **API 端点精简为 12 个**：合并冗余端点（upload/recognize/batch→统一 batch 端点，preview/confirm→合并入 grading 流程），砍掉暂不需要的端点（base64 识别、题库导入独立端点），保留核心查询和管理端点

## Capabilities

### New Capabilities

- `ocr-upload-pipeline`: 答题卡批量上传、文件验证、存储、UploadSession 状态机管理
- `ocr-recognition-engine`: 三引擎 OCR 识别（百度/MinerU/VLM）+ 降级链 + APScheduler 任务调度 + 学生信息提取
- `ocr-grading-engine`: 答案来源解析（题库/教师/LLM 自判）+ 双路径批改（correct_edu/LLM 语义）+ 答案解析器
- `ocr-statistics-report`: 考试后班级统计聚合 + LLM 自然语言报告生成

### Modified Capabilities

- `data-model`: UploadSession 新增 10 字段、OCRTask 新增 9 字段、StudentSubmission 字段调整
- `exam-lifecycle`: ExamRecord 在 OCR 上传阶段自动创建（status='grading'），批改完成后由统计步骤驱动状态迁移至 'completed'

## Impact

- **数据模型**: `models/ocr.py`（UploadSession + OCRTask + StudentSubmission 字段补齐），Alembic migration 新增
- **API 端点**: `api/v1/ocr.py` 重写 batch_upload + 新增 grading/stats/services-status 端点
- **服务层**: `services/ocr_service.py` 大幅扩展（上传/调度/统计/报告），新增 `services/ocr_engine.py`（三引擎）、`services/answer_parser.py`（答案解析）、`services/grading_service.py`（批改引擎）
- **基础设施**: `infrastructure/scheduler.py` 新增 ocr_processor IntervalTrigger job
- **LLM 层**: `llm/providers/openai_compat.py` messages 类型扩展为支持多模态，`llm/router.py` 新增智谱 VLM provider
- **配置**: `config.py` 新增上传目录、大小限制、VLM provider 等配置项
- **前端**: 新增 `frontend/pages/ocr-v2.html`（API 驱动单页应用）
- **Agent 工具**: 新增 3 个 OCR Agent Tool（查询进度/触发批改/保存结果），第二批交付
- **权限**: 复用已有 `ocr` 和 `grading` 资源权限，无需修改 RBAC spec
- **外部依赖**: 百度 OCR API（`doc_analysis` + `correct_edu`），MinerU CLI（本地模型下载），智谱 GLM-4V API
- **偏离设计文档**: `file_data`（数据库 BLOB）改为 `file_path`（文件系统路径），原因：SQLite BLOB 存储 10MB 图片为反模式

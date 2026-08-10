## Context

ChemAI 当前 OCR 模块只有模型骨架：`UploadSession`、`OCRTask`、`StudentSubmission` 三个 ORM 模型和基础 CRUD 查询端点。`batch_upload_stub` 硬编码 3 个占位任务，整条"上传→OCR→批改→保存→诊断→统计→报告"管线未实现。详见 proposal.md — Why。

本设计基于需求对齐阶段确认的 11 项决策，覆盖 P0 到 P4 全部五个优先级的实现方案。

### 现有架构约束

- **数据库**：SQLite + WAL 模式，单容器单体部署
- **ORM**：SQLAlchemy 2.0 async，mapped_column + Mapped 类型注解
- **调度器**：APScheduler `AsyncIOScheduler`，Asia/Shanghai 时区，已有 3 个 cron job
- **LLM**：三层 fallback 路由（MiMo → 通义千问 → DeepSeek），OpenAI 兼容协议
- **Agent**：LangGraph `create_react_agent`，MCP 工具注册模式
- **诊断引擎**：`chem_skills.chemistry_diagnosis.engine`，已实现 `run_llm_diagnosis(exam_record_id)` 批量诊断
- **学情面板**：`PanelService` 按需实时聚合，指数衰减加权算法

## Goals / Non-Goals

**Goals:**
- 实现设计文档《24-答题卡OCR批改系统设计》规定的完整 10 步管线
- 三引擎 OCR（百度/MinerU/VLM）全做，含完整降级链
- 双路径批改（correct_edu + LLM 语义）全做
- 三种答案来源（题库匹配/教师录入/LLM 自判）全做
- 45 张答题卡 < 5 分钟端到端处理（设计文档目标）
- 文件存文件系统（路径存 DB），不存 BLOB

**Non-Goals:**
- 不处理手写公式识别（由 LLM 批改阶段补充判断）
- 不做实时视频流批改
- 不做跨校对比统计
- Agent 工具（查询进度/触发批改/保存结果）放第二批
- 题库导入独立端点（`POST /ocr/tasks/{upload_id}/import`）暂时砍掉

## Decisions

### 1. 文件存储：文件系统路径替代 BLOB

**决策**：文件存 `data/ocr_uploads/{teacher_id}/{YYYY-MM-DD}/{uuid}.{ext}`，DB 只存相对路径字符串。

**理由**：SQLite BLOB 存 10MB 图片是反模式（一次 45 张 = 450MB+，数据库膨胀、备份慢、查询每次加载 BLOB）。文件系统读写在 async 环境下性能更好。

**替代方案**：对象存储（MinIO/S3）与单体部署定位冲突，未来多实例部署时迁移。

**偏离设计文档**：设计文档 §三.3 的 `file_data`（二进制）字段改为 `file_path`（字符串）。这是与设计文档的唯一偏离点。

### 2. 调度器策略：每 tick 取 5 个 + Semaphore(5)

**决策**：APScheduler IntervalTrigger(5s)，每 tick SELECT 最多 5 条 pending 任务，`asyncio.create_task` 发射到后台，`asyncio.Semaphore(5)` 控制百度 API 并发数。

**理由**：每 tick 1 个任务时 45 张串行耗时 3.75-22.5 分钟，不满足 < 5 分钟目标。Semaphore(5) 确保不会打爆百度 API 限流。后台协程不阻塞调度器下次触发。

**替代方案**：Celery + Redis 消息队列 → 过度工程，与单体部署定位冲突。

### 3. 引擎路由：EngineRouter 统一降级链

**决策**：单一 `EngineRouter.route(image_path, detected_type)` 入口，根据文件类型自动选择引擎+降级路径。

```
IMAGE: 百度 OCR(doc_analysis) → VLM(GLM-4V/MiMo) → partial result
PDF:   MinerU(parse_by_cli) → 逐页转图→百度 OCR → VLM → partial result
```

**理由**：调度器只需调一个入口，引擎选择和降级逻辑内聚在 EngineRouter 中。新增引擎只需修改路由表。

### 4. VLM 集成：扩展现有 LLM Router

**决策**：`OpenAICompatProvider.chat()` 的 messages 类型从 `list[dict[str, str]]` 改为 `list[dict[str, Any]]`，新增 `llm_vision_chat()` 函数注册智谱 GLM-4V provider。

**理由**：最小改动原则——只改类型签名（向后兼容），不加新 provider 抽象层。OpenAI Vision API 格式本身支持 content 数组。

### 5. 答案解析：正则 + LLM 混合策略

**决策**：选择题用纯正则 `/(\d+)\.\s*([A-Da-d])/` 提取，非选择题(填空/计算/实验)用单次 LLM 调用批量提取。

**理由**：选择题格式固定，正则准确率 ~99% 且零成本。非选择题格式多变（化学式下标、方程式箭头、单位），LLM 语义理解比逐题正则更可靠。一次 LLM 调用提取多道题比逐题调 LLM 更经济。

### 6. 答案比较：分层策略

**决策**：选择题纯字符串比较（strip+upper+exact），非选择题（化学式/方程式）走 LLM 语义等价判断。

**理由**：化学等价不能只靠字符串匹配——`H2O` 与 `H₂O`、`→`与`=`在化学语境中等价。选择题(A/B/C/D)无此类歧义。

### 7. 事务边界：双写 + 异步后处理

**决策**：保存时 `StudentSubmission` + `StudentAnswer` 在同一事务中写入。诊断→统计→报告的 Pipeline 用 `asyncio.create_task` 异步执行，不阻塞 HTTP 响应。

**理由**：双写保证答题卡原始快照（StudentSubmission）和诊断输入（StudentAnswer）同时就绪。异步后处理链耗时可能 20-60 秒（LLM 诊断 5-15s + 统计 2-5s + 报告 3-10s），不应阻塞教师等待。

### 8. ExamRecord 生命周期扩展

**决策**：上传时自动创建 ExamRecord（status='grading'），统计完成后由 `compute_exam_statistics()` 改为 'completed'。

**理由**：诊断引擎（步骤 8）需要 `exam_record_id`，越早创建越好。上传阶段教师已选定班级，信息足够创建 ExamRecord。

**现有状态机影响**：新增一条状态转换路径 `[不存在] → grading`（从 OCR 上传创建），属于 ADDED 行为，不修改现有 pending→in_progress→grading→completed 路径。

### 9. API 端点精简

**决策**：设计文档 20 个端点精简为 12 个，合并功能重叠端点，砍掉暂不需要的端点。

**精简清单**：
| 设计文档端点 | 处理方式 |
|------------|---------|
| `POST /ocr/upload` | 合并到 `POST /ocr/tasks/batch`（上传即开始） |
| `POST /ocr/recognize` | 内部调用（调度器），不暴露 API |
| `POST /ocr/recognize/batch` | 合并到 `POST /ocr/tasks/batch` |
| `POST /ocr/recognize/base64` | 砍掉（前端用 multipart） |
| `POST /ocr/preview` | 合并（上传后自动预览） |
| `POST /ocr/confirm` | 合并到 `POST /grading/save` |
| `POST /ocr/retry-vision` | 合并到 `POST /ocr/tasks/{id}/retry` |
| `POST /ocr/parse/document` | 内部调用（EngineRouter） |
| `POST /ocr/tasks/{upload_id}/import` | 砍掉（题库导入暂不做） |

### 10. 前端：新建 ocr-v2.html

**决策**：新建 `frontend/pages/ocr-v2.html`，Vue 3 CDN 单页应用，参考现有 `exam-v2.html` 的技术模式，保留 `ocr.html` 原型的视觉设计（牛津蓝 + 深青 + 暖纸色）。

**理由**：原型代码是 AI 生成的静态 demo，改造不如重写。Vue 3 CDN 模式与项目其他页面一致。

## Risks / Trade-offs

- **[Risk] MinerU 模型下载失败 → PDF 解析不可用**：降级链自动回退到 PDF→逐页转图→百度 OCR。MinerU 失败不影响核心流程，仅增加 PDF 场景的 API 调用成本
- **[Risk] 百度 API 配额耗尽 → 整个 OCR 不可用**：VLM 降级作为兜底。虽慢且贵（Token 计费），但保证管线不中断。前端展示降级提示"当前使用备用引擎，速度较慢"
- **[Risk] 异步后处理链失败 → 诊断/统计/报告丢失**：Pipeline 每步独立 try/catch，前一步失败不阻塞后续步骤。失败只记录日志，不重试（重试可能重复诊断）。教师可在 Panel 手动触发诊断
- **[Risk] LLM 自判模式误判化学等价**：所有 LLM 自判结果标记 `needs_review=True`，前端橙色警告"AI 自行判定，建议人工复核"。`correct_answer="AUTO"` 时强制判错
- **[Trade-off] 文件系统 vs 对象存储**：文件系统简单但单机绑定，多实例部署时需迁移到共享存储或 MinIO。当前单体部署可接受，迁移路径清晰（改 config + 加 storage adapter 层）
- **[Trade-off] 调度器轮询 vs WebSocket**：轮询有 5s 延迟但实现简单，设计文档 §十.1 已详细论证此决策
- **[Trade-off] SQLite 任务队列 vs Redis**：SQLite 简单但高并发下可能成为瓶颈。单教师场景（45-90 张/批次）够用，设计文档 §十.2 已论证

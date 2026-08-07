## Why

当前 `DiagnosisService.get_class_diagnosis()` 返回全零占位数据，`POST /diagnosis/run-llm` 和 `PUT /diagnosis/override` 端点未实现。学生错题诊断的核心链路缺失——从错题到根因到自适应练习的闭环断裂。需要实现 LLM 驱动的障碍诊断引擎，填补从"知道谁错了"到"知道为什么错"的关键缺口。

## What Changes

- **新增** `chem_skills/chemistry_diagnosis/engine/` 纯函数库：`models.py`（诊断数据结构）、`llm_diagnoser.py`（LLM 诊断 + 批量并发）、`aggregator.py`（学生画像 + 班级分布聚合）
- **新增** `POST /api/v1/diagnosis/run-llm/{exam_id}` 端点，支持教师触发批量 LLM 诊断
- **新增** `PUT /api/v1/diagnosis/override/{student_answer_id}` 端点，支持教师覆盖诊断结果
- **替换** `DiagnosisService.get_class_diagnosis()` 的 stub 实现为真实的诊断聚合逻辑
- **简化** 诊断架构为纯 LLM 路径（不含规则引擎、不含 confidence 列、不含置信度分级自动采纳）

## Capabilities

### New Capabilities
- `llm-diagnoser`: LLM 驱动的障碍诊断核心——接收错题上下文，返回 barrier_type + misconception_category（3×6 矩阵）+ reasoning + suggestion。并发控制 asyncio.Semaphore(5)，批量上限 10 条/次。
- `diagnosis-aggregator`: 诊断结果聚合——单生 barrier_type 画像 JSON、班级三维障碍分布统计、薄弱知识点排名。

### Modified Capabilities
- `diagnosis-engine`: 移除规则引擎路径和 confidence 置信度分级，简化为纯 LLM 诊断 + 教师覆盖；新增 misconception_category 作为 LLM 输出必填字段；替换 get_class_diagnosis() stub。

## Impact

- `chem_skills/chemistry_diagnosis/engine/` — 新增 models.py, llm_diagnoser.py, aggregator.py
- `app/services/diagnosis_service.py` — 替换 stub + 新增 run_llm_diagnosis()、override_diagnosis()
- `app/api/v1/diagnosis.py` — 新增两个端点，修改 class diagnosis 端点
- `app/schemas/diagnosis.py` — 新增 LLM 诊断请求/响应、覆盖请求/响应 schema
- 零数据库 migration（复用现有 StudentAnswer 字段，不加 confidence 列）

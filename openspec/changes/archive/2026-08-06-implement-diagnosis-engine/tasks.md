## 1. Engine Models

- [x] 1.1 创建 `chem_skills/chemistry_diagnosis/engine/models.py`：定义 `DiagnosisResult`、`BarrierProfile`、`ClassDistribution` dataclass
- [x] 1.2 创建 `chem_skills/chemistry_diagnosis/engine/__init__.py`：全量导出三个模块的公共接口

## 2. LLM Diagnoser

- [x] 2.1 创建 `chem_skills/chemistry_diagnosis/engine/llm_diagnoser.py`：实现 `diagnose_single()` 函数，接收 LLM Provider callback + 四项输入，构建 Prompt，调用 LLM，正则提取 JSON，验证字段合法性
- [x] 2.2 实现 `diagnose_batch()` 函数：接收错误作答列表（最多 10 条），`asyncio.Semaphore(5)` 并发调用 `diagnose_single()`，返回 `list[DiagnosisResult]` + failed_count

## 3. Aggregator

- [x] 3.1 创建 `chem_skills/chemistry_diagnosis/engine/aggregator.py`：实现 `aggregate_student()` — 输入 `list[StudentAnswer]`，计数 → 归一化 → 输出 `BarrierProfile`
- [x] 3.2 实现 `aggregate_class()` — 输入按学生分组的诊断结果，输出 `ClassDistribution` + top_weak_kps

## 4. Service Integration

- [x] 4.1 在 `DiagnosisService` 中新增 `run_llm_diagnosis(db, exam_record_id)` — 筛选最多 10 条未诊断错误作答，调用 `diagnose_batch()`，写入 StudentAnswer，触发聚合
- [x] 4.2 在 `DiagnosisService` 中新增 `override_diagnosis(db, student_answer_id, data)` — 更新单条作答的 barrier_type 和 misconception_category，设置 diagnosed_by=teacher 和 diagnosis_overridden_at
- [x] 4.3 替换 `DiagnosisService.get_class_diagnosis()` stub — 调用 aggregator 的真实聚合逻辑

## 5. API Endpoints

- [x] 5.1 新增 `POST /api/v1/diagnosis/run-llm/{exam_id}` 端点 — 调用 `DiagnosisService.run_llm_diagnosis()`，返回 `{"success": true, "analyzed_count": N, "failed_count": N, "remaining_count": N}`。所有 Provider 不可用时返回 503
- [x] 5.2 新增 `PUT /api/v1/diagnosis/override/{student_answer_id}` 端点 — 调用 `DiagnosisService.override_diagnosis()`，返回旧值 + 新值
- [x] 5.3 新增 request/response Pydantic schemas（`DiagnosisRunResponse`、`DiagnosisOverrideRequest`、`DiagnosisOverrideResponse`）
- [x] 5.4 前端 exam-v2.html 添加诊断按钮 + 自动循环逻辑：读取 `remaining_count`，> 0 时自动再次触发，进度条展示，按钮禁用直到 `remaining_count = 0`

## 6. Tests

- [x] 6.1 引擎单元测试：`diagnose_single()` mock LLM → 验证 JSON 提取和字段校验；`diagnose_batch()` → 验证并发和批量上限
- [x] 6.2 聚合测试：`aggregate_student()` → 验证占比计算和边界（零作答）；`aggregate_class()` → 验证分布统计
- [x] 6.3 API 集成测试：`POST /diagnosis/run-llm/{exam_id}` → 验证诊断流程；`PUT /diagnosis/override/{student_answer_id}` → 验证覆盖逻辑

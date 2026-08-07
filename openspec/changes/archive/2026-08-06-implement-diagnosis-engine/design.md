## Context

当前 `DiagnosisService.get_class_diagnosis()` 返回全零占位数据，`chem_skills/chemistry_diagnosis/engine/` 仅有空 `__init__.py`。参见 proposal.md — Why。

现有基础设施就绪：`StudentAnswer` 模型含 `barrier_type`、`misconception_category`、`diagnosed_by`、`diagnosis_overridden_at`；`BarrierType`、`MisconceptionCategory`、`DiagnosisSource` 枚举已定义；LLM Provider 层基于 `httpx.AsyncClient` 的异步调用模式已稳定运行。

## Goals / Non-Goals

**Goals:**
- 实现 LLM 驱动的障碍诊断纯函数库（models.py、llm_diagnoser.py、aggregator.py）
- 替换 `get_class_diagnosis()` stub 为真实聚合逻辑
- 新增 `POST /diagnosis/run-llm/{exam_id}` 和 `PUT /diagnosis/override/{student_answer_id}` 端点

**Non-Goals:**
- 不实现规则引擎
- 不添加 `confidence` 列到数据库
- 不实现单次作答实时诊断
- 不跨学科诊断

## Decisions

### 1. 架构：引擎优先（方案 A）

**选择**：`chem_skills/chemistry_diagnosis/engine/` 纯函数库先写，API 层薄封装。与四维审核引擎一致。

**理由**：引擎核心不依赖 FastAPI/DB，可独立测试，可被 Agent 工具、API、CLI 等多入口直接 import。

**替代方案**：直接在 `DiagnosisService` 中内联逻辑 — 耦合 DB Session，测试需要 mock 数据库，不利于复用。

### 2. 文件结构：三层模块

```
chem_skills/chemistry_diagnosis/engine/
├── __init__.py           # 全量导出
├── models.py             # DiagnosisResult, BarrierProfile, ClassDistribution
├── llm_diagnoser.py      # diagnose_single() + diagnose_batch()
└── aggregator.py         # aggregate_student() + aggregate_class()
```

`models.py`：纯 dataclass，不依赖 Pydantic/SQLAlchemy，引擎零外部依赖。
`llm_diagnoser.py`：接收 LLM Provider callback（依赖注入），不直接 import LLM 模块。
`aggregator.py`：接收 student_answers 列表，纯计数逻辑，不访问数据库。

### 3. LLM 调用：依赖注入 Provider Callback

**选择**：`llm_diagnoser.py` 不直接 import LLM 模块，由调用方（DiagnosisService）注入 `Callable[[str], str]`。

**理由**：引擎保持零外部依赖，LLM Provider 切换不影响引擎代码，测试时注入 mock 即可。

**替代方案**：引擎直接 import LLM Provider — 耦合度高，测试困难，但更简单。取舍是依赖注入的开销很小（一个 callback 参数），收益大（可测试性）。

### 4. 并发：asyncio.Semaphore(5)

**选择**：`asyncio.gather` + `asyncio.Semaphore(5)`。

**理由**：与现有 LLM Provider 层（`httpx.AsyncClient`）一致，全链路异步，无需线程池。

**替代方案**：设计文档提到的 `concurrent.futures.ThreadPoolExecutor(5)` — 在异步 FastAPI 应用中引入线程池会增加上下文切换开销，且与现有异步模式不一致。

### 5. LLM Prompt 设计

System Prompt：教育心理学专家视角，分析学生障碍类型。
User Prompt 模板：

```
## 题目
{question_content}

## 学生答案
{student_answer}

## 正确答案
{correct_answer}

## 历史错题
{history}

请分析该学生的障碍类型，返回 JSON。
```

输出 JSON schema 在 Prompt 中明确指定四个字段。温度 0.3，max_tokens 2000。温度 0.3 已经足够稳定，不需要 JSON mode —— 正则 `r'\{[\s\S]*\}'` 提取后驗证字段即可。

### 6. 批量上限：10 条/次

**选择**：`POST /diagnosis/run-llm/{exam_id}` 单次最多诊断 10 条未诊断错误作答。

**理由**：每个 LLM 调用 ~2-3 秒，5 并发，单批 ~5-6 秒。40 人班 200 条错题分 20 次，教师可逐步触发。避免单次请求超时。

### 7. 教师覆盖端点

**选择**：`PUT /diagnosis/override/{student_answer_id}` — 覆盖单条作答的诊断结果，非学生整体画像。

**理由**：更精细的控制。教师可以在考试详情页逐题修改诊断，而非只能改学生画像。

**替代方案**：设计文档的 `PUT /diagnosis/override/{student_id}` 覆盖学生整体画像 — 粒度太粗，教师无法精确修改单条诊断。

### 8. 教师覆盖与 LLM 诊断等权聚合

**选择**：覆盖记录与 LLM 诊断记录在聚合时等权计数。

**理由**：教师覆盖是对单条作答的修正，并入整体计数即可。90%/5%/5% 的强制加权会扭曲画像。

### 9. misconception_category 对所有 barrier_type 尝试推断

**选择**：LLM Prompt 要求对所有 barrier_type（包括 reading 和 expression）尝试推断 misconception_category。推断不出时填 null。

**理由**：审题障碍和表述障碍也绑定特定知识领域（如氧化还原题目的信息提取、化学用语规范），null 会丢失有价值的信号。

**替代方案**：reading 时强制 null — 信息损失，下游自适应引擎无法区分"氧化还原审题差"和"有机化学审题差"。

### 10. LLM 全部不可用时返回 503

**选择**：所有 LLM Provider 不可用时，`POST /diagnosis/run-llm/{exam_id}` 返回 `503 Service Unavailable`，不做降级分类。

**理由**：返回随机或默认分类比不返回更危险——下游自适应引擎会基于错误诊断推送不合适的题目。

### 11. 前端自动循环诊断

**选择**：前端点一次"开始诊断"后自动循环触发，直到全部未诊断作答处理完毕。进度条展示，期间按钮禁用。

**理由**：教师只需点一次，体感连续。后端响应需加 `remaining_count` 字段供前端判断终止条件。

**替代方案**：单次触发，每次只诊断 10 条 — 教师需点 20 次，体验差。

### 12. 部分成功处理

**选择**：成功的写入 DB + 聚合，失败的保持 `barrier_type=NULL` 等下次重试。返回 `{"analyzed_count": 7, "failed_count": 3}`。

**理由**：部分成功 > 全部失败。LLM 偶发超时或格式错误不影响已成功的诊断。

**替代方案**：全部或全不 — 任一条失败就回滚，教师需反复重试，体验差。

### 13. 批量上限硬编码 10

**选择**：10 条/次硬编码，不在 BarrierConfig 中可配置。

**理由**：MVP 简单优先。配合前端自动循环，教师体感无差异。`BarrierConfig` 已有 4 个阈值，不再增加配置项。

### 14. 不记录覆盖审计日志

**选择**：覆盖直接写入，不创建 audit_log 表。`diagnosis_overridden_at` 不为空即表示被覆盖过。

**理由**：教师覆盖频率低（< 5%），独立审计表过度设计。

## Risks / Trade-offs

- **[LLM 幻觉]** LLM 可能返回非法 barrier_type 或 misconception_category → 正则提取 JSON 后字段验证，非法值跳过并计入 failed_count
- **[温度 0.3 非绝对稳定]** 同一错题两次调用可能给出不同诊断 → 教师覆盖作为纠错机制，同一学生多次诊断后占比趋于稳定
- **[无 confidence 可能导致错误诊断被采纳]** LLM 诊断结果直接写入无审核门槛 → 教师覆盖端点作为安全阀，所有诊断结果在教师端可查看、可推翻
- **[批量 10 条/次在大班场景可能不够]** 60 人班 × 30 题可能产生 500+ 错题 → 教师可多次点击触发，或未来调整为可配置上限

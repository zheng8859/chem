## Purpose

LLM 驱动的障碍诊断核心——接收错题的题目内容、标准答案、学生作答和历史错题上下文，通过教育心理学视角分析并返回结构化的三维障碍分类和迷思概念归类结果。

## ADDED Requirements

### Requirement: LLM 障碍诊断输入

LLM 诊断 SHALL 接收四项输入：当前题目正文（截断至 500 字）、学生实际答案、题目标准答案、该学生近期错题列表（最多 5 条，每条含题文、错误答案、正确答案）。

#### Scenario: 正常诊断
- **WHEN** 系统调用 LLM 诊断，传入完整的四项输入
- **THEN** LLM 返回 JSON 包含 barrier_type、misconception_category、reasoning、suggestion

#### Scenario: 无历史错题
- **WHEN** 该学生没有历史错题记录
- **THEN** 历史错题输入为空数组，LLM 仍基于当前题目完成诊断

### Requirement: LLM 诊断输出格式

LLM 返回的 JSON SHALL 包含四个字段：`barrier_type`（concept/reading/expression）、`misconception_category`（chemical_equilibrium/redox/mole_calculation/organic_chemistry/chemical_notation/structure_of_matter 或 null）、`reasoning`（判定依据自然语言）、`suggestion`（教学干预建议）。

#### Scenario: 输出包含 misconception_category
- **WHEN** LLM 判断错误涉及特定化学知识领域
- **THEN** misconception_category 为该领域的枚举值

#### Scenario: 审题障碍尽量推断知识领域
- **WHEN** barrier_type 为 reading
- **THEN** LLM SHALL 尝试推断 misconception_category，判断不了时填 null

### Requirement: 批量诊断并发控制

批量诊断 SHALL 使用 asyncio.Semaphore 控制并发，最多 5 个并发 LLM 调用。单次批量最多诊断 10 条错误作答。

#### Scenario: 10 条错误作答批量诊断
- **WHEN** 触发批量诊断，待诊断作答 10 条
- **THEN** 系统以最多 5 个并发调用 LLM，所有诊断完成后统一写入数据库

#### Scenario: 超过 10 条分批处理
- **WHEN** 待诊断作答超过 10 条
- **THEN** 系统仅诊断前 10 条，返回本次诊断数量，剩余等待下次触发

### Requirement: LLM 诊断结果写入

诊断完成后 SHALL 将结果写入 StudentAnswer 记录：`barrier_type`、`misconception_category`、`diagnosed_by="ai_llm"`。不存储 LLM confidence 分数。

#### Scenario: 诊断结果持久化
- **WHEN** LLM 返回有效诊断结果
- **THEN** StudentAnswer 的 barrier_type、misconception_category、diagnosed_by 字段被更新

#### Scenario: LLM 返回非法值
- **WHEN** LLM 返回的 barrier_type 不是 concept/reading/expression 之一或 misconception_category 不在合法枚举中
- **THEN** 该条诊断被跳过，计入 failed_count，不写入数据库

### Requirement: LLM 调用参数

LLM 调用 SHALL 使用 temperature=0.3 确保输出稳定性，max_tokens=2000 限定输出长度。支持多 LLM Provider 自动回退。

#### Scenario: Provider 回退
- **WHEN** 主 LLM Provider 不可用
- **THEN** 系统自动回退到下一个可用 Provider

#### Scenario: 所有 Provider 不可用
- **WHEN** 所有 LLM Provider 均不可用
- **THEN** 端点 SHALL 返回 `503 Service Unavailable`，不做任何降级分类

### Requirement: 批量诊断部分成功

批量诊断中部分 LLM 调用成功、部分失败时，成功的 SHALL 写入数据库，失败的 SHALL 保持 barrier_type=NULL 等待下次重试。

#### Scenario: 部分成功
- **WHEN** 10 条诊断中 7 条成功、3 条失败（LLM 超时或返回非法值）
- **THEN** 返回 `{"success": true, "analyzed_count": 7, "failed_count": 3, "remaining_count": <total>}`，7 条已写入

### Requirement: 前端自动循环

批量诊断响应 SHALL 包含 `remaining_count` 字段，表示该考试仍有多少条未诊断错误作答。前端 SHALL 在 `remaining_count > 0` 时自动再次触发诊断，直到 `remaining_count = 0`。

#### Scenario: 自动循环直到完成
- **WHEN** 首次诊断返回 `remaining_count: 185`
- **THEN** 前端自动再次触发，直到 `remaining_count: 0`，进度条走完

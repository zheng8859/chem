## Purpose

为 ChemAI AI 内容质量评测提供 100 条结构化 Golden 样本，覆盖 5 大化学模块中出题、诊断、对话辅导三类场景，支持确定性断言和 LLM 语义评分的统一加载与查询。

## ADDED Requirements

### Requirement: Golden 样本按化学模块组织

系统 SHALL 按 5 个化学模块（化学平衡、酸碱盐、氧化还原、有机化学、化学计量）组织 Golden 样本，每模块 20 条，共 100 条。

#### Scenario: 加载化学平衡模块样本
- **WHEN** 评测系统请求 chemical_equilibrium 模块的 Golden 样本
- **THEN** 系统返回 20 条样本，包含出题 8 条、诊断 8 条、对话辅导 4 条

#### Scenario: 加载不存在的模块
- **WHEN** 评测系统请求不存在的模块名称
- **THEN** 系统返回空列表，不抛出异常

### Requirement: 样本结构定义

每条 Golden 样本 SHALL 包含 id、module、category、input 和 expected_output 字段。出题样本额外包含 difficulty、knowledge_points、grade_level 和 tolerance 字段。诊断样本额外包含 tolerance.misconception_match 和 tolerance.confidence_range 字段。对话辅导样本额外包含 expected_output.tone 和 expected_output.uses_socratic_method 字段。

#### Scenario: 验证出题样本完整性
- **WHEN** 加载一条出题类型 Golden 样本
- **THEN** 该样本包含 id、module="question_generation"、category、difficulty（1-5）、knowledge_points（非空列表）、grade_level、input.prompt、input.parameters、expected_output.questions（非空列表）、expected_output.quality_checks、tolerance 和 eval_type="l3" 字段

#### Scenario: 验证诊断样本完整性
- **WHEN** 加载一条诊断类型 Golden 样本
- **THEN** 该样本包含 id、module="diagnosis"、input.question、input.student_answer、expected_output.primary_misconception、expected_output.error_type（概念错误/计算错误/知识空白/推理错误之一）、tolerance.misconception_match="semantic" 和 eval_type="l3" 字段

#### Scenario: 验证对话辅导样本完整性
- **WHEN** 加载一条对话辅导类型 Golden 样本
- **THEN** 该样本包含 id、module="tutoring"、input.student_question、input.context（含 grade_level 和 topic）、expected_output.should_contain_keywords（非空列表）、expected_output.should_not_contain、expected_output.tone（encouraging/neutral/challenging 之一）和 expected_output.uses_socratic_method 字段

### Requirement: Schema 校验

系统 SHALL 提供一个 JSON Schema 文件（tests/evals/golden_dataset/schema.json），对所有 5 个模块的 JSON 数据文件进行结构校验。

#### Scenario: 合法样本通过校验
- **WHEN** 用 schema.json 校验 5 个模块 JSON 文件
- **THEN** 所有文件通过校验，无错误

#### Scenario: 缺失必填字段的样本被拒绝
- **WHEN** 某条样本缺少 id 或 module 字段
- **THEN** Schema 校验失败，报告具体缺失字段名

### Requirement: 容差参数定义

系统 SHALL 定义以下容差参数作为评测框架的核心阈值：scientific_accuracy_min=0.9、misconception_match="semantic"（语义相似度≥0.6）、keyword_match_ratio=0.7、confidence_range=±0.15、confidence_min=0.7、difficulty_match_tolerance=±1级、response_time_max_seconds=30。

#### Scenario: 出题科学性评分应用容差
- **WHEN** 评测出题质量时，科学性检查得分 < 0.9
- **THEN** 该样本的 L3 评测结果标记为不通过，原因注明"科学性不足"

#### Scenario: 诊断语义匹配
- **WHEN** 评测诊断结果时，实际输出与预期输出的迷思概念语义相似度 < 0.6
- **THEN** 该样本的诊断评测结果标记为不通过

### Requirement: 回归基线样本保护

系统 SHALL 维护 4 条已知回归基线样本（golden_027、golden_031、golden_056、golden_089），每次评测后单独验证这些样本的通过状态，不允许基线下调。

#### Scenario: 回归样本劣化检测
- **WHEN** 某条回归基线样本的通过率较上次基线下降
- **THEN** 评测报告明确标注该样本 ID 和劣化幅度，CI 中触发告警

#### Scenario: 新增回归样本
- **WHEN** 某样本在版本更新后通过率下降超过 15%
- **THEN** 该样本添加到回归基线清单，后续每次评测验证

### Requirement: SQLite 数据库存储

系统 SHALL 通过种子脚本（scripts/seed_golden.py）将 5 个模块的 JSON Golden 样本导入 SQLite 数据库（tests/evals/golden_dataset.db），表结构含 golden_samples 和 eval_runs 两张表。

#### Scenario: 种子脚本幂等性
- **WHEN** 多次运行 seed_golden.py
- **THEN** 数据库中的 Golden 样本数据保持一致，不产生重复记录

#### Scenario: 评测运行记录
- **WHEN** 完成一次评测运行
- **THEN** eval_runs 表中新增一条记录，包含时间戳、通过率、失败样本 ID 列表

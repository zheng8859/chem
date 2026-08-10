## MODIFIED Requirements

### Requirement: Diagnosis source tracking

The system SHALL record on each StudentAnswer which diagnostic method produced the barrier type and misconception category. Only LLM diagnosis (ai_llm) and teacher override (teacher) are supported.

#### Scenario: LLM deep diagnosis
- **WHEN** an LLM analyzes the answer from an educational psychology perspective
- **THEN** the StudentAnswer SHALL have diagnosed_by="ai_llm"

#### Scenario: Teacher override
- **WHEN** a teacher manually changes the diagnosis
- **THEN** the StudentAnswer SHALL have diagnosed_by="teacher" and diagnosis_overridden_at set to the current timestamp

### Requirement: Teacher override of AI diagnosis

The system SHALL allow teachers to override AI-generated diagnoses on a specific StudentAnswer via `PUT /diagnosis/override/{student_answer_id}`, recording the override event. Overridden records SHALL be counted with equal weight as LLM-diagnosed records when aggregating the student barrier profile.

#### Scenario: Teacher overrides barrier type
- **WHEN** a teacher changes a StudentAnswer's barrier_type from concept to reading
- **THEN** the system SHALL update barrier_type, set diagnosed_by="teacher", and set diagnosis_overridden_at

#### Scenario: Teacher overrides misconception category
- **WHEN** a teacher changes a StudentAnswer's misconception_category
- **THEN** the student's barrier_profile SHALL be recalculated reflecting the correction

#### Scenario: Override counted equally in aggregation
- **WHEN** a student has 5 LLM-diagnosed answers and 1 teacher-overridden answer
- **THEN** all 6 answers SHALL be counted with equal weight when computing the barrier_profile ratios

### Requirement: Async post-diagnosis profile update

The system SHALL update Student.barrier_profile JSON after each batch of new diagnoses is saved.

#### Scenario: Barrier profile recalculation
- **WHEN** a new batch of diagnoses is saved for students
- **THEN** each affected student's Student.barrier_profile JSON SHALL be recalculated to reflect the latest distribution of concept/reading/expression across all diagnosed answers

## REMOVED Requirements

### Requirement: Confidence tiering for auto-adoption
**Reason**: LLM 自评置信度不可靠——诊断和打分由同一模型完成，缺乏独立校准。改为不存储 confidence，所有 LLM 诊断结果直接写入，教师覆盖作为唯一的质控信号。
**Migration**: confidence 字段不会添加到 StudentAnswer 表。现有的三级阈值判定逻辑不实现。

### Requirement: Diagnosis source tracking — AI rule-engine
**Reason**: 当前考试场景仅为选择题，规则引擎对纯选择答案无信号（覆盖率 < 30%）。诊断路径纯 LLM 驱动。
**Migration**: 移除 `diagnosed_by="ai_rule"` 场景。规则引擎作为未来优化方向保留可能性。

### Scenario: Override weights — teacher dominates
**Reason**: 教师覆盖记录与 LLM 诊断记录在聚合时改为等权计数，不再使用 90%/5%/5% 强制权重。
**Migration**: aggregator 的计数逻辑对所有 diagnosed_by 值一视同仁。

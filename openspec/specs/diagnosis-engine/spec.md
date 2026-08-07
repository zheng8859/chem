## Purpose

Defines the orthogonal 3×6 diagnosis framework that classifies student errors by barrier type (how they err) and misconception category (what they misunderstand), with LLM deep diagnosis and teacher override for per-answer correction.

## ADDED Requirements

### Requirement: Orthogonal diagnosis matrix

The system SHALL classify each student error using two independent dimensions: barrier type (concept/reading/expression) and misconception category (chemical_equilibrium/redox/mole_calculation/organic_chemistry/chemical_notation/structure_of_matter).

#### Scenario: Error classified in both dimensions
- **WHEN** a student answers a chemical equilibrium question incorrectly due to misunderstanding Le Chatelier's principle
- **THEN** the diagnosis SHALL produce barrier_type=concept AND misconception_category=chemical_equilibrium

#### Scenario: Reading error on redox problem
- **WHEN** a student misses a redox question because they overlooked the "acidic medium" condition in the stem
- **THEN** the diagnosis SHALL produce barrier_type=reading AND misconception_category=redox

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
- **WHEN** a new batch of diagnoses is saved for a student
- **THEN** the Student.barrier_profile JSON SHALL be recalculated to reflect the latest distribution of concept/reading/expression across all diagnosed answers

### Requirement: Configurable diagnosis thresholds

The system SHALL allow each teacher to configure the consecutive wrong-answer thresholds that trigger warnings for each barrier type.

#### Scenario: Default thresholds
- **WHEN** a teacher has not customized their BarrierConfig
- **THEN** the system SHALL use concept_threshold=3, reading_threshold=2, expression_threshold=3

#### Scenario: Custom threshold triggers warning
- **WHEN** a student's consecutive_wrong_count for a concept-type error reaches the teacher's configured concept_threshold
- **THEN** the system SHALL generate a warning log event

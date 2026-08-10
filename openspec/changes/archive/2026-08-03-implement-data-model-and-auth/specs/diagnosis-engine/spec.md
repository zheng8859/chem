## Purpose

Defines the orthogonal 3×6 diagnosis framework that classifies student errors by barrier type (how they err) and misconception category (what they misunderstand), with rule-engine pre-classification, LLM deep diagnosis, teacher override, and async profile updates.

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

The system SHALL record on each StudentAnswer which diagnostic method produced the barrier type and misconception category.

#### Scenario: AI rule-engine diagnosis
- **WHEN** a rule engine pre-classifies an answer based on keyword matching
- **THEN** the StudentAnswer SHALL have diagnosed_by="ai_rule"

#### Scenario: LLM deep diagnosis
- **WHEN** an LLM analyzes the answer from an educational psychology perspective
- **THEN** the StudentAnswer SHALL have diagnosed_by="ai_llm"

#### Scenario: Teacher override
- **WHEN** a teacher manually changes the diagnosis
- **THEN** the StudentAnswer SHALL have diagnosed_by="teacher" and diagnosis_overridden_at set to the current timestamp

### Requirement: Teacher override of AI diagnosis

The system SHALL allow teachers to override AI-generated diagnoses on any StudentAnswer, recording the override event.

#### Scenario: Teacher overrides barrier type
- **WHEN** a teacher changes a StudentAnswer's barrier_type from concept to reading
- **THEN** the system SHALL update barrier_type, set diagnosed_by="teacher", and set diagnosis_overridden_at

#### Scenario: Override weights — teacher dominates
- **WHEN** a teacher has overridden a diagnosis and the barrier_profile is recalculated
- **THEN** the teacher-specified barrier type SHALL carry 90% weight in the recalculation, the other two types 5% each

### Requirement: Confidence tiering for auto-adoption

The system SHALL use confidence thresholds to determine whether a diagnosis is auto-adopted or flagged for review.

#### Scenario: High confidence auto-adoption
- **WHEN** an LLM diagnosis has confidence ≥ 0.8
- **THEN** the barrier_type and misconception_category SHALL be automatically written to StudentAnswer

#### Scenario: Medium confidence flagging
- **WHEN** an LLM diagnosis has confidence between 0.7 and 0.8
- **THEN** the diagnosis SHALL be adopted but flagged for teacher attention

#### Scenario: Low confidence review
- **WHEN** an LLM diagnosis has confidence < 0.7
- **THEN** the diagnosis SHALL be marked for mandatory teacher review before adoption

### Requirement: Async post-diagnosis profile update

The system SHALL asynchronously update the student's consecutive wrong/correct counts and barrier profile after each new diagnosis is saved.

#### Scenario: Consecutive wrong count increment
- **WHEN** a student answers a mole calculation question incorrectly for the third consecutive time on the same knowledge point
- **THEN** the StudentAnswer.consecutive_wrong_count SHALL be set to 3

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

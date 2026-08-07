## Purpose

Provides REST API endpoints for the diagnosis system — barrier configuration, knowledge point management, review tasks (spaced repetition), review history, and warning logs — enabling the diagnostic loop that is ChemAI's core value proposition.

## ADDED Requirements

### Requirement: Barrier configuration management
The system SHALL allow teachers to read and update their barrier diagnosis thresholds (concept, reading, expression consecutive-wrong triggers and mastery standard).

#### Scenario: Teacher reads own barrier config
- **WHEN** a teacher sends GET /api/v1/diagnosis/barrier-config
- **THEN** the system returns the teacher's BarrierConfig with concept_threshold, reading_threshold, expression_threshold, mastery_threshold, auto_sync_enabled

#### Scenario: Teacher updates barrier thresholds
- **WHEN** a teacher sends PATCH /api/v1/diagnosis/barrier-config with new concept_threshold=5
- **THEN** the system updates the config and returns the updated BarrierConfigRead

#### Scenario: Default config for new teacher
- **WHEN** a teacher with no existing config sends GET /api/v1/diagnosis/barrier-config
- **THEN** the system auto-creates a default config (thresholds: concept=3, reading=3, expression=2, mastery=3)

### Requirement: Knowledge point listing
The system SHALL provide endpoints to list and filter knowledge points, including their dynamic error rates.

#### Scenario: List all knowledge points
- **WHEN** a teacher sends GET /api/v1/knowledge-points
- **THEN** the system returns all knowledge points with category, question_count, and dynamic_error_rate

#### Scenario: Filter by category
- **WHEN** a user sends GET /api/v1/knowledge-points?category=电解质
- **THEN** the system returns only knowledge points in the 电解质 category

### Requirement: Class diagnosis overview
The system SHALL provide a class-level diagnosis overview showing barrier distribution and per-student diagnosis items for a given exam.

#### Scenario: Teacher requests class diagnosis
- **WHEN** a teacher sends GET /api/v1/diagnosis/class/{class_id}/exam/{exam_id}
- **THEN** the system returns ClassDiagnosisResponse with class_summary (barrier rates, top weak KPs) and per-student diagnosis items

### Requirement: Review task management
The system SHALL support listing review tasks by student and completing review tasks (spaced repetition with level progression).

#### Scenario: Student lists pending reviews
- **WHEN** a student sends GET /api/v1/reviews/pending?student_id={id}
- **THEN** the system returns review tasks where next_review_date <= today and status is pending

#### Scenario: Complete a review task
- **WHEN** a student sends POST /api/v1/reviews/complete with review_task_id and result=true
- **THEN** the system upgrades the task to the next level (1→3→7→14→30 days→mastered), schedules next_review_date, and records a ReviewHistory entry

#### Scenario: Failed review task downgrade
- **WHEN** a student sends POST /api/v1/reviews/complete with result=false
- **THEN** the system downgrades the task level by 1 (minimum 1) and reschedules for the next day

### Requirement: Warning log management
The system SHALL support listing, filtering, and resolving warning logs (attendance, performance, error-rate, new-barrier).

#### Scenario: Teacher lists active warnings
- **WHEN** a teacher sends GET /api/v1/warnings?class_id={id}&resolved=false
- **THEN** the system returns unresolved warnings for students in that class, ordered by severity

#### Scenario: Resolve a warning
- **WHEN** a teacher sends POST /api/v1/warnings/resolve with warning_id
- **THEN** the system marks the warning as resolved and updates all three notification flags

### Requirement: Adaptive practice assignment
The system SHALL provide an endpoint to assign adaptive practice questions based on student barrier profile and ZPD.

#### Scenario: Teacher assigns adaptive practice
- **WHEN** a teacher sends POST /api/v1/practice/assign with student_id, question_count, optional target_barrier
- **THEN** the system returns a practice_session_id, list of question IDs, and estimated_time_minutes (stub: returns random questions from same knowledge points until ZPD engine is built)

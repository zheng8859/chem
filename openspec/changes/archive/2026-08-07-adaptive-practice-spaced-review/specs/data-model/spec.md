## MODIFIED Requirements

### Requirement: ReviewTask 6-level Ebbinghaus model

The system SHALL model ReviewTask levels from 0 to 5 (previously 1 to 6), where Level 0 represents initial learning with immediate review availability, Levels 1-4 represent increasing review intervals (1, 3, 7, 14 days), and Level 5 represents mastery with no further review. The review interval for each level SHALL be computed from the current time plus the level's interval days.

#### Scenario: ReviewTask with Level 0 for new wrong answer
- **WHEN** a student answers incorrectly and auto-sync creates a ReviewTask
- **THEN** the system SHALL create the task with level=0, next_review_date=now()

#### Scenario: Level 1 review scheduled 1 day later
- **WHEN** a student completes a review at Level 0 and meets upgrade conditions
- **THEN** the system SHALL set level=1 and next_review_date=now()+1day

#### Scenario: Level 5 marks task as mastered
- **WHEN** a ReviewTask reaches level=5
- **THEN** the system SHALL set status=completed and next_review_date=NULL

#### Scenario: Downgrade from Level 3 to Level 2
- **WHEN** a student answers incorrectly at Level 3
- **THEN** the system SHALL decrement to level=2 and set next_review_date=now()+7days (standard Level 2 interval)

## ADDED Requirements

### Requirement: VariantQuestion entity

The system SHALL maintain a VariantQuestion table that stores LLM-generated variant questions isolated from the Question main table for analytics purity.

#### Scenario: VariantQuestion storage
- **WHEN** a variant question is generated
- **THEN** the system SHALL store it with original_question_id (FK to Question), content, question_type, options, answer, analysis, knowledge_point_tags, difficulty, generated_at, and expires_at (default now()+90days)

#### Scenario: VariantQuestion lifecycle
- **WHEN** expires_at passes
- **THEN** the variant SHALL NOT be returned for reuse; new variants SHALL be generated on next request

#### Scenario: VariantQuestion does not appear in Question queries
- **WHEN** querying the Question table for exam questions, bank browsing, or analytics
- **THEN** VariantQuestion records SHALL NOT be included (separate table, no UNION or JOIN in analytics queries)

### Requirement: PracticeSessionQuestion join table

The system SHALL maintain a PracticeSessionQuestion join table linking PracticeSession records to their assigned Question records with ordering.

#### Scenario: Practice session contains ordered questions
- **WHEN** a practice session is created
- **THEN** the system SHALL create PracticeSessionQuestion records with practice_session_id, question_id, and sort_order for each assigned question

#### Scenario: Unique constraint on session-question pair
- **WHEN** a duplicate (session_id, question_id) pair is inserted
- **THEN** the system SHALL reject it with a unique constraint violation

### Requirement: PracticeSession extended fields

The system SHALL extend the PracticeSession model with a business identifier, title, question count, and optional deadline.

#### Scenario: PracticeSession with business fields
- **WHEN** a practice session is created
- **THEN** the system SHALL store practice_id (unique string), title, question_count, and optional deadline alongside the existing barrier_type and status fields

### Requirement: Student barrier tracking fields

The system SHALL store the student's barrier type distribution and weak knowledge points on the Student model for efficient ZPD computation without repeated aggregation.

#### Scenario: Barrier type stored as JSON
- **WHEN** the diagnosis engine completes a student analysis
- **THEN** the system SHALL update Student.barrier_type with {"concept": 0.7, "reading": 0.15, "expression": 0.15} format

#### Scenario: Weak knowledge points stored as JSON array
- **WHEN** the diagnosis engine identifies weak knowledge points
- **THEN** the system SHALL update Student.weak_knowledge_points with ["氧化还原反应", "离子反应"] format

### Requirement: Daily practice in ExamRecord

The system SHALL use ExamRecord with type=daily_practice (in addition to existing practice/monthly/homework types) for the daily scheduler's per-student practice records.

#### Scenario: Daily practice ExamRecord
- **WHEN** the daily scheduler creates a practice for a student
- **THEN** the system SHALL create an ExamRecord with type="daily_practice", class_id from the student's class, exam_date=today, and question_stats containing the target knowledge points, question count, and difficulty metadata

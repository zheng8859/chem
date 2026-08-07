## MODIFIED Requirements

### Requirement: Variant question generation and tracking

The system SHALL store LLM-generated variant questions in a dedicated VariantQuestion table (isolated from the Question main table), with a reference to the original question and an expiration timestamp, enabling cross-student reuse within 90 days without polluting exam analytics or difficulty calibration data.

#### Scenario: Variant created from original question
- **WHEN** the LLM generates 3 variants of question #42 by changing substance, data, and option wording
- **THEN** the system SHALL create 3 VariantQuestion records with original_question_id=42, expires_at=now()+90days

#### Scenario: Variants reused across students within 90 days
- **WHEN** student B requests variants for question #42 and VariantQuestion records exist with original_question_id=42 and expires_at > now()
- **THEN** the system SHALL return the existing variants without calling LLM

#### Scenario: Expired variants trigger regeneration
- **WHEN** student requests variants for question #42 and all existing VariantQuestion records have expires_at < now()
- **THEN** the system SHALL call LLM to generate fresh variants

#### Scenario: Variants excluded from analytics
- **WHEN** computing class-level error rates, difficulty calibration, or any statistical report
- **THEN** the system SHALL NOT include VariantQuestion records

## ADDED Requirements

### Requirement: Practice session question association

The system SHALL associate PracticeSession records with their constituent questions through a dedicated PracticeSessionQuestion join table, enabling lookup of which questions were served in which session.

#### Scenario: Questions linked to practice session
- **WHEN** a practice session is created with 10 questions
- **THEN** the system SHALL create 10 PracticeSessionQuestion records with session_id, question_id, and sort_order

#### Scenario: Student fetches questions for active session
- **WHEN** a student opens a pending practice session
- **THEN** the system SHALL return all questions for that session ordered by sort_order

### Requirement: Practice session structured metadata

The system SHALL store practice sessions with a business identifier (practice_id), title, question count, and optional deadline in addition to the existing barrier tracking fields.

#### Scenario: Practice session with full metadata
- **WHEN** an adaptive practice is assigned to a student
- **THEN** the system SHALL create a PracticeSession with practice_id (format: "adaptive_{student_id}_{timestamp}"), title, question_count, and optional deadline

#### Scenario: Deadline-aware task listing
- **WHEN** a practice task has a deadline in the past and the session is not completed
- **THEN** the system SHALL include an "expired" status indicator in task list responses

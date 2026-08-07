## Purpose

Enables adaptive practice sessions driven by barrier type and ZPD, persisting session metadata while storing individual answers as StudentAnswer records and tracking variant question lineage.

## ADDED Requirements

### Requirement: Practice session tracking

The system SHALL create a PracticeSession record when a student begins an adaptive practice session, tracking the targeted barrier type, knowledge points, and outcomes.

#### Scenario: Practice session for concept barrier
- **WHEN** a student whose dominant barrier is concept starts an adaptive practice on redox reactions
- **THEN** the system SHALL create a PracticeSession with barrier_type=concept, knowledge_point_tags=["氧化还原反应"], status=in_progress

#### Scenario: Session completion
- **WHEN** the student answers all served questions
- **THEN** the PracticeSession SHALL transition to completed with questions_served and questions_correct populated

#### Scenario: Session abandonment
- **WHEN** a student exits practice without completing all questions
- **THEN** the PracticeSession SHALL transition to abandoned, preserving partial results

### Requirement: ZPD-based question selection

The system SHALL select practice questions within the student's Zone of Proximal Development, avoiding questions already mastered (mastery_threshold consecutive correct) or far beyond current level.

#### Scenario: Mastered knowledge point skipped
- **WHEN** a student has answered oxidation-reduction questions correctly 3 times consecutively (meeting mastery_threshold)
- **THEN** the practice engine SHALL NOT serve additional oxidation-reduction questions in the current session

#### Scenario: Too-difficult questions excluded
- **WHEN** selecting practice questions for a student whose current level maps to medium difficulty
- **THEN** the system SHALL NOT serve competition-level questions

### Requirement: Variant question generation and tracking

The system SHALL store LLM-generated variant questions in the Question table with a reference to the blueprint question and the dimensions that were varied.

#### Scenario: Variant created from blueprint
- **WHEN** the LLM generates a variant of question #42 by changing the substance from HCl to H₂SO₄
- **THEN** the system SHALL create a new Question with variant_of_question_id=42, variant_dimensions={"substance": true, "value": false, "stem": false, "options": false, "difficulty": false}, and source=ai_generated

#### Scenario: Variant dimensions guide audit
- **WHEN** an audit engine reviews a variant question
- **THEN** it SHALL focus on the dimensions flagged true in variant_dimensions, skipping unchanged dimensions

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

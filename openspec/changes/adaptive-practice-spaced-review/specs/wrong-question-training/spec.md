## Purpose

Provides students with on-demand access to their wrong question history, LLM-generated variant questions for targeted practice on the same knowledge point at the same difficulty, and ephemeral training sessions with learning suggestions.

## ADDED Requirements

### Requirement: Wrong question listing with error count

The system SHALL return a paginated list of a student's wrong questions, ordered by cumulative error count descending then by most recent error time descending.

#### Scenario: Wrong questions sorted by error frequency
- **WHEN** a student has wrong answers on questions Q1 (5 errors), Q2 (3 errors), Q3 (1 error)
- **THEN** the system SHALL return questions in order: Q1, Q2, Q3

#### Scenario: Same error count sorted by recency
- **WHEN** two questions have the same error count
- **THEN** the system SHALL order by last_error_at descending (most recently wrong first)

#### Scenario: Each wrong question includes your_answer
- **WHEN** listing wrong questions for a student
- **THEN** each entry SHALL include the student's most recent answer content (your_answer), the correct answer, the analysis, knowledge points, difficulty, and error count

#### Scenario: Empty wrong question list
- **WHEN** a student has no incorrect answers
- **THEN** the system SHALL return an empty list with total=0

#### Scenario: Simple offset/limit pagination
- **WHEN** the client requests wrong questions with limit=30 and offset=0
- **THEN** the system SHALL return at most 30 results and the total count

### Requirement: Variant question generation with isolated storage

The system SHALL generate variant questions via LLM that share the same knowledge point and difficulty as the original question but have different surface form (data, scenario, option wording), storing them in a dedicated VariantQuestion table separate from the Question main table.

#### Scenario: Generate 3 variants in one LLM call
- **WHEN** a student requests variants for a choice question about redox reactions at medium difficulty
- **THEN** the system SHALL call the LLM once with a prompt requesting exactly 3 variant questions, all sharing the same knowledge points and difficulty, with different values/scenarios/option wording

#### Scenario: Variants stored in isolated table
- **WHEN** LLM returns 3 variant questions
- **THEN** the system SHALL store them in the VariantQuestion table with original_question_id, expires_at=now()+90days, and source=ai_generated

#### Scenario: Cross-student variant reuse within 90 days
- **WHEN** student B requests variants for the same original question that student A previously generated variants for, and the existing variants are less than 90 days old
- **THEN** the system SHALL return the existing variants without calling LLM

#### Scenario: Variants excluded from analytics
- **WHEN** computing class-level error rates, difficulty calibration, or any statistical report
- **THEN** the system SHALL NOT include VariantQuestion records — only Question table records participate in analytics

#### Scenario: Insufficient LLM output triggers retry
- **WHEN** the LLM returns fewer than 3 valid variant questions
- **THEN** the system SHALL make one additional LLM call to supplement, up to a maximum of 2 total calls; if still fewer than 3, return whatever is available

### Requirement: Ephemeral training sessions

The system SHALL create in-memory training sessions that group variant questions for a student to answer, with submission returning per-question results and a graded learning suggestion.

#### Scenario: Training session creation
- **WHEN** a student confirms they want to start training with 3 variant questions
- **THEN** the system SHALL create an ephemeral training session (not persisted to database) with a unique session_id and the 3 questions

#### Scenario: Training submission with learning suggestions
- **WHEN** a student submits answers for all questions in a training session with 90% accuracy
- **THEN** the system SHALL return per-question correctness, overall accuracy, and a learning suggestion: "已掌握，可尝试更高难度"

#### Scenario: Low accuracy triggers remedial suggestion
- **WHEN** a student submits with accuracy below 50%
- **THEN** the system SHALL return the suggestion: "需要先复习知识点再练习"

#### Scenario: Medium accuracy suggests persistence
- **WHEN** a student submits with accuracy between 70% and 90%
- **THEN** the system SHALL return the suggestion: "做得不错，继续练习可达完美"

#### Scenario: Accuracy between 50% and 70% suggests review
- **WHEN** a student submits with accuracy between 50% and 70%
- **THEN** the system SHALL return the suggestion: "还需努力，查看解析理解思路"

### Requirement: Knowledge point filter for wrong questions

The system SHALL allow filtering wrong questions by knowledge point tag.

#### Scenario: Filter by knowledge point
- **WHEN** a client requests wrong questions with knowledge_point_filter="氧化还原反应"
- **THEN** the system SHALL return only wrong questions tagged with that knowledge point

#### Scenario: List available knowledge points with wrong questions
- **WHEN** a client requests the set of knowledge points that have at least one wrong question
- **THEN** the system SHALL return the distinct knowledge point names and their error counts

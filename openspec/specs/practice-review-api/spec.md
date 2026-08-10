## Purpose

Exposes REST API endpoints for students to list and complete practice tasks, submit answers, track practice effectiveness, list due review tasks, submit review results, browse wrong questions, generate variant questions, run training sessions, and mark questions as mastered.

## ADDED Requirements

### Requirement: Practice task list endpoint

The system SHALL provide an endpoint that returns all practice tasks for a student, grouped by status (pending/completed).

#### Scenario: List practice tasks with pending/completed split
- **WHEN** a student requests GET /api/practice/student/{uid}/tasks
- **THEN** the system SHALL return tasks grouped into pending and completed sections, each task containing practice_id, title, knowledge_points, difficulty, status, question_count, and optional deadline

#### Scenario: Empty practice task list
- **WHEN** a student has no practice tasks
- **THEN** the system SHALL return an empty tasks array with pending_count=0 and completed_count=0

### Requirement: Practice submission endpoint

The system SHALL accept student answers for a practice session, return per-question correctness and overall accuracy, and trigger ReviewTask sync for incorrect answers.

#### Scenario: Submit practice answers
- **WHEN** a student submits answers for practice_id P with an array of {question_id, selected_option} objects
- **THEN** the system SHALL create StudentAnswer records, compute score, accuracy, and per-question results (q_number, is_correct, correct_answer, analysis), and return them

#### Scenario: Incorrect answers trigger ReviewTask creation
- **WHEN** submission results include incorrect answers
- **THEN** the system SHALL trigger automatic ReviewTask sync for each incorrectly answered question (asynchronously)

### Requirement: Practice effect tracking endpoint

The system SHALL compare the student's two most recent practice sessions and return the accuracy improvement rate.

#### Scenario: Improvement rate computed from last two sessions
- **WHEN** a teacher requests GET /api/practice/effect/{student_id}
- **THEN** the system SHALL return student_id, student_name, and an improvement object with before_practice_date, before_accuracy, after_practice_date, after_accuracy, and improvement_rate (after_accuracy - before_accuracy)

#### Scenario: Only one practice session available
- **WHEN** a student has only one completed practice session
- **THEN** the system SHALL return the single session as "after" and null values for "before" fields with a note indicating insufficient data

### Requirement: Due review task list endpoint

The system SHALL return ReviewTask records that are due for review (next_review_date <= now(), status=pending or overdue), ordered by next_review_date ascending.

#### Scenario: Due review tasks with question content
- **WHEN** a student requests GET /api/review/student/{id}/due
- **THEN** the system SHALL return tasks including task_id, question_id, question_content, review_level, next_review_at, consecutive_correct count, and counts for due and overdue tasks

#### Scenario: Overdue tasks appear first
- **WHEN** tasks have varying next_review_at values, some in the past
- **THEN** the system SHALL order by next_review_at ASC so the most overdue tasks appear first

### Requirement: Review submission endpoint

The system SHALL accept a review result for a specific ReviewTask and return the updated level and next review date.

#### Scenario: Submit correct review answer
- **WHEN** a student submits POST /api/review/submit with task_id, student_id, is_correct=true
- **THEN** the system SHALL apply the upgrade/downgrade rules and return {success: true, new_review_level, next_review_at}

#### Scenario: Review arrives at mastery
- **WHEN** a review submission results in level reaching 5
- **THEN** the system SHALL return next_review_at=null and status=completed

### Requirement: Wrong question list endpoint

The system SHALL return paginated wrong questions for a student via GET /api/review/wrong/list.

#### Scenario: Wrong question list with full details
- **WHEN** a student requests GET /api/review/wrong/list with student_id and optional limit
- **THEN** the system SHALL return questions array with question_id, content, options, answer, analysis, knowledge_points, difficulty, wrong_count, your_answer, and total count

### Requirement: Mastery marking endpoint

The system SHALL mark a specific question as mastered for a student via POST /api/review/wrong/{question_id}/master.

#### Scenario: Mark question as mastered
- **WHEN** a student marks question Q as mastered
- **THEN** the system SHALL set the corresponding ReviewTask to completed (level=5) or create one if absent, and return success

### Requirement: Variant generation endpoint

The system SHALL generate variant questions for a given original question via POST /api/review/wrong-topic/variant/generate.

#### Scenario: Generate variants for a wrong question
- **WHEN** a student requests variants for question Q with count=3
- **THEN** the system SHALL return up to 3 variant questions (from VariantQuestion cache or freshly generated by LLM) with question content, options, and answer

### Requirement: Training session endpoints

The system SHALL support ephemeral training session creation and submission via POST /api/review/wrong-topic/training/create and /submit.

#### Scenario: Create training session
- **WHEN** a student creates a training session with a list of question_ids
- **THEN** the system SHALL return a session_id and the full question list

#### Scenario: Submit training session
- **WHEN** a student submits answers for a training session
- **THEN** the system SHALL return per-question correctness, overall accuracy, and a graded learning suggestion based on accuracy thresholds (>=90%, >=70%, >=50%, <50%)

### Requirement: Authorization and data isolation

The system SHALL enforce that students can only access their own practice, review, and wrong question data. When a teacher assigns a practice via POST /api/v1/practice/assign, the system SHALL automatically create a notification for the assigned student.

#### Scenario: Student can only see own data
- **WHEN** student A requests practice tasks
- **THEN** the system SHALL only return records where student_id matches student A

#### Scenario: Teacher can see class-level practice statistics
- **WHEN** a teacher requests practice effect data
- **THEN** the system SHALL verify the teacher teaches the class the student belongs to before returning data

#### Scenario: Practice assignment triggers student notification
- **WHEN** a teacher successfully assigns a practice session to a student via POST /api/v1/practice/assign
- **THEN** the system SHALL create a notification for the student with type "practice_assigned", including the practice_id as related_id; notification write failure SHALL NOT block the assignment

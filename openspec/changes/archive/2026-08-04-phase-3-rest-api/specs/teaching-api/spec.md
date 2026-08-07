## Purpose

Provides REST API endpoints for teaching operations — exam records, questions, student answers, practice submission, and LLM grading triggers — forming the core instructional workflow.

## ADDED Requirements

### Requirement: Exam record CRUD
The system SHALL support creating, listing, and reading exam records. Exams are scoped to classes.

#### Scenario: Teacher creates an exam record
- **WHEN** a teacher sends POST /api/v1/exams with class_id, exam_type, exam_date, name
- **THEN** the system creates the exam record and returns ExamRead with HTTP 201

#### Scenario: Teacher lists exams for a class
- **WHEN** a teacher sends GET /api/v1/classes/{class_id}/exams
- **THEN** the system returns paginated exams with participant_count and avg_score, newest first

#### Scenario: Get exam detail with error stats
- **WHEN** a teacher sends GET /api/v1/exams/{id}
- **THEN** the system returns the exam with full error_stats breakdown by knowledge point

### Requirement: Question CRUD
The system SHALL support creating, listing, updating, and deleting Question entities with filtering by difficulty, source, and knowledge point tags.

#### Scenario: Teacher creates a question
- **WHEN** a teacher sends POST /api/v1/questions with content, question_type, answer, difficulty, knowledge_point_tags
- **THEN** the system creates the question and returns QuestionRead with HTTP 201

#### Scenario: Filter questions by knowledge point
- **WHEN** a user sends GET /api/v1/questions?knowledge_point=盐类水解&difficulty=medium
- **THEN** the system returns only matching questions

#### Scenario: AI question generation
- **WHEN** a teacher sends POST /api/v1/questions/generate with knowledge_points, difficulty, count, question_type
- **THEN** the system invokes the LLM generation pipeline and returns generated questions (stub: returns empty list with "not implemented" warning until LLM pipeline is built)

### Requirement: Student answer recording and retrieval
The system SHALL record student answers to questions and allow retrieval by student, exam, or question.

#### Scenario: Student submits a practice answer
- **WHEN** a student sends POST /api/v1/practice/submit with student_id, question_id, answer_content
- **THEN** the system records the answer, auto-grades against the question answer, and returns StudentAnswerRead

#### Scenario: Teacher views answers for an exam
- **WHEN** a teacher sends GET /api/v1/exams/{exam_id}/answers
- **THEN** the system returns all student answers for that exam, grouped by student

#### Scenario: Teacher views a student's answer history
- **WHEN** a teacher sends GET /api/v1/students/{student_id}/answers?limit=50
- **THEN** the system returns the student's most recent answers with barrier_type labels

### Requirement: Grading trigger
The system SHALL provide an endpoint to trigger LLM grading for all ungraded submissions in an exam.

#### Scenario: Teacher triggers batch grading
- **WHEN** a teacher sends POST /api/v1/grading/run with exam_id and class_id
- **THEN** the system returns a grading_job_id and the total_submissions count (stub: actual LLM grading pipeline implemented in a later phase)

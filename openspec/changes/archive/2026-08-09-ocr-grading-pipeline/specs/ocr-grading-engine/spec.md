## Purpose

Performs grading of student answers extracted from OCR against correct answers obtained from one of three sources, using either Baidu's correct_edu API or LLM-based semantic comparison as a fallback.

## ADDED Requirements

### Requirement: Answer source resolution with three-mode priority

The system SHALL resolve correct answers for grading in priority order: (1) exam paper matching — query ExamPaper→ExamPaperQuestion→Question.answer when exam_paper_id is provided; (2) teacher input — use answers provided inline by the teacher; (3) LLM auto-judgment — mark all questions as needing teacher review when neither source is available.

#### Scenario: Exam paper matching resolves answers
- **WHEN** the teacher provides exam_paper_id=15 for grading
- **THEN** the system SHALL query all ExamPaperQuestion records for that paper, sorted by sort_order, and build an AnswerKey from each Question.answer

#### Scenario: Teacher-provided answers override exam paper
- **WHEN** the teacher provides both exam_paper_id and explicit answers
- **THEN** the system SHALL use the teacher-provided answers (priority 2 overrides priority 1)

#### Scenario: LLM auto-judgment mode
- **WHEN** neither exam_paper_id nor teacher answers are provided
- **THEN** the system SHALL set all correct_answer values to "AUTO", mark all questions with needs_review=true, and flag source_mode="llm_auto"

### Requirement: Dual-path grading engine

The system SHALL execute grading via Baidu correct_edu API (asynchronous: create task → poll every 3 seconds for up to 120 seconds) and fall back to LLM semantic grading (synchronous: parse answers from OCR text, compare with correct answers) when correct_edu is unavailable.

#### Scenario: correct_edu successfully grades an answer sheet
- **WHEN** correct_edu API is available and an image is submitted with an answer key
- **THEN** the system SHALL create a grading task via the Baidu API, poll for results every 3 seconds, and return a GradingResult with engine="baidu_correct_edu"

#### Scenario: correct_edu polling timeout
- **WHEN** correct_edu task status does not reach "done" within 120 seconds
- **THEN** the system SHALL raise a GradingTimeoutError and fall back to LLM semantic grading

#### Scenario: correct_edu unavailable triggers LLM fallback
- **WHEN** correct_edu API call fails (network error, quota exhausted, or API error)
- **THEN** the system SHALL degrade to LLM semantic grading and set degraded=true in the result

#### Scenario: correctResult code mapping
- **WHEN** correct_edu returns per-question results
- **THEN** correctResult=0 SHALL map to needs_review=true (unprocessed), correctResult=1 to is_correct=true, correctResult=2 to is_correct=false, and correctResult=3 to is_correct=false with reason "未作答"

### Requirement: Answer parsing from OCR text

The system SHALL parse structured student answers from OCR raw text using regex for choice questions (matching patterns like "1. C", "2. B") and a single LLM call for non-choice questions (fill-in-blank, calculation, experiment inquiry).

#### Scenario: Choice question answer extraction by regex
- **WHEN** OCR text contains "1. C  2. B  3. A"
- **THEN** the system SHALL extract [{q_number:1, student_answer:"C", question_type:"choice"}, {q_number:2, student_answer:"B"}, {q_number:3, student_answer:"A"}]

#### Scenario: Non-choice question extraction by LLM
- **WHEN** OCR text contains fill-in-blank answers like "16. H₂O  17. Fe³⁺"
- **THEN** the system SHALL use a single LLM call to extract all remaining answers after regex has handled choice questions

#### Scenario: Partial extraction when parsing incomplete
- **WHEN** the number of extracted answers is less than the expected question_count
- **THEN** the system SHALL mark the result is_partial=true

### Requirement: Chemical equivalence judgment for non-choice answers

The system SHALL compare non-choice student answers against correct answers using LLM-based semantic equivalence, recognizing chemical equivalences such as subscript normalization (H2O ≡ H₂O), arrow equivalence (→ ≡ =), and spacing/order normalization, rather than simple string matching.

#### Scenario: Chemical formula with subscript variants
- **WHEN** student_answer="H2O" and correct_answer="H₂O"
- **THEN** the LLM SHALL judge them as chemically equivalent (is_correct=true)

#### Scenario: Chemical equation with arrow variants
- **WHEN** student_answer="2H₂+O₂=2H₂O" and correct_answer="2H₂ + O₂ → 2H₂O"
- **THEN** the LLM SHALL judge them as chemically equivalent (is_correct=true)

#### Scenario: Non-equivalent answers correctly rejected
- **WHEN** student_answer="氧化反应" and correct_answer="氧化还原反应"
- **THEN** the LLM SHALL judge them as NOT equivalent (is_correct=false)

### Requirement: Simple string comparison for choice questions

The system SHALL compare choice question answers using case-insensitive trimmed string equality without invoking LLM.

#### Scenario: Correct choice answer match
- **WHEN** student_answer=" c " and correct_answer="C"
- **THEN** the comparison SHALL return is_correct=true after trimming and uppercasing both

#### Scenario: Incorrect choice answer
- **WHEN** student_answer="B" and correct_answer="D"
- **THEN** the comparison SHALL return is_correct=false

#### Scenario: Empty student answer
- **WHEN** student_answer is empty, null, or whitespace-only
- **THEN** the comparison SHALL return is_correct=false

#### Scenario: AUTO-mode answer
- **WHEN** correct_answer equals "AUTO" (LLM auto-judgment mode)
- **THEN** the comparison SHALL return is_correct=false and set reason="待教师确认"

### Requirement: Structured grading result

The system SHALL produce a GradingResult containing: task_id, student_id_raw, student_name_raw, score (float), total (int), engine (string), degraded (boolean), a questions array (each with q_number, student_answer, correct_answer, is_correct, reason, score, confidence, needs_review), and a summary object (correct_count, wrong_count, unanswered_count, needs_review_count).

#### Scenario: Complete grading result with all question types
- **WHEN** grading completes for a 10-question answer sheet (6 choice + 4 fill-in-blank)
- **THEN** the GradingResult SHALL contain 10 QuestionGrading entries with per-question scores, and the summary SHALL total correct_count + wrong_count = 10

#### Scenario: Low-confidence results marked for review
- **WHEN** any question has correct_edu correctResult=0 or LLM comparison confidence < 0.7
- **THEN** the question SHALL have needs_review=true

### Requirement: Grading API endpoints

The system SHALL expose POST /api/v1/grading/run to trigger grading for one or more OCR tasks, GET /api/v1/grading/results/{batch_id} to query grading results, and POST /api/v1/grading/save to confirm and persist grading results.

#### Scenario: Trigger grading for completed OCR tasks
- **WHEN** the teacher POSTs to /grading/run with task_ids and an optional exam_paper_id
- **THEN** the system SHALL resolve the answer source, execute grading for each task, store grading_result on each OCRTask, and return the batch grading summary

#### Scenario: Query grading results by batch
- **WHEN** the teacher GETs /grading/results/{batch_id}
- **THEN** the system SHALL return all task grading results for that UploadSession batch

#### Scenario: Student without permission cannot trigger grading
- **WHEN** a student attempts to POST to /grading/run
- **THEN** the system SHALL return HTTP 403

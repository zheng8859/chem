## Purpose

Provides REST API endpoints for the OCR answer-sheet grading pipeline — upload session management, OCR task tracking, and student submission retrieval.

## ADDED Requirements

### Requirement: Upload session management
The system SHALL support creating and tracking batch upload sessions for answer sheet OCR processing.

#### Scenario: Teacher creates a batch upload session
- **WHEN** a teacher sends POST /api/v1/ocr/sessions with teacher_id, class_id, exam_name
- **THEN** the system creates an UploadSession with status=pending and returns the session with batch_id

#### Scenario: List upload sessions
- **WHEN** a teacher sends GET /api/v1/ocr/sessions?teacher_id={id}
- **THEN** the system returns paginated upload sessions for that teacher, newest first

#### Scenario: Get session status
- **WHEN** a teacher sends GET /api/v1/ocr/sessions/{session_id}
- **THEN** the system returns the session with current status and aggregated task stats (pending/processing/done/failed counts)

### Requirement: OCR task tracking
The system SHALL provide endpoints to list and inspect individual OCR tasks within an upload session.

#### Scenario: List tasks in a session
- **WHEN** a teacher sends GET /api/v1/ocr/sessions/{session_id}/tasks
- **THEN** the system returns all OCR tasks in that session with their status and results

#### Scenario: Get OCR task detail
- **WHEN** a teacher sends GET /api/v1/ocr/tasks/{task_id}
- **THEN** the system returns the OCR task with ocr_raw_result and grading_result if completed

### Requirement: Student submission retrieval
The system SHALL allow listing and reading student submissions (graded answer sheets).

#### Scenario: List submissions by exam
- **WHEN** a teacher sends GET /api/v1/ocr/submissions?exam_record_id={id}
- **THEN** the system returns all StudentSubmissions for that exam with scores

#### Scenario: Get submission detail
- **WHEN** a teacher sends GET /api/v1/ocr/submissions/{id}
- **THEN** the system returns the submission with original_image path, graded_image path, answer_list, and total_score

### Requirement: Batch upload initiation
The system SHALL provide an endpoint to initiate batch OCR processing for multiple answer sheets.

#### Scenario: Teacher triggers batch OCR
- **WHEN** a teacher sends POST /api/v1/ocr/tasks/batch with teacher_id, class_id, exam_name
- **THEN** the system creates an UploadSession and returns a batch_id with the number of OCR tasks created (stub: actual OCR processing triggered via APScheduler in a later phase)

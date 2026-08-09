## ADDED Requirements

### Requirement: ExamRecord auto-creation from OCR upload

The system SHALL automatically create an ExamRecord with status='grading' and exam_type='practice' when a teacher uploads answer sheets via the OCR batch upload endpoint, associating it with the specified class_id, so that diagnosis and statistics processing have an exam_record_id to reference throughout the OCR pipeline.

#### Scenario: ExamRecord created on batch upload
- **WHEN** a teacher uploads answer sheets with class_id=3 via POST /api/v1/ocr/tasks/batch
- **THEN** the system SHALL create ExamRecord(class_id=3, exam_type='practice', status='grading', exam_date=today) in the same transaction as the UploadSession

#### Scenario: ExamRecord transitions to completed after statistics
- **WHEN** the async post-save pipeline completes statistics computation for the exam
- **THEN** the ExamRecord SHALL transition from grading to completed, and participant_count, avg_score, and error_stats SHALL be populated

#### Scenario: ExamRecord name derived from upload context
- **WHEN** the teacher provides exam_name="7月月考" during upload
- **THEN** the created ExamRecord SHALL have name="7月月考"

### Requirement: Exam grading state entry from OCR pipeline

The system SHALL accept ExamRecord creation directly into the grading state when initiated from the OCR upload pipeline, in addition to the existing pending→in_progress→grading transition from standard exam assignment.

#### Scenario: OCR-created ExamRecord starts in grading
- **WHEN** an ExamRecord is created by the OCR upload pipeline
- **THEN** it SHALL start with status='grading' (skipping pending and in_progress, as students are not taking the exam online)

#### Scenario: Standard exam flow unchanged
- **WHEN** a teacher assigns an ExamPaper to a class through the standard exam management flow
- **THEN** the ExamRecord SHALL follow the existing pending→in_progress→grading→completed lifecycle without modification

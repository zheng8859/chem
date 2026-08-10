## Purpose

Defines the two-layer exam lifecycle: reusable ExamPaper templates with scoring and ExamRecord execution instances with independent state machines.

## ADDED Requirements

### Requirement: ExamPaper as reusable template

The system SHALL model exam papers as reusable templates containing an ordered, scored set of questions, owned by a teacher.

#### Scenario: Teacher creates exam paper
- **WHEN** a teacher creates a paper "高一期中化学模拟卷" with 20 questions and a total score of 100
- **THEN** the system SHALL create an ExamPaper with status=draft, containing 20 question associations each with a score value

#### Scenario: Same paper used for multiple classes
- **WHEN** a teacher assigns the same published ExamPaper to 高一(1)班 and 高一(3)班
- **THEN** the system SHALL create two separate ExamRecord instances, each referencing the same ExamPaper

#### Scenario: Paper scoring sums to total
- **WHEN** a teacher sets per-question scores on an ExamPaper
- **THEN** the sum of all question scores SHALL equal the ExamPaper.total_score

### Requirement: ExamPaper state machine

The system SHALL manage ExamPaper through three states: draft → published → archived.

#### Scenario: Draft paper is editable
- **WHEN** an ExamPaper is in draft status
- **THEN** the teacher SHALL be able to add, remove, reorder, or re-score questions

#### Scenario: Published paper is locked
- **WHEN** an ExamPaper transitions to published
- **THEN** the question list and scores SHALL become immutable

#### Scenario: Archived paper is hidden from active selection
- **WHEN** an ExamPaper is archived
- **THEN** it SHALL NOT appear in the default paper list for creating new ExamRecords

### Requirement: ExamRecord lifecycle

The system SHALL manage ExamRecord through the states: pending → in_progress → grading → completed → archived, with a cancelled terminal state reachable from any active state.

#### Scenario: Record starts pending
- **WHEN** an ExamRecord is created for a class with an ExamPaper
- **THEN** it SHALL have status=pending (teacher has assigned but students haven't started)

#### Scenario: Students begin the exam
- **WHEN** the first student in the class starts answering
- **THEN** the ExamRecord SHALL transition to in_progress

#### Scenario: Exam moves to grading
- **WHEN** the exam time expires or the teacher closes submissions
- **THEN** the ExamRecord SHALL transition to grading

#### Scenario: Teacher cancels exam
- **WHEN** a teacher cancels an ExamRecord in pending, in_progress, or grading status
- **THEN** the ExamRecord SHALL transition to cancelled

#### Scenario: Grading completes
- **WHEN** all student answers have been graded
- **THEN** the ExamRecord SHALL transition to completed

### Requirement: Per-question scoring on exam paper

The system SHALL store the score value for each question within the paper's question association, since the same question may carry different weights on different papers.

#### Scenario: Question has different scores on different papers
- **WHEN** question #42 (a redox calculation problem) is included in a midterm paper and a final paper
- **THEN** it SHALL be possible to assign score=5 on the midterm paper and score=10 on the final paper

#### Scenario: Total score computed from question scores
- **WHEN** a student's graded answers are totaled
- **THEN** the system SHALL sum the per-question scores of correctly answered questions to compute the student's total score

### Requirement: 考试删除安全策略

`DELETE /exams/{id}` SHALL 校验考试状态。`in_progress` 和 `grading` 状态的考试 SHALL 禁止删除，返回 403 Forbidden。`pending` 和 `completed` 状态的考试 SHALL 允许删除。

#### Scenario: 删除进行中的考试被拒绝
- **WHEN** 教师尝试删除 status=`in_progress` 的考试
- **THEN** 返回 403，detail 包含"进行中或批改中的考试不可删除"

#### Scenario: 删除草稿考试成功
- **WHEN** 教师删除 status=`pending` 的考试
- **THEN** 考试记录、题目关联、答题记录被级联删除，返回 204

#### Scenario: 删除已完成考试成功
- **WHEN** 教师删除 status=`completed` 的考试
- **THEN** 考试记录被删除，返回 204

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

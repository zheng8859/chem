## Purpose

Computes post-exam class-level statistics and generates an LLM-powered natural language analysis report after grading and diagnosis complete, feeding results into the existing learning panel.

## ADDED Requirements

### Requirement: Post-grading exam statistics computation

The system SHALL compute class-level statistics after all grading results for an exam are saved, including participant_count, avg_score, score distribution (bucketed by 10-point intervals), per-question error rate, and barrier type distribution, and SHALL persist these to ExamRecord.error_stats.

#### Scenario: Statistics computed after grading save
- **WHEN** grading results are saved for all tasks in an exam and diagnosis completes
- **THEN** the system SHALL compute avg_score from all student scores, count participants, and write the result to ExamRecord.error_stats

#### Scenario: Score distribution bucketed by 10-point intervals
- **WHEN** 45 students have scores ranging from 45 to 98
- **THEN** the system SHALL bucket scores into 0-59, 60-69, 70-79, 80-89, 90-100 intervals

#### Scenario: Per-question error rate computed
- **WHEN** statistics are computed for a 20-question exam
- **THEN** for each question, error_rate SHALL equal (wrong_count / total_answers) for that question

#### Scenario: Barrier type distribution aggregated
- **WHEN** diagnosis has assigned barrier types to wrong answers
- **THEN** the distribution SHALL count concept, reading, and expression barrier types across all students

### Requirement: LLM class analysis report generation

The system SHALL generate a natural language class analysis report via LLM call, covering overall performance summary, weak knowledge point analysis, learning barrier diagnosis, and actionable improvement suggestions, in 300-500 words of professional Chinese prose.

#### Scenario: Report generated after statistics
- **WHEN** exam statistics computation completes
- **THEN** the system SHALL construct a structured prompt with exam data and call the LLM router to generate a report

#### Scenario: Report includes weak knowledge point analysis
- **WHEN** per-question error rate shows question #5 (氧化还原) has error_rate > 0.3
- **THEN** the report SHALL identify 氧化还原反应 as a weak area and provide pedagogical suggestions

#### Scenario: Report includes barrier-type analysis
- **WHEN** barrier distribution shows concept=15, reading=8, expression=5
- **THEN** the report SHALL note concept understanding as the primary barrier and recommend targeted concept review exercises

### Requirement: Async post-save processing pipeline

The system SHALL execute the post-save pipeline (diagnosis → statistics → report) asynchronously via asyncio.create_task after grading save completes, without blocking the HTTP response to the teacher.

#### Scenario: Save response returns immediately
- **WHEN** the teacher confirms grading save via POST /grading/save
- **THEN** the HTTP response SHALL return within 2 seconds with saved_count and diagnosis_triggered=true, while the pipeline runs in background

#### Scenario: Pipeline step failure does not block subsequent steps
- **WHEN** the diagnosis step fails in the async pipeline
- **THEN** the statistics step SHALL still execute, using whatever diagnosis data is available at that point

### Requirement: Statistics API endpoint

The system SHALL expose POST /api/v1/ocr/stats to trigger on-demand class statistics computation and report generation for a given exam_record_id.

#### Scenario: On-demand statistics computation
- **WHEN** a teacher POSTs to /ocr/stats with {"exam_record_id": 15}
- **THEN** the system SHALL compute and persist statistics, generate a report, and return both

### Requirement: Student answer double-write on save

The system SHALL write both StudentSubmission (whole-answer-sheet snapshot with answer_list JSON and total_score) and StudentAnswer (per-question records with answer_content, is_correct, and FK to Question and Student) when saving grading results.

#### Scenario: Both tables written on save
- **WHEN** grading results for a 10-question answer sheet are saved
- **THEN** the system SHALL INSERT one StudentSubmission record AND 10 StudentAnswer records in a single transaction

#### Scenario: Unknown student ID skipped with reason
- **WHEN** a task's student_id_raw is "unknown" or does not match any Student record
- **THEN** the system SHALL skip that task's answers, increment skipped_count, and record the reason "student_not_found"

#### Scenario: Already-confirmed task is idempotent
- **WHEN** the teacher attempts to save results for a task where confirmed=true
- **THEN** the system SHALL skip that task without error (idempotent)

### Requirement: ExamRecord auto-creation on upload

The system SHALL automatically create an ExamRecord with status='grading' when a batch upload completes, linked to the teacher's specified class, so that diagnosis and statistics have an exam_record_id to reference.

#### Scenario: ExamRecord created on upload
- **WHEN** a teacher uploads answer sheets with class_id=3
- **THEN** the system SHALL create ExamRecord(class_id=3, status='grading', exam_type='practice') and associate it with the UploadSession

#### Scenario: ExamRecord transitions to completed after statistics
- **WHEN** post-grading statistics computation completes successfully
- **THEN** the ExamRecord status SHALL transition from grading to completed and participant_count, avg_score, error_stats SHALL be populated

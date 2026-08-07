## Purpose

Automatically creates a daily 10-question practice for every approved student at 08:00 UTC, selecting knowledge points based on each student's dominant barrier type, with idempotent per-day deduplication and parent notification for overdue review tasks.

## ADDED Requirements

### Requirement: Scheduled daily practice creation

The system SHALL run a cron job at 08:00 UTC daily that creates a practice record for every student whose account is in approved status.

#### Scenario: Daily practice created for all approved students
- **WHEN** the scheduler fires at 08:00 UTC
- **THEN** the system SHALL create an ExamRecord with type=practice, exam_date=today for each approved student

#### Scenario: Idempotent per-day deduplication
- **WHEN** the scheduler fires and a practice record already exists for (student_id, date=today, type=practice)
- **THEN** the system SHALL NOT create a duplicate — it SHALL return the existing record

### Requirement: Barrier-type-based knowledge point selection

The system SHALL select practice knowledge points based on the student's dominant barrier type from their barrier_type JSON field.

#### Scenario: Concept barrier student gets foundational topics
- **WHEN** a student's dominant barrier is concept (score > 0.4)
- **THEN** the system SHALL select knowledge points focused on foundational chemistry topics (e.g., "盐类水解", "电离平衡", "水解平衡")

#### Scenario: Reading barrier student gets experimental design topics
- **WHEN** a student's dominant barrier is reading (score > 0.4)
- **THEN** the system SHALL select knowledge points focused on experimental design and question analysis (e.g., "化学实验设计", "题干分析技巧")

#### Scenario: Expression barrier student gets notation topics
- **WHEN** a student's dominant barrier is expression (score > 0.4)
- **THEN** the system SHALL select knowledge points focused on chemical notation and equation writing (e.g., "化学用语规范", "表述练习")

#### Scenario: No clear dominant barrier falls back to defaults
- **WHEN** a student's barrier_type is missing or no single barrier exceeds 0.4
- **THEN** the system SHALL select default knowledge points (e.g., "盐类水解", "电离平衡", "氧化还原反应")

### Requirement: Question sourcing for daily practice

The system SHALL fill the daily practice with 10 questions, prioritizing the existing Question bank and supplementing with LLM generation only when the bank has insufficient matching questions.

#### Scenario: Bank has sufficient questions
- **WHEN** the Question table has 10 or more questions matching the target knowledge points, difficulty=medium, and audit_status=passed
- **THEN** the system SHALL randomly select 10 from the bank without calling LLM

#### Scenario: Bank insufficient, LLM supplements
- **WHEN** the Question table has only 6 matching questions
- **THEN** the system SHALL select all 6 bank questions and call LLM to generate the remaining 4

### Requirement: Parent notification for overdue review tasks

The system SHALL check for overdue ReviewTask records during the daily scheduler run and notify bound parents.

#### Scenario: Parent notified of overdue reviews
- **WHEN** a student has N overdue ReviewTask records (status=pending or overdue, next_review_date < now()) AND a parent is actively bound to the student
- **THEN** the system SHALL create a ParentNotification with type=reminder containing the count N

#### Scenario: No overdue tasks creates no notification
- **WHEN** a student has zero overdue ReviewTask records
- **THEN** the system SHALL NOT create a review reminder notification

### Requirement: Practice record creation with question placeholder

The system SHALL create the daily practice ExamRecord with question metadata stored in the record's JSON field, deferring actual question assignment to when the student opens the practice.

#### Scenario: ExamRecord created with question metadata
- **WHEN** the daily scheduler creates a practice
- **THEN** the system SHALL store the target knowledge points, question count (10), difficulty (medium), and target barrier type in the ExamRecord's question_stats JSON field

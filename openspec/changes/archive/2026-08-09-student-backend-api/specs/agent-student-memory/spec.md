## Purpose

Enables the Agent to personalize student conversations by writing diagnosis history to LangGraph Store and injecting student profile data (barrier profile, learning plan, practice stats) into the System Message of each student conversation.

## ADDED Requirements

### Requirement: Diagnosis history write to LangGraph Store

The system SHALL write student diagnosis results to the LangGraph AsyncSqliteStore after each batch of LLM diagnosis completes, using a best-effort strategy that does not block the diagnosis pipeline.

#### Scenario: Diagnosis results written to Store
- **WHEN** POST /api/v1/diagnosis/run-llm completes a batch diagnosis for a student
- **THEN** the system SHALL attempt to write the student's updated barrier_profile and last_diagnosis_date to LangGraph Store keyed by student_id; failure SHALL be logged but SHALL NOT raise an exception

#### Scenario: Store write failure is non-blocking
- **WHEN** writing to LangGraph Store fails (e.g., database locked)
- **THEN** the diagnosis pipeline SHALL complete successfully, and the error SHALL be logged

### Requirement: Learning plan write to LangGraph Store

The system SHALL write the student's active learning plan to LangGraph Store when a teacher creates or updates a learning plan, using a best-effort strategy.

#### Scenario: Learning plan written to Store
- **WHEN** a teacher creates or updates a learning plan for a student
- **THEN** the system SHALL attempt to write the plan summary (title, task count, days) to LangGraph Store keyed by student_id

### Requirement: Student profile injection into Agent System Message

The system SHALL, when the current persona is "student", prepend a student profile section to the Agent's System Message containing the student's name, class, barrier profile, weak knowledge points, active learning plan summary, and practice statistics.

#### Scenario: Student profile in System Message
- **WHEN** a student initiates an Agent conversation
- **THEN** the Agent's System Message SHALL include a structured block with student_name, class_name, barrier_profile (dominant_type and rates), weak_kps (top 5), active_plan_summary (title and total tasks), and practice_stats (total_practices, overall_accuracy)

#### Scenario: Student has no data
- **WHEN** a student has no diagnosis history, no learning plan, and no practice history
- **THEN** the student profile section SHALL indicate that each data category is not yet available, using placeholder text such as "暂无诊断数据"

#### Scenario: Non-student persona unaffected
- **WHEN** the Agent persona is teacher, tutor, or parent
- **THEN** the System Message SHALL NOT include the student profile section

### Requirement: Agent memory_read tool reads from Store

The system SHALL update the memory_student_get Agent tool to read diagnosis history and learning plan data from LangGraph Store, returning the most recent 5 diagnosis records and the current active learning plan.

#### Scenario: memory_student_get returns Store data
- **WHEN** the Agent calls memory_student_get for a student_id with Store data
- **THEN** the tool SHALL return diagnosis_history (up to 5 records, each with barrier_type, distribution, and timestamp) and active_learning_plan (title, task count, days)

#### Scenario: memory_student_get with empty Store
- **WHEN** the Agent calls memory_student_get for a student with no Store data
- **THEN** the tool SHALL return empty diagnosis_history and null active_learning_plan

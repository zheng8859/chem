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

### Requirement: LLM summary in context trimming

The system SHALL invoke LLM summarization when context trimming discards 10 or more messages, compressing the discarded messages into ≤ 200 Chinese characters and prepending the summary to the retained message list. The summary SHALL be cached per checkpoint to avoid re-summarizing the same discarded messages on subsequent Agent invocations.

#### Scenario: Summary generated and injected
- **WHEN** context trimming discards 12 messages
- **THEN** the system SHALL call LLM to generate a ≤ 200 character Chinese summary of the discarded messages and prepend it as a System Message to the output

#### Scenario: Summary not regenerated for same checkpoint
- **WHEN** the same conversation is invoked again without new messages being discarded
- **THEN** the system SHALL reuse the previously cached summary rather than calling LLM again

### Requirement: Long-term memory integration into tool chain

The system SHALL integrate the LangGraph AsyncSqliteStore into the Agent tool chain, enabling memory_student_get to read diagnosis history and learning plans from the Store, and memory_teacher_get to read teacher preferences. The Store connection SHALL be initialized at application startup and injected into the Agent dependency container.

#### Scenario: memory_student_get reads from Store
- **WHEN** the Agent calls memory_student_get for a student with 5 diagnosis records in the Store
- **THEN** the tool SHALL return all 5 records with barrier_type, distribution, and timestamp

#### Scenario: memory_teacher_get reads teacher preferences
- **WHEN** the Agent calls memory_teacher_get for a teacher with stored preferences
- **THEN** the tool SHALL return teaching_style, difficulty_preference, and class_configuration

#### Scenario: Store read failure returns empty
- **WHEN** reading from Store fails (e.g., database locked)
- **THEN** memory_student_get SHALL return empty diagnosis_history and null active_learning_plan without raising an exception

### Requirement: Checkpoint persistence configuration

The system SHALL configure LangGraph AsyncSqliteSaver with a dedicated checkpoint database file (separate from the main application database), initialized at application startup and shared across all Agent invocations as a process-level singleton.

#### Scenario: Checkpoint survives service restart
- **WHEN** the FastAPI service restarts
- **THEN** all previously saved conversation checkpoints SHALL be recoverable from the checkpoint database

#### Scenario: Conversation isolation by thread_id
- **WHEN** two different thread_ids are used for Agent conversations
- **THEN** messages from one thread SHALL NOT appear in the other thread's history

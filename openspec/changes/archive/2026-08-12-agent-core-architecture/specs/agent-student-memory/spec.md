## ADDED Requirements

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

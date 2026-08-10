## MODIFIED Requirements

### Requirement: Async post-diagnosis profile update

The system SHALL update Student.barrier_profile JSON after each batch of new diagnoses is saved. After the profile update, the system SHALL attempt to write the updated barrier profile and diagnosis timestamp to LangGraph AsyncSqliteStore keyed by student_id, using a best-effort strategy.

#### Scenario: Barrier profile recalculation
- **WHEN** a new batch of diagnoses is saved for a student
- **THEN** the Student.barrier_profile JSON SHALL be recalculated to reflect the latest distribution of concept/reading/expression across all diagnosed answers

#### Scenario: Diagnosis results written to Agent Store
- **WHEN** barrier profile is recalculated after a batch diagnosis
- **THEN** the system SHALL attempt to write the updated profile (barrier_type, rates, last_diagnosis_date) to LangGraph Store; if the Store write fails, the error SHALL be logged and the diagnosis pipeline SHALL complete successfully

## MODIFIED Requirements

### Requirement: Authorization and data isolation

The system SHALL enforce that students can only access their own practice, review, and wrong question data. When a teacher assigns a practice via POST /api/v1/practice/assign, the system SHALL automatically create a notification for the assigned student.

#### Scenario: Student can only see own data
- **WHEN** student A requests practice tasks
- **THEN** the system SHALL only return records where student_id matches student A

#### Scenario: Teacher can see class-level practice statistics
- **WHEN** a teacher requests practice effect data
- **THEN** the system SHALL verify the teacher teaches the class the student belongs to before returning data

#### Scenario: Practice assignment triggers student notification
- **WHEN** a teacher successfully assigns a practice session to a student via POST /api/v1/practice/assign
- **THEN** the system SHALL create a notification for the student with type "practice_assigned", including the practice_id as related_id; notification write failure SHALL NOT block the assignment

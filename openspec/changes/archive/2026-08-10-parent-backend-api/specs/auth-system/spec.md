## ADDED Requirements

### Requirement: Student bind code registration endpoint

The system SHALL provide an endpoint for students to register a 6-digit bind code that parents can use to bind to them.

#### Scenario: Student sends bind code
- **WHEN** an authenticated student sends POST /api/v1/parent/bind-code/{student_id} with body {"bind_code": "384729"}
- **THEN** the system SHALL store the bind_code on the Student record, replacing any previously stored code, and return success

#### Scenario: Bind code format validation
- **WHEN** a student sends a bind_code that is not exactly 6 numeric characters
- **THEN** the system SHALL return 400 with a validation error

#### Scenario: Cross-student bind code access denied
- **WHEN** student A attempts to send a bind code to student B's endpoint
- **THEN** the system SHALL return 403 FORBIDDEN

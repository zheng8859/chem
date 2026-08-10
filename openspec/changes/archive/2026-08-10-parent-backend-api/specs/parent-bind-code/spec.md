## Purpose

Enables the complete parent-student binding flow: students generate and send a 6-digit bind code to the server, parents verify the code during registration to create an active binding relationship, and either party can query or terminate the binding.

## ADDED Requirements

### Requirement: Student sends bind code to server

The system SHALL provide an endpoint for students to register a 6-digit bind code, which parents can then use to bind to that student.

#### Scenario: Student generates and sends bind code
- **WHEN** a student with id=100 sends POST /api/v1/parent/bind-code/100 with body {"bind_code": "384729"}
- **THEN** the system SHALL store the bind_code on the Student record, replacing any previously stored bind_code

#### Scenario: Bind code format validation
- **WHEN** a student sends a bind_code that is not exactly 6 numeric characters
- **THEN** the system SHALL reject with 400 and a validation error message

#### Scenario: Bind code regeneration invalidates old code
- **WHEN** a student sends a new bind_code while one already exists
- **THEN** the system SHALL overwrite the old bind_code — the old code becomes invalid immediately

#### Scenario: Cross-student bind code access denied
- **WHEN** student A attempts to POST /api/v1/parent/bind-code/{student_B_id}
- **THEN** the system SHALL return 403 FORBIDDEN

### Requirement: Parent queries bound children

The system SHALL allow a parent to list all students they have an active binding with.

#### Scenario: Parent with active bindings
- **WHEN** a parent requests GET /api/v1/parent/children
- **THEN** the system SHALL return a list of bound students, each containing student_id, student_name, class_name, school_name, relation, and binding_id

#### Scenario: Parent with no bindings
- **WHEN** a parent with no active bindings requests GET /api/v1/parent/children
- **THEN** the system SHALL return an empty list

### Requirement: Parent binds to student

The system SHALL allow a parent to bind to a student using the student's ID and bind code.

#### Scenario: Successful binding
- **WHEN** a parent sends POST /api/v1/parent/bind with student_id and a valid bind_code
- **THEN** the system SHALL create a StudentParentBinding record with status=active and the specified relation

#### Scenario: Invalid bind code
- **WHEN** a parent sends a bind_code that does not match the student's current bind_code
- **THEN** the system SHALL return 400 with error detail "绑定码无效"

#### Scenario: Already bound
- **WHEN** a parent attempts to bind to a student they already have an active binding with
- **THEN** the system SHALL return 400 with error detail "已绑定该学生"

### Requirement: Unbind parent from student

The system SHALL allow a parent or student to terminate an active binding relationship.

#### Scenario: Parent unbinds
- **WHEN** a parent sends DELETE /api/v1/parent/bind/{binding_id}
- **THEN** the system SHALL set the binding status to inactive, preventing further child data access

#### Scenario: Unbind non-existent binding
- **WHEN** a DELETE targets a binding_id that does not exist
- **THEN** the system SHALL return 404

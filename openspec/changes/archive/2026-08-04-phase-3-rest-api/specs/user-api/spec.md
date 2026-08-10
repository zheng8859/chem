## Purpose

Provides REST API endpoints for user management — teacher onboarding approval, student/parent CRUD, teaching assignments, and account lifecycle — enforcing RBAC at the endpoint level.

## ADDED Requirements

### Requirement: Teacher application approval workflow
The system SHALL support the full teacher onboarding workflow: pending applications can be listed by admins, and individually approved or rejected.

#### Scenario: Admin lists pending applications
- **WHEN** an admin sends GET /api/v1/users/teacher-applications?status=pending
- **THEN** the system returns a paginated list of TeacherApplication objects, newest first

#### Scenario: Admin approves a teacher application
- **WHEN** an admin sends POST /api/v1/users/teacher-applications/{id}/approve with approved=true and reviewer_id
- **THEN** the system creates Teacher + Account records, updates application status to approved, and returns the new TeacherRead with HTTP 201

#### Scenario: Admin rejects a teacher application
- **WHEN** an admin sends POST /api/v1/users/teacher-applications/{id}/approve with approved=false
- **THEN** the system sets application status to rejected and returns HTTP 200

### Requirement: Student management
The system SHALL support CRUD operations on Student entities. Students are scoped to classes. Students may only view their own data.

#### Scenario: Admin creates a student
- **WHEN** an admin sends POST /api/v1/students with account_id, class_id, name
- **THEN** the system creates the student and returns StudentRead with HTTP 201

#### Scenario: Teacher lists students by class
- **WHEN** a teacher sends GET /api/v1/classes/{class_id}/students
- **THEN** the system returns paginated students in that class, including barrier_profile summary

#### Scenario: Student reads own profile
- **WHEN** a student sends GET /api/v1/students/me
- **THEN** the system returns the student's full profile including barrier_profile and practice stats

#### Scenario: Teacher updates student class assignment
- **WHEN** a teacher sends PATCH /api/v1/students/{id} with a new class_id
- **THEN** the system updates the student's class and returns the updated StudentRead

### Requirement: Parent management
The system SHALL support CRUD on Parent entities and parent login via phone + bind_code.

#### Scenario: Parent login with phone and bind code
- **WHEN** a parent sends POST /api/auth/parent-login with phone and bind_code
- **THEN** the system validates credentials and returns JWT access + refresh tokens

### Requirement: Teacher-class-subject assignments
The system SHALL support creating, listing, and deleting teacher-class-subject assignments (TeacherClassSubject).

#### Scenario: Admin assigns a teacher to a class
- **WHEN** an admin sends POST /api/v1/teacher-assignments with teacher_id, class_id, subject, is_head_teacher
- **THEN** the system creates the assignment and returns TeacherClassSubjectRead

#### Scenario: Teacher views own assignments
- **WHEN** a teacher sends GET /api/v1/teachers/me/assignments
- **THEN** the system returns all classes and subjects assigned to that teacher

### Requirement: Account management
The system SHALL allow admins to list and manage user accounts (Account entities).

#### Scenario: Admin lists all accounts
- **WHEN** an admin sends GET /api/v1/accounts with optional role filter
- **THEN** the system returns a paginated list of accounts, excluding password hashes

## Purpose

Provides unified phone-based authentication across all three user roles (teacher, student, parent) with JWT token management, role-separated registration flows, and refresh token rotation.

## ADDED Requirements

### Requirement: Unified phone-based login

The system SHALL authenticate all users (teacher, student, parent) through a single `/api/auth/login` endpoint using phone number and password only.

#### Scenario: Successful login returns tokens
- **WHEN** a user provides a registered phone number and correct password
- **THEN** the system SHALL return an access token (24h), refresh token (7d), user_id, name, and role

#### Scenario: Wrong password rejection
- **WHEN** a user provides a registered phone number but wrong password
- **THEN** the system SHALL return 401 with a generic error message that does NOT reveal whether the phone number exists

#### Scenario: Role resolved server-side
- **WHEN** a user logs in with only phone and password
- **THEN** the system SHALL resolve the Account role from the database — the user does NOT declare their role in the login request

### Requirement: JWT payload with sub-role

The system SHALL include both the identity role (Account.role: teacher/student/parent) and the permission sub-role (Teacher.role: system_admin/academic_admin/subject_lead/teacher) in the JWT access token payload.

#### Scenario: Teacher with sub-role gets both fields
- **WHEN** a system_admin teacher logs in successfully
- **THEN** the JWT payload SHALL contain `role: "teacher"` and `sub_role: "system_admin"`

#### Scenario: Student gets no sub-role
- **WHEN** a student logs in successfully
- **THEN** the JWT payload SHALL contain `role: "student"` and `sub_role: null`

#### Scenario: Parent gets no sub-role or school_id
- **WHEN** a parent logs in successfully
- **THEN** the JWT payload SHALL contain `role: "parent"`, `sub_role: null`, and NO `school_id`

### Requirement: School-aware JWT for students and teachers

The system SHALL resolve and include school_id in the JWT for teacher and student roles.

#### Scenario: Teacher JWT includes school_id
- **WHEN** a teacher belonging to school_id=1 logs in
- **THEN** the JWT payload SHALL include `school_id: 1`

#### Scenario: Student JWT includes school_id
- **WHEN** a student logs in
- **THEN** the system SHALL traverse Student → Class → Grade → School to resolve school_id and include it in the JWT payload

### Requirement: Refresh token carries credential metadata

The system SHALL encode school_id and sub_role into refresh tokens so that access token rotation does not lose these fields.

#### Scenario: Refresh preserves school_id
- **WHEN** a teacher with school_id=1 and sub_role=teacher refreshes their access token
- **THEN** the new access token SHALL still contain `school_id: 1` and `sub_role: "teacher"`

### Requirement: Teacher application registration

The system SHALL support teacher registration through an application workflow requiring admin approval.

#### Scenario: Teacher submits application
- **WHEN** a teacher submits an application with phone, password, name, and selected school
- **THEN** the system SHALL create Account(phone, password_hash, role=teacher) + Teacher(school_id, name, status=pending, sub_role=teacher) + TeacherApplication(status=pending) atomically

#### Scenario: Duplicate phone rejection
- **WHEN** a teacher application uses a phone number already registered as any role
- **THEN** the system SHALL reject with duplicate resource error

### Requirement: Student batch creation and activation

The system SHALL allow teachers to batch-create student accounts with initial credentials; students activate by logging in.

#### Scenario: Teacher creates student
- **WHEN** a teacher creates a student with name, student ID, and initial password
- **THEN** the system SHALL create Account(phone=null, initially) + Student(class_id, school_id, student_id, name, is_activated=false) — the phone can be set during activation

#### Scenario: Student activates on first login
- **WHEN** the created student logs in with the initial credentials
- **THEN** the system SHALL set Student.is_activated=true and prompt for phone number setup

### Requirement: Parent registration with bind code

The system SHALL allow parent registration with mandatory student bind code validation.

#### Scenario: Parent registers with valid bind code
- **WHEN** a parent provides phone, password, and a bind code matching an active Student.bind_code
- **THEN** the system SHALL create Account(role=parent, phone) + Parent(name) + StudentParentBinding(student_id, parent_id, status=active)

#### Scenario: Bind code not found or expired
- **WHEN** a parent provides a bind code that does not match any student
- **THEN** the system SHALL reject the registration

### Requirement: Teacher sub-role enforcement

The system SHALL restrict teacher login to accounts whose Teacher.status is approved.

#### Scenario: Approved teacher logs in
- **WHEN** a teacher with status=approved provides correct credentials
- **THEN** the system SHALL return valid tokens

#### Scenario: Pending teacher rejected
- **WHEN** a teacher with status=pending provides correct credentials
- **THEN** the system SHALL return 403 "账号尚未通过审核，请联系管理员"

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

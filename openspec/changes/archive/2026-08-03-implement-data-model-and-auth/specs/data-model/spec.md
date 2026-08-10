## Purpose

Defines the core domain entities for the ChemAI platform, establishing the organizational hierarchy, user profiles, and teaching-learning data structures that underpin all other capabilities.

## ADDED Requirements

### Requirement: Organizational hierarchy

The system SHALL model organizations as a three-level hierarchy: School → Grade → Class, where Class is the minimum organizational unit and the boundary for data isolation.

#### Scenario: School contains grades
- **WHEN** a school is created with name "长沙市第一中学"
- **THEN** the school SHALL accept multiple grades (e.g., "高一", "高二", "高三")

#### Scenario: Grade contains classes
- **WHEN** a grade is created under a school
- **THEN** the grade SHALL accept multiple classes (e.g., "高一(1)班", "高一(2)班")

#### Scenario: Class name uniqueness within grade
- **WHEN** a teacher attempts to create a second class named "高一(1)班" within the same grade
- **THEN** the system SHALL reject the duplicate

### Requirement: Unified account with phone-based identity

The system SHALL use a single `Account` entity as the login credential for all users, identified by a globally unique phone number.

#### Scenario: Account creation with phone
- **WHEN** a new account is registered with phone "13800138001"
- **THEN** the system SHALL create an Account record with role teacher, student, or parent

#### Scenario: Phone uniqueness enforcement
- **WHEN** a registration attempts to use an already-registered phone number
- **THEN** the system SHALL reject it with a duplicate resource error

### Requirement: Role-specific profiles

The system SHALL maintain separate profile tables (Teacher, Student, Parent) linked to Account via foreign key, each carrying role-specific attributes.

#### Scenario: Teacher profile with sub-role
- **WHEN** a teacher account is created
- **THEN** the system SHALL create a Teacher profile with a sub-role of teacher, academic_admin, subject_lead, or system_admin

#### Scenario: Student profile with class assignment
- **WHEN** a student account is created
- **THEN** the system SHALL create a Student profile linked to a specific Class, carrying a school-assigned student ID (学号) that is unique within the school

#### Scenario: Parent profile without school association
- **WHEN** a parent account is created
- **THEN** the system SHALL create a Parent profile with NO school_id — parents are not school members

### Requirement: Teacher-class subject relationship

The system SHALL track which teachers teach which classes through a TeacherClassSubject join table with subjects and head-teacher designation.

#### Scenario: Teacher assigned to class
- **WHEN** a teacher is assigned to teach chemistry to 高一(1)班
- **THEN** a TeacherClassSubject record SHALL be created with teacher_id, class_id, subject="化学"

#### Scenario: Head teacher designation
- **WHEN** a teacher is designated as head teacher (班主任) for a class
- **THEN** the TeacherClassSubject record SHALL have is_head_teacher=true

### Requirement: Teacher application workflow

The system SHALL support a teacher registration application process where an Account is created on application submission with pending status.

#### Scenario: Application creates pending account
- **WHEN** a teacher submits an application with phone, password, name, and school selection
- **THEN** the system SHALL create Account(role=teacher, phone) + Teacher(status=pending) + TeacherApplication(status=pending) in a single transaction

#### Scenario: Pending teacher cannot log in
- **WHEN** a teacher with pending status attempts to log in
- **THEN** the system SHALL reject with "账号尚未通过审核"

#### Scenario: Application approval activates teacher
- **WHEN** an admin approves the application
- **THEN** the Teacher status SHALL change to approved and the teacher can log in

### Requirement: Student activation flow

The system SHALL support batch creation of students by teachers, with students activating their accounts on first login.

#### Scenario: Teacher batch-creates students
- **WHEN** a teacher creates a student with name, student ID, and initial password
- **THEN** the system SHALL create Account(role=student, phone can be set later) + Student(class_id, student_id, is_activated=false)

#### Scenario: Student first login activates account
- **WHEN** a student logs in for the first time with the initial credentials
- **THEN** the system SHALL set Student.is_activated=true

#### Scenario: Inactive student restricted
- **WHEN** a student whose is_activated is false attempts to use the system before first login
- **THEN** the system SHALL restrict access to profile setup only

### Requirement: Parent-child binding

The system SHALL allow parents to bind to students via a 6-digit binding code during registration.

#### Scenario: Parent registers with valid bind code
- **WHEN** a parent registers with phone, password, and a valid 6-digit bind code matching a Student
- **THEN** the system SHALL create Account(role=parent) + Parent + StudentParentBinding(status=active) in one transaction

#### Scenario: Invalid bind code rejection
- **WHEN** a parent provides a bind code that does not match any student's current bind_code
- **THEN** the system SHALL reject the registration with an error

### Requirement: Knowledge point hierarchy

The system SHALL model knowledge points as a hierarchical tree via parent_id for syllabus-ordered navigation.

#### Scenario: Knowledge point nesting
- **WHEN** knowledge point "弱电解质的电离" has parent_id pointing to "电解质溶液"
- **THEN** the system SHALL traverse from parent to child for syllabus-ordered question selection

#### Scenario: Root knowledge points
- **WHEN** a knowledge point has parent_id IS NULL
- **THEN** it SHALL be treated as a top-level category

### Requirement: Approval request for destructive agent actions

The system SHALL persist agent approval requests as structured records for audit and recovery.

#### Scenario: Agent requests approval
- **WHEN** an agent calls a destructive tool (assign_adaptive_practice, delete_bank)
- **THEN** the system SHALL create an ApprovalRequest with status=pending, tool_name, tool_params, and a timeout

#### Scenario: Teacher approves
- **WHEN** a teacher explicitly approves the pending request
- **THEN** the ApprovalRequest status SHALL change to approved, the action SHALL execute

#### Scenario: Approval timeout
- **WHEN** a pending approval request reaches its expires_at timestamp without teacher action
- **THEN** the system SHALL set status to expired and the action SHALL NOT execute

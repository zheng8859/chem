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

### Requirement: VariantQuestion entity

The system SHALL maintain a VariantQuestion table that stores LLM-generated variant questions isolated from the Question main table for analytics purity.

#### Scenario: VariantQuestion storage
- **WHEN** a variant question is generated
- **THEN** the system SHALL store it with original_question_id (FK to Question), content, question_type, options, answer, analysis, knowledge_point_tags, difficulty, generated_at, and expires_at (default now()+90days)

#### Scenario: VariantQuestion lifecycle
- **WHEN** expires_at passes
- **THEN** the variant SHALL NOT be returned for reuse; new variants SHALL be generated on next request

#### Scenario: VariantQuestion does not appear in Question queries
- **WHEN** querying the Question table for exam questions, bank browsing, or analytics
- **THEN** VariantQuestion records SHALL NOT be included (separate table, no UNION or JOIN in analytics queries)

### Requirement: PracticeSessionQuestion join table

The system SHALL maintain a PracticeSessionQuestion join table linking PracticeSession records to their assigned Question records with ordering.

#### Scenario: Practice session contains ordered questions
- **WHEN** a practice session is created
- **THEN** the system SHALL create PracticeSessionQuestion records with practice_session_id, question_id, and sort_order for each assigned question

#### Scenario: Unique constraint on session-question pair
- **WHEN** a duplicate (session_id, question_id) pair is inserted
- **THEN** the system SHALL reject it with a unique constraint violation

### Requirement: PracticeSession extended fields

The system SHALL extend the PracticeSession model with a business identifier, title, question count, and optional deadline.

#### Scenario: PracticeSession with business fields
- **WHEN** a practice session is created
- **THEN** the system SHALL store practice_id (unique string), title, question_count, and optional deadline alongside the existing barrier_type and status fields

### Requirement: Student barrier tracking fields

The system SHALL store the student's barrier type distribution and weak knowledge points on the Student model for efficient ZPD computation without repeated aggregation.

#### Scenario: Barrier type stored as JSON
- **WHEN** the diagnosis engine completes a student analysis
- **THEN** the system SHALL update Student.barrier_type with {"concept": 0.7, "reading": 0.15, "expression": 0.15} format

#### Scenario: Weak knowledge points stored as JSON array
- **WHEN** the diagnosis engine identifies weak knowledge points
- **THEN** the system SHALL update Student.weak_knowledge_points with ["氧化还原反应", "离子反应"] format

### Requirement: Daily practice in ExamRecord

The system SHALL use ExamRecord with type=daily_practice (in addition to existing practice/monthly/homework types) for the daily scheduler's per-student practice records.

#### Scenario: Daily practice ExamRecord
- **WHEN** the daily scheduler creates a practice for a student
- **THEN** the system SHALL create an ExamRecord with type="daily_practice", class_id from the student's class, exam_date=today, and question_stats containing the target knowledge points, question count, and difficulty metadata

### Requirement: ReviewTask 6-level Ebbinghaus model

The system SHALL model ReviewTask levels from 0 to 5 (previously 1 to 6), where Level 0 represents initial learning with immediate review availability, Levels 1-4 represent increasing review intervals (1, 3, 7, 14 days), and Level 5 represents mastery with no further review. The review interval for each level SHALL be computed from the current time plus the level's interval days.

#### Scenario: ReviewTask with Level 0 for new wrong answer
- **WHEN** a student answers incorrectly and auto-sync creates a ReviewTask
- **THEN** the system SHALL create the task with level=0, next_review_date=now()

#### Scenario: Level 1 review scheduled 1 day later
- **WHEN** a student completes a review at Level 0 and meets upgrade conditions
- **THEN** the system SHALL set level=1 and next_review_date=now()+1day

#### Scenario: Level 5 marks task as mastered
- **WHEN** a ReviewTask reaches level=5
- **THEN** the system SHALL set status=completed and next_review_date=NULL

#### Scenario: Downgrade from Level 3 to Level 2
- **WHEN** a student answers incorrectly at Level 3
- **THEN** the system SHALL decrement to level=2 and set next_review_date=now()+7days (standard Level 2 interval)

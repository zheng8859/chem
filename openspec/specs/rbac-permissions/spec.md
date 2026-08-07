## Purpose

Defines the role-based access control matrix that governs which actions each user role can perform on each resource, enforced through FastAPI dependency injection.

## ADDED Requirements

### Requirement: Permission matrix covers all teacher sub-roles

The system SHALL define a resource×action permission matrix for four teacher sub-roles (system_admin, academic_admin, subject_lead, teacher) covering school, grade, class, teacher, student, analysis, exam, question, ocr, and grading resources.

#### Scenario: Admin has full access
- **WHEN** a system_admin requests any resource
- **THEN** the system SHALL grant create, read, update, and delete on school, grade, class, and teacher resources

#### Scenario: Ordinary teacher has limited access
- **WHEN** an ordinary teacher requests to delete a school
- **THEN** the system SHALL reject with 403 — teachers have read-only access to organizational resources

#### Scenario: Academic admin can manage classes
- **WHEN** an academic_admin requests to create or update a class
- **THEN** the system SHALL grant the operation

### Requirement: Student self-data access

The system SHALL grant students read access to their own grade, assignments, and grades.

#### Scenario: Student reads their own grade info
- **WHEN** a student requests grade information for the grade they belong to
- **THEN** the system SHALL return the data scoped to their class and grade

#### Scenario: Student cannot read other students' data
- **WHEN** a student requests another student's detailed profile
- **THEN** the system SHALL reject with 403

### Requirement: Parent data access through binding

The system SHALL grant parents read-only access to their bound children's data.

#### Scenario: Parent reads bound child's report
- **WHEN** a parent with an active StudentParentBinding requests the child's learning report
- **THEN** the system SHALL return the report

#### Scenario: Parent cannot access unbound student
- **WHEN** a parent requests data for a student they are not bound to
- **THEN** the system SHALL reject with 403

### Requirement: Permission enforcement via FastAPI dependency

The system SHALL provide a `require_permission(resource, action)` FastAPI dependency that extracts the current user, checks the permission matrix, and returns UserContext or raises 403.

#### Scenario: Authorized user passes permission check
- **WHEN** an endpoint decorated with `Depends(require_permission("exam", "create"))` is called by a teacher
- **THEN** the dependency SHALL return the UserContext and the endpoint executes

#### Scenario: Unauthorized user receives 403
- **WHEN** an endpoint decorated with `Depends(require_permission("school", "delete"))` is called by an ordinary teacher
- **THEN** the dependency SHALL raise HTTPException(403, "权限不足")

### Requirement: Teacher class-scoped data isolation

The system SHALL filter teacher data access to only the classes they are assigned to through TeacherClassSubject.

#### Scenario: Teacher sees only assigned classes
- **WHEN** a teacher requests the student list
- **THEN** the system SHALL return only students whose class_id matches the teacher's TeacherClassSubject records

#### Scenario: System admin sees all classes
- **WHEN** a system_admin requests the student list
- **THEN** the system SHALL return all students within their school without TeacherClassSubject filtering

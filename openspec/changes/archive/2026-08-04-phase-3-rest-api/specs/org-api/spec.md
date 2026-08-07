## Purpose

Provides REST API endpoints for managing the organizational hierarchy — schools, grades, and classes — forming the multi-tenant data isolation backbone of ChemAI.

## ADDED Requirements

### Requirement: School CRUD
The system SHALL provide create, read, update, and delete operations for School entities. Only users with admin role may create or delete schools. All authenticated users within a school may read their own school.

#### Scenario: Admin creates a school
- **WHEN** an admin sends POST /api/v1/schools with name, region, address, phone, current_semester
- **THEN** the system creates a new school and returns the SchoolRead object with HTTP 201

#### Scenario: Teacher reads own school
- **WHEN** an authenticated teacher sends GET /api/v1/schools/{school_id}
- **THEN** the system returns the SchoolRead if the teacher belongs to that school, otherwise HTTP 403

#### Scenario: List all schools
- **WHEN** an admin sends GET /api/v1/schools
- **THEN** the system returns a paginated list of schools

### Requirement: Grade CRUD with school scoping
The system SHALL allow CRUD operations on Grade entities, scoped by school. Grades MUST always be created under a valid school.

#### Scenario: Admin creates a grade under a school
- **WHEN** an admin sends POST /api/v1/schools/{school_id}/grades with name and academic_year
- **THEN** the system creates the grade under that school and returns GradeRead with HTTP 201

#### Scenario: Teacher lists grades in own school
- **WHEN** a teacher sends GET /api/v1/schools/{school_id}/grades
- **THEN** the system returns only grades belonging to that teacher's school

#### Scenario: Create grade with invalid school
- **WHEN** any user sends POST with a non-existent school_id
- **THEN** the system returns HTTP 404 with detail "学校不存在"

### Requirement: Class CRUD with grade scoping
The system SHALL provide CRUD operations on Class entities, scoped by grade. Each class belongs to exactly one grade.

#### Scenario: Teacher creates a class
- **WHEN** an authorized teacher sends POST /api/v1/grades/{grade_id}/classes with name and optional head_teacher_id
- **THEN** the system creates the class and returns ClassRead

#### Scenario: List classes by grade
- **WHEN** a user sends GET /api/v1/grades/{grade_id}/classes
- **THEN** the system returns all classes under that grade, including student_count per class

### Requirement: Organization chain traversal
The system SHALL support navigating the full organization chain: school → grades → classes in a single request.

#### Scenario: Get full org tree
- **WHEN** an admin or teacher sends GET /api/v1/org/tree?school_id={id}
- **THEN** the system returns a nested JSON: school with grades array, each grade with classes array

## Purpose

Enables teachers (via Agent) to create and manage structured learning plans for students, and students to view and execute their assigned plan by marking tasks as complete.

## ADDED Requirements

### Requirement: Teacher creates learning plan

The system SHALL allow teachers to create a learning plan for a student via POST /api/v1/learning-plan, auto-archiving any previous active plan for the same student.

#### Scenario: Create new learning plan
- **WHEN** a teacher creates a learning plan with title and an array of tasks (each with day_number, task_description, estimated_minutes, and optional knowledge_points)
- **THEN** the system SHALL create the plan with is_active=true, return the plan_id and all created task ids, and set any previously active plan for the same student to is_active=false

#### Scenario: Create plan with no previous plan
- **WHEN** a student has no existing learning plan and a teacher creates one
- **THEN** the system SHALL create the new plan without requiring any archive operation

#### Scenario: Create plan for non-existent student
- **WHEN** a teacher attempts to create a plan for a student_id that does not exist
- **THEN** the system SHALL return 404 RESOURCE_NOT_FOUND

### Requirement: Teacher updates learning plan

The system SHALL allow teachers to update an existing learning plan's title and tasks via PUT /api/v1/learning-plan/{plan_id}.

#### Scenario: Update plan with new tasks
- **WHEN** a teacher updates a plan's tasks, replacing the existing task list
- **THEN** the system SHALL delete the old tasks, create new ones from the provided list, and update the plan's updated_at timestamp

#### Scenario: Update non-existent plan
- **WHEN** a teacher attempts to update a plan that does not exist
- **THEN** the system SHALL return 404 RESOURCE_NOT_FOUND

### Requirement: Student fetches active learning plan

The system SHALL allow a student to fetch their currently active learning plan via GET /api/v1/learning-plan/{student_id}.

#### Scenario: Fetch active plan with tasks
- **WHEN** a student requests their learning plan
- **THEN** the system SHALL return the active plan with all tasks ordered by day_number ascending, each task containing id, day_number, task_description, estimated_minutes, knowledge_points, and status

#### Scenario: No active plan
- **WHEN** a student has no active learning plan
- **THEN** the system SHALL return plan=null with an appropriate message

#### Scenario: Archived plan not returned
- **WHEN** a student has only archived (is_active=false) plans
- **THEN** the GET endpoint SHALL return plan=null

### Requirement: Student marks task as complete

The system SHALL allow a student to mark a specific learning plan task as completed via PATCH /api/v1/learning-plan/tasks/{task_id}/complete.

#### Scenario: Mark task complete
- **WHEN** a student marks a pending task as complete
- **THEN** the system SHALL set the task's status to "completed" and set completed_at to the current timestamp

#### Scenario: Mark already-completed task
- **WHEN** a student attempts to mark a task that is already completed
- **THEN** the system SHALL return 409 CONFLICT with an appropriate message

#### Scenario: Mark task for another student's plan
- **WHEN** a student attempts to mark a task belonging to a plan assigned to a different student
- **THEN** the system SHALL return 403 FORBIDDEN

### Requirement: One active plan per student

The system SHALL enforce that each student has at most one active (is_active=true) learning plan at any time.

#### Scenario: New plan auto-archives old
- **WHEN** a teacher creates a new plan for a student who already has an active plan
- **THEN** the old plan SHALL be set to is_active=false before the new plan is created

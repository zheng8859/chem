## Purpose

Provides a notification system that automatically creates notifications when teachers perform key actions (assign practice, send learning plan), and allows students to retrieve and read their notifications.

## ADDED Requirements

### Requirement: Student notification list endpoint

The system SHALL provide an endpoint for students to retrieve their notifications, ordered by created_at descending.

#### Scenario: Retrieve notification list
- **WHEN** a student requests GET /api/v1/notifications/student/{student_id}?limit=20&offset=0
- **THEN** the system SHALL return a paginated list of notifications, each containing id, type, title, body, related_id, and created_at

#### Scenario: No notifications
- **WHEN** a student has no notifications
- **THEN** the system SHALL return an empty data array with total=0

### Requirement: Mark notification as read

The system SHALL allow a student to mark a notification as read via POST /api/v1/notifications/{id}/read.

#### Scenario: Mark notification read
- **WHEN** a student marks a notification as read
- **THEN** the system SHALL set read_at to the current timestamp and return success

#### Scenario: Mark another student's notification
- **WHEN** a student attempts to mark a notification belonging to a different student as read
- **THEN** the system SHALL return 403 FORBIDDEN

### Requirement: Auto-trigger notification on practice assignment

The system SHALL automatically create a notification for a student when a teacher assigns them a practice via POST /api/v1/practice/assign.

#### Scenario: Practice assigned triggers notification
- **WHEN** a teacher assigns a practice session to student S with question_count=10
- **THEN** the system SHALL create a notification for student S with type="practice_assigned", title="新的自适应练习已布置", and body containing the question count; the notification's related_id SHALL be set to the practice_id

### Requirement: Auto-trigger notification on learning plan creation

The system SHALL automatically create a notification for a student when a teacher creates or updates a learning plan for them.

#### Scenario: Learning plan created triggers notification
- **WHEN** a teacher creates a new learning plan for student S
- **THEN** the system SHALL create a notification for student S with type="plan_updated", title="学习计划已更新", and body describing the plan title; the notification's related_id SHALL be set to the plan_id

#### Scenario: Learning plan updated triggers notification
- **WHEN** a teacher updates an existing learning plan for student S
- **THEN** the system SHALL create a notification for student S with type="plan_updated"

### Requirement: Notification write is best-effort

The system SHALL write notifications on a best-effort basis: notification creation failure SHALL NOT block the parent operation (practice assignment or plan creation/update).

#### Scenario: Notification write fails gracefully
- **WHEN** notification creation encounters a database error
- **THEN** the parent operation (practice assignment or plan creation) SHALL still complete successfully, and the error SHALL be logged

### Requirement: Notification retention

The system SHALL retain notifications for 30 days, after which they MAY be automatically deleted.

#### Scenario: Old notifications cleaned
- **WHEN** a notification's created_at is older than 30 days
- **THEN** it MAY be excluded from query results

### Requirement: Student self-data isolation for notifications

The system SHALL enforce that students can only access their own notifications.

#### Scenario: Student accesses own notifications
- **WHEN** a student requests their notification list
- **THEN** the system SHALL only return notifications where the student_id matches

#### Scenario: Cross-student access denied
- **WHEN** a student attempts to access another student's notifications
- **THEN** the system SHALL return 403 FORBIDDEN

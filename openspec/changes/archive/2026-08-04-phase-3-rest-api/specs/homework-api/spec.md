## Purpose

Provides REST API endpoints for home-school communication — student-parent binding via 6-digit code, parent notification management, and weekly report dispatch.

## ADDED Requirements

### Requirement: Student-parent binding with code
The system SHALL support creating student-parent bindings using the student's 6-digit bind_code, and listing bindings by parent or student.

#### Scenario: Parent binds to student with valid code
- **WHEN** a parent sends POST /api/v1/bindings with student_id, parent_id, bind_code matching the student's code
- **THEN** the system creates a StudentParentBinding with status=active and returns BindingRead with HTTP 201

#### Scenario: Parent binds with invalid code
- **WHEN** a parent sends POST /api/v1/bindings with a bind_code that does not match the student's code
- **THEN** the system returns HTTP 400 with detail "绑定码不匹配"

#### Scenario: List parent's bound children
- **WHEN** a parent sends GET /api/v1/parents/{parent_id}/bindings
- **THEN** the system returns all active bindings for that parent, including student names

#### Scenario: List student's bound parents
- **WHEN** a teacher sends GET /api/v1/students/{student_id}/bindings
- **THEN** the system returns all parent bindings for that student

### Requirement: Parent notification delivery
The system SHALL support creating, listing, and marking notifications as read for parents.

#### Scenario: System creates a notification
- **WHEN** the system sends POST /api/v1/notifications with parent_id, notification_type, title, body
- **THEN** the system creates a ParentNotification with is_read=false

#### Scenario: Parent lists notifications
- **WHEN** a parent sends GET /api/v1/notifications?parent_id={id}
- **THEN** the system returns paginated notifications, unread first, newest first

#### Scenario: Parent marks notification as read
- **WHEN** a parent sends PATCH /api/v1/notifications/{id}/read
- **THEN** the system sets is_read=true

### Requirement: Report dispatch
The system SHALL provide an endpoint to send exam reports to all parents of students in a given exam.

#### Scenario: Teacher sends exam reports
- **WHEN** a teacher sends POST /api/v1/reports/send-to-students/{exam_id}
- **THEN** the system creates ParentNotification for each bound parent of students in the exam, returns sent_count and failed_count

## MODIFIED Requirements

### Requirement: Parent-child binding

The system SHALL allow parents to bind to students via a 6-digit binding code during registration, and SHALL provide an endpoint for students to register their bind code before parent registration.

#### Scenario: Parent registers with valid bind code
- **WHEN** a parent registers with phone, password, and a valid 6-digit bind code matching a Student
- **THEN** the system SHALL create Account(role=parent) + Parent + StudentParentBinding(status=active) in one transaction

#### Scenario: Invalid bind code rejection
- **WHEN** a parent provides a bind code that does not match any student's current bind_code
- **THEN** the system SHALL reject the registration with an error

#### Scenario: Student sends bind code to server
- **WHEN** a student sends POST /api/v1/parent/bind-code/{student_id} with a valid 6-digit code
- **THEN** the system SHALL store the code on Student.bind_code, overwriting any previous code

### Requirement: Notification types

The system SHALL support the NotificationType enum with five values for parent-facing notifications: weekly_report, score_alert, learning_plan, reminder, daily_report. The existing values learning_report, warning_alert, teacher_message SHALL be retained. The ParentNotification model SHALL use notification_type with these values, while the student-facing Notification model SHALL continue using its own type field (practice_assigned, plan_updated, report_ready) independently.

#### Scenario: Parent notification type values
- **WHEN** a ParentNotification is created
- **THEN** its notification_type SHALL be one of: weekly_report, score_alert, learning_plan, reminder, daily_report

#### Scenario: Student notification type unchanged
- **WHEN** a student Notification is created
- **THEN** its type SHALL continue to be one of: practice_assigned, plan_updated, report_ready

### Requirement: ParentNotification field alignment

The system SHALL use read_at (datetime, nullable) instead of is_read (boolean) for tracking notification read status, SHALL include a related_id field for linking to source resources, and SHALL retain notifications for 90 days.

#### Scenario: Notification read tracking
- **WHEN** a parent marks a notification as read
- **THEN** read_at SHALL be set to the current timestamp; is_read SHALL be derived from read_at IS NOT NULL

#### Scenario: Related resource linking
- **WHEN** a notification is created for a specific weekly report or warning event
- **THEN** the related_id SHALL reference the source entity (e.g., weekly_report_id or warning_log_id)

## ADDED Requirements

### Requirement: WeeklyReport entity

The system SHALL maintain a WeeklyReport table for caching LLM-generated parent weekly reports.

#### Scenario: WeeklyReport storage
- **WHEN** a weekly report is generated
- **THEN** the system SHALL store it with student_id (FK to Student), week_start (date), week_end (date), summary (text, ≤60 chars), detail (text, ≤120 chars), advice (text, ≤80 chars), no_data (boolean), generated_at (datetime), and generated_by (enum: "auto" or "manual")

#### Scenario: WeeklyReport uniqueness
- **WHEN** a report for the same (student_id, week_start) is generated twice
- **THEN** the system SHALL return the existing cached report instead of generating a new one

#### Scenario: WeeklyReport history
- **WHEN** a new week's report is generated for the same student
- **THEN** the previous week's report SHALL remain in the database as history

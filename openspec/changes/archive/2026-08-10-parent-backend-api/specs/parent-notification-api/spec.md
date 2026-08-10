## Purpose

Provides parent-side notification management: system events (weekly report ready, score alerts, learning plans, reminders, daily reports) generate notifications for parents, who can list and read them via REST API.

## ADDED Requirements

### Requirement: Parent notification list endpoint

The system SHALL provide an endpoint for parents to retrieve their notifications, ordered by sent_at descending.

#### Scenario: Retrieve notification list
- **WHEN** a parent requests GET /api/v1/parent/notifications?limit=20&offset=0
- **THEN** the system SHALL return a paginated list of notifications, each containing id, notification_type, title, body, related_id, is_read (derived from read_at != null), and sent_at

#### Scenario: No notifications
- **WHEN** a parent has no notifications
- **THEN** the system SHALL return an empty items array with total=0

### Requirement: Mark parent notification as read

The system SHALL allow a parent to mark a notification as read.

#### Scenario: Mark notification read
- **WHEN** a parent sends PUT /api/v1/parent/notifications/{notification_id}/read
- **THEN** the system SHALL set read_at to the current timestamp and return the updated notification

#### Scenario: Mark another parent's notification
- **WHEN** a parent attempts to mark a notification belonging to a different parent as read
- **THEN** the system SHALL return 403 FORBIDDEN

### Requirement: Five parent notification types

The system SHALL support five notification types for parent-facing messages.

#### Scenario: Weekly report notification
- **WHEN** a weekly report is generated for a bound child
- **THEN** the system SHALL create a ParentNotification with type="weekly_report", title containing the child's name (e.g., "张三本周学习周报已生成"), and body containing the report summary

#### Scenario: Score alert notification
- **WHEN** a student's accuracy drops more than 15% for two consecutive weeks
- **THEN** the system SHALL create a ParentNotification with type="score_alert", title "成绩下滑预警 - {student_name}", and body describing the trend

#### Scenario: Learning plan notification
- **WHEN** a new learning plan is created for a bound child
- **THEN** the system SHALL create a ParentNotification with type="learning_plan", title "新的学习计划已生成", and body describing the plan

#### Scenario: Reminder notification
- **WHEN** a student has not logged in for 3 consecutive days
- **THEN** the system SHALL create a ParentNotification with type="reminder", title "连续3天未练习提醒", and body naming the child

#### Scenario: Daily practice notification
- **WHEN** a teacher assigns practice to a student
- **THEN** the system SHALL create a ParentNotification with type="daily_report", title "{student_name}今日练习已推送", and body containing practice details

### Requirement: Parent notification retention

The system SHALL retain parent notifications for 90 days, after which they MAY be automatically excluded from query results.

#### Scenario: Notifications in retention window
- **WHEN** a parent requests their notification list
- **THEN** the system SHALL include notifications where sent_at is within the last 90 days

#### Scenario: Expired notifications excluded
- **WHEN** a notification's sent_at is older than 90 days
- **THEN** it MAY be excluded from list query results

### Requirement: Parent self-data isolation for notifications

The system SHALL enforce that parents can only access their own notifications.

#### Scenario: Parent accesses own notifications
- **WHEN** a parent requests their notification list
- **THEN** the system SHALL only return notifications where parent_id matches the authenticated parent

#### Scenario: Cross-parent access denied
- **WHEN** a parent attempts to mark another parent's notification as read
- **THEN** the system SHALL return 403 FORBIDDEN

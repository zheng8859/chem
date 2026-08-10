## Purpose

Provide the parent-side main dashboard as a mobile-optimized single page with a child selector, three content tabs (Overview, Learning Report, Messages), and a bind-new-child bottom sheet, consuming the existing parent REST API endpoints.

## ADDED Requirements

### Requirement: Auth guard on dashboard entry

The system SHALL verify the user is authenticated and has parent role before rendering the dashboard.

#### Scenario: Authenticated parent enters
- **WHEN** a parent with valid JWT token navigates to `parent.html`
- **THEN** the page SHALL load the children list and render the dashboard

#### Scenario: Unauthenticated user enters
- **WHEN** a user without a valid token accesses `parent.html`
- **THEN** the system SHALL redirect to `parent-login.html`

#### Scenario: Non-parent role enters
- **WHEN** a teacher or student with valid token accesses `parent.html`
- **THEN** the system SHALL redirect to their role-appropriate page or show an access denied message

### Requirement: Child selector with data binding

The system SHALL populate a swipeable child selector from `GET /api/v1/parent/children` and switch all tabs' data when a different child is selected.

#### Scenario: Children list loaded on entry
- **WHEN** the dashboard loads
- **THEN** the system SHALL call `GET /api/v1/parent/children` and render each child as a selectable item in the child selector, showing student name, class name, and school name

#### Scenario: Switch to another child
- **WHEN** the parent selects a different child in the selector
- **THEN** the currently active tab SHALL reload its data for the new child
- **AND** cached data for the previously selected child SHALL be preserved in memory

#### Scenario: No children bound
- **WHEN** the parent has no active bindings
- **THEN** the child selector SHALL show "暂无绑定子女" with a prominent "绑定子女" call-to-action

#### Scenario: Single child
- **WHEN** the parent has exactly one bound child
- **THEN** the child selector SHALL show the child name without left/right navigation arrows

### Requirement: Overview tab (Tab 1)

The system SHALL display the child's learning overview from `GET /api/v1/parent/child/{student_id}/report`.

#### Scenario: Overview data loaded
- **WHEN** the Overview tab is active
- **THEN** the system SHALL display: weekly practice count, accuracy rate, weak knowledge points, last practice time, learning characteristics text, and streak days
- **AND** the obstacle bar (concept/reading/expression) SHALL reflect the barrier type distribution when available

#### Scenario: Overview with no practice data
- **WHEN** the child has never completed a practice
- **THEN** the overview SHALL show "暂无学习数据" with placeholder values (0 practices, -- accuracy)

#### Scenario: Overview loading state
- **WHEN** the API request is in flight
- **THEN** the tab SHALL show a loading skeleton or spinner

#### Scenario: Overview API error
- **WHEN** the API returns an error
- **THEN** the tab SHALL show an error message with a "重试" (retry) button

### Requirement: Learning report tab (Tab 2)

The system SHALL display the current week's learning report with a week navigator.

#### Scenario: Weekly report cached
- **WHEN** the Report tab loads and `GET /api/v1/parent/child/{student_id}/weekly` returns a cached report
- **THEN** the system SHALL render the report summary, detail, and advice, along with knowledge point mastery bars from the timeline data

#### Scenario: Weekly report not yet generated
- **WHEN** the API returns 404 (no cached report)
- **THEN** the system SHALL show "本周周报尚未生成" with a "生成周报" button that calls `POST .../weekly/generate`

#### Scenario: Manual report generation
- **WHEN** the parent taps "生成周报"
- **THEN** the system SHALL call `POST /api/v1/parent/child/{student_id}/weekly/generate`, show a loading state during generation, and render the result on success

#### Scenario: Week navigation
- **WHEN** the parent uses the week selector arrows
- **THEN** for the current week, the full cached report SHALL be shown; for past weeks, a simplified summary from the timeline API SHALL be shown

### Requirement: Messages tab (Tab 3)

The system SHALL display paginated parent notifications from `GET /api/v1/parent/notifications`.

#### Scenario: Notifications loaded
- **WHEN** the Messages tab is active
- **THEN** the system SHALL load the first page of notifications and render each as a tappable card showing notification type, title, preview body, and sent time

#### Scenario: Mark notification as read
- **WHEN** a parent taps an unread notification
- **THEN** the system SHALL expand the full message body and call `PUT /api/v1/parent/notifications/{id}/read`
- **AND** the unread indicator (blue dot) SHALL disappear

#### Scenario: No notifications
- **WHEN** the parent has no notifications
- **THEN** the tab SHALL show "暂无消息" with an illustration placeholder

#### Scenario: Notification pagination
- **WHEN** the parent scrolls to the bottom of the message list
- **THEN** the system SHALL load the next page if more notifications exist

### Requirement: Bind new child bottom sheet

The system SHALL provide an in-page bottom sheet for binding an additional child without leaving the dashboard.

#### Scenario: Open bind sheet
- **WHEN** the parent taps "绑定新子女"
- **THEN** a bottom sheet SHALL slide up with fields for bind code (required, 6-digit) and relation (optional, default "other")

#### Scenario: Successful binding
- **WHEN** the parent enters a valid bind code and submits
- **THEN** the system SHALL call `POST /api/v1/parent/bind`, close the sheet, refresh the children list, and auto-select the newly bound child

#### Scenario: Invalid bind code in sheet
- **WHEN** the parent enters an incorrect or expired bind code
- **THEN** the system SHALL display an error message without closing the sheet, allowing retry

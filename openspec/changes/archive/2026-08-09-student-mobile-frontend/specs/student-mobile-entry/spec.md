## Purpose

Provides the student mobile entry experience: login form with JWT handshake and role-based redirect, a profile/report page showing stats, diagnosis, and learning plan data from existing APIs, a shared TabBar navigation shell across all 6 pages, and auth guards that protect student-only routes.

## ADDED Requirements

### Requirement: Student login form submission

The login page SHALL accept school_id (or phone) and password, submit to the auth API, store the JWT, and redirect to the student home page.

#### Scenario: Successful login with school_id
- **WHEN** a student submits school_id "S2024001" and correct password
- **THEN** the system SHALL POST to /api/v1/auth/login, call ChemAuth.login(token) on success, and redirect to index.html

#### Scenario: Successful login with phone
- **WHEN** a student submits phone "13800138000" and correct password
- **THEN** the system SHALL POST to /api/v1/auth/login with the phone field and proceed with the same JWT-handshake flow

#### Scenario: Login failure shows error
- **WHEN** the login API returns 401
- **THEN** the form SHALL display "学号或密码错误" below the login button and re-enable the button

#### Scenario: Login button loading state
- **WHEN** the login request is in flight
- **THEN** the button SHALL be disabled and display "登录中..."

### Requirement: Auth guard on protected pages

Every student page except login SHALL verify the user is authenticated and has the student role before rendering content.

#### Scenario: Unauthenticated user redirected
- **WHEN** a user navigates to index.html without a valid JWT in localStorage
- **THEN** the page SHALL redirect to login.html immediately

#### Scenario: Non-student role redirected
- **WHEN** a teacher's JWT is used to access a student page
- **THEN** the page SHALL detect the role mismatch and redirect to the teacher home page

### Requirement: Profile page stats display

The personal center page SHALL fetch and display the student's practice stats from the existing stats API.

#### Scenario: Stats loaded on page init
- **WHEN** a student navigates to report.html
- **THEN** the system SHALL GET /api/v1/student/{user_id}/stats and display total_practice_count, accuracy_rate, and streak_days in the three stat cards

#### Scenario: Stats API failure shows fallback
- **WHEN** the stats API returns an error
- **THEN** the stat cards SHALL display "--" with grey text and a "加载失败" toast

### Requirement: Profile card with student identity

The personal center page SHALL display the student's name, class name, and binding code from the user's JWT claims and class API.

#### Scenario: Profile rendered from JWT
- **WHEN** report.html loads
- **THEN** the profile card SHALL extract student_name and class_id from the JWT payload and display them

#### Scenario: Binding code displayed
- **WHEN** the profile card renders
- **THEN** a 6-character binding code from the user object SHALL be displayed for parent-child binding

### Requirement: Weekly report bottom sheet

The personal center page SHALL display a bottom-sheet modal containing a learning weekly report with practice stats, knowledge-point progress bars, and teacher comments.

#### Scenario: Weekly report modal opens
- **WHEN** the student taps the "学习报告" entry
- **THEN** a bottom sheet SHALL slide up from the bottom showing the student's recent practice count, accuracy, study duration, knowledge-point progress bars, and teacher remarks

#### Scenario: Modal closes on overlay tap
- **WHEN** the student taps the semi-transparent overlay behind the bottom sheet
- **THEN** the sheet SHALL slide down and close

### Requirement: Menu entry navigation

The 5 menu entries on the profile page SHALL navigate to their respective destinations or open modals.

#### Scenario: Wrong question entry navigates
- **WHEN** the student taps "我的错题本"
- **THEN** the system SHALL navigate to wrong.html via location.href

#### Scenario: Review center entry navigates
- **WHEN** the student taps "复习中心"
- **THEN** the system SHALL navigate to review.html via location.href

#### Scenario: Settings entry shows placeholder
- **WHEN** the student taps "个人设置"
- **THEN** the system SHALL display a toast "设置功能即将上线"

#### Scenario: Learning plan entry opens plan view
- **WHEN** the student taps "学习计划"
- **THEN** the system SHALL GET /api/v1/learning-plan/{student_id} and display the plan content in a bottom sheet or navigate to a dedicated view

### Requirement: Shared TabBar navigation shell

All 6 student pages SHALL share a consistent 4-tab bottom navigation bar (AI助教/练习/错题/我的) with active-state highlighting and cross-page navigation.

#### Scenario: TabBar renders on all pages
- **WHEN** any student page loads after authentication
- **THEN** a 56px-height TabBar SHALL render at the bottom with 4 tabs in order: AI助教, 练习, 错题, 我的

#### Scenario: Active tab highlights correctly
- **WHEN** the student is on index.html (AI助教)
- **THEN** the AI助教 tab SHALL have the active style (Oxford Blue text) and the other 3 tabs SHALL use muted color

#### Scenario: Tab tap navigates to target page
- **WHEN** the student taps the "错题" tab
- **THEN** the system SHALL navigate to wrong.html via location.href

### Requirement: Logout

The profile page SHALL provide a logout mechanism that clears the auth token and redirects to the login page.

#### Scenario: Logout clears token
- **WHEN** the student taps "退出登录"
- **THEN** the system SHALL call ChemAuth.logout(), clear the JWT from localStorage, and redirect to login.html

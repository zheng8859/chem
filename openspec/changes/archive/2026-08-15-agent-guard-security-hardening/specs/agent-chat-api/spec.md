## MODIFIED Requirements

### Requirement: Unified SSE chat streaming endpoint

The system SHALL expose a single POST /api/v1/chat/stream endpoint that accepts a user message, thread_id, and context (containing role and optional student_id/class_id), and streams SSE events from the Agent engine. The persona SHALL be derived from the authenticated user identity (JWT), NOT from the untrusted request-body context.role. The allowed persona mapping SHALL be: teacher → teacher/tutor (a teacher MAY select tutor), student → student, parent → parent. A request whose context.role would elevate the caller's persona beyond its authenticated role SHALL be rejected with HTTP 403 before any tool executes. The request body SHALL be JSON with fields: message, thread_id, context.

#### Scenario: Teacher persona chat stream
- **WHEN** POST /api/v1/chat/stream is called by an authenticated teacher with message "出5道氧化还原选择题"
- **THEN** the system SHALL load the Teacher persona Agent, execute the ReAct loop, and stream SSE events back

#### Scenario: Student persona chat stream
- **WHEN** POST /api/v1/chat/stream is called by an authenticated student with message "帮我讲解离子方程式"
- **THEN** the system SHALL load the Student persona Agent, inject student context into the System Message, and stream SSE events back

#### Scenario: Teacher may select tutor persona
- **WHEN** POST /api/v1/chat/stream is called by an authenticated teacher with context.role="tutor"
- **THEN** the system SHALL load the tutor persona Agent

#### Scenario: Cross-role escalation rejected
- **WHEN** POST /api/v1/chat/stream is called by an authenticated student with context.role="teacher"
- **THEN** the system SHALL return HTTP 403 and SHALL NOT execute any teacher-only tool, preventing cross-role tool leakage

#### Scenario: Invalid auth role rejected
- **WHEN** POST /api/v1/chat/stream is called by an authenticated user whose role is not teacher, student, or parent
- **THEN** the system SHALL return HTTP 403

### Requirement: Approval resume endpoint

The system SHALL expose POST /api/v1/chat/resume that receives a thread_id, an approval_id, and an approval decision (approved/rejected). The endpoint SHALL first verify that the calling user owns the thread (via the persisted GuardState user_id), rejecting cross-user access with HTTP 403. It SHALL then verify that the supplied approval_id matches the thread's pending approval interrupt, rejecting a missing or mismatched approval_id with HTTP 409. On success it SHALL load the interrupted Agent checkpoint, resume the paused execution with the approval decision applied, and continue the SSE event stream from the point of interruption.

#### Scenario: Resume after approval
- **WHEN** POST /api/v1/chat/resume is called by the thread owner with thread_id, a matching approval_id, and approved=true
- **THEN** the system SHALL resume the interrupted Agent execution with the approval applied, execute the previously blocked tool call, and continue the SSE stream

#### Scenario: Resume after rejection
- **WHEN** POST /api/v1/chat/resume is called by the thread owner with a matching approval_id and approved=false
- **THEN** the system SHALL resume the interrupted Agent execution with the rejection applied, skip the blocked tool call, and have the Agent inform the user the operation was cancelled

#### Scenario: Cross-user resume rejected
- **WHEN** POST /api/v1/chat/resume is called for a thread owned by a different user
- **THEN** the system SHALL return HTTP 403 and SHALL NOT resume the thread

#### Scenario: Mismatched approval id rejected
- **WHEN** POST /api/v1/chat/resume is called with an approval_id that does not match the pending approval
- **THEN** the system SHALL return HTTP 409 and SHALL NOT resume the thread

#### Scenario: Resume with no pending approval rejected
- **WHEN** POST /api/v1/chat/resume is called for a thread with no pending approval interrupt
- **THEN** the system SHALL return HTTP 409 and SHALL NOT resume the thread

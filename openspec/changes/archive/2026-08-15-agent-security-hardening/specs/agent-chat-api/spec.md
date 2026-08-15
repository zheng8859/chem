## MODIFIED Requirements

### Requirement: Approval resume endpoint

The system SHALL expose POST /api/v1/chat/resume that receives a thread_id, an approval_id, and an approval decision (approved/rejected). The endpoint SHALL first verify that the calling user owns the thread (via the persisted GuardState user_id), rejecting cross-user access with HTTP 403. A thread whose persisted GuardState has no user_id SHALL be rejected with HTTP 403 (fail-closed), since the owner is unverifiable. The endpoint SHALL then verify that the thread's persisted persona is permitted for the authenticated user's role (reusing the same persona-resolution defense as the stream endpoint), rejecting an escalation with HTTP 403. It SHALL then verify that the supplied approval_id matches the thread's pending approval interrupt, rejecting a missing or mismatched approval_id with HTTP 409. On success it SHALL load the interrupted Agent checkpoint, resume the paused execution with the approval decision applied, and continue the SSE event stream from the point of interruption.

#### Scenario: Resume after approval
- **WHEN** POST /api/v1/chat/resume is called by the thread owner with thread_id, a matching approval_id, and approved=true
- **THEN** the system SHALL resume the interrupted Agent execution with the approval applied, execute the previously blocked tool call, and continue the SSE stream

#### Scenario: Resume after rejection
- **WHEN** POST /api/v1/chat/resume is called by the thread owner with a matching approval_id and approved=false
- **THEN** the system SHALL resume the interrupted Agent execution with the rejection applied, skip the blocked tool call, and have the Agent inform the user the operation was cancelled

#### Scenario: Cross-user resume rejected
- **WHEN** POST /api/v1/chat/resume is called for a thread owned by a different user
- **THEN** the system SHALL return HTTP 403 and SHALL NOT resume the thread

#### Scenario: Resume with unverifiable owner rejected
- **WHEN** POST /api/v1/chat/resume is called for a thread whose persisted GuardState has no user_id
- **THEN** the system SHALL return HTTP 403 and SHALL NOT resume the thread

#### Scenario: Resume with escalated persona rejected
- **WHEN** POST /api/v1/chat/resume is called by a user whose authenticated role does not permit the thread's persisted persona
- **THEN** the system SHALL return HTTP 403 and SHALL NOT resume the thread

#### Scenario: Mismatched approval id rejected
- **WHEN** POST /api/v1/chat/resume is called with an approval_id that does not match the pending approval
- **THEN** the system SHALL return HTTP 409 and SHALL NOT resume the thread

#### Scenario: Resume with no pending approval rejected
- **WHEN** POST /api/v1/chat/resume is called for a thread with no pending approval interrupt
- **THEN** the system SHALL return HTTP 409 and SHALL NOT resume the thread

## MODIFIED Requirements

### Requirement: Approval resume endpoint

The system SHALL expose POST /api/v1/chat/resume that receives a thread_id and an approval decision (approved/rejected), loads the interrupted Agent checkpoint, resumes the paused execution with the approval decision applied, and continues the SSE event stream from the point of interruption.

#### Scenario: Resume after approval
- **WHEN** POST /api/v1/chat/resume is called with thread_id and decision="approved"
- **THEN** the system SHALL resume the interrupted Agent execution with the approval applied, execute the previously blocked tool call, and continue the SSE stream

#### Scenario: Resume after rejection
- **WHEN** POST /api/v1/chat/resume is called with thread_id and decision="rejected"
- **THEN** the system SHALL resume the interrupted Agent execution with the rejection applied, skip the blocked tool call, and have the Agent inform the user the operation was cancelled

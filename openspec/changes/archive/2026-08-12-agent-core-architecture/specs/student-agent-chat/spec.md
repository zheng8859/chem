## ADDED Requirements

### Requirement: Migration to unified chat API

The student Agent chat SHALL use the unified POST /api/v1/chat/stream endpoint with context.role="student" instead of a student-specific SSE endpoint. All existing SSE event handling and rendering requirements remain unchanged.

#### Scenario: Student chat uses unified endpoint
- **WHEN** a student sends a message via the chat UI
- **THEN** the frontend SHALL POST to /api/v1/chat/stream with context.role="student" and a student-specific thread_id prefix "s-"

#### Scenario: Conversation management uses unified endpoints
- **WHEN** the student opens the conversation drawer
- **THEN** the frontend SHALL call GET /api/v1/chat/conversations?prefix=s- instead of a student-specific endpoint

## REMOVED Requirements

### Requirement: Dedicated student SSE endpoint
**Reason**: Replaced by unified /api/v1/chat/stream endpoint with context.role="student"
**Migration**: Change frontend POST URL from the old student-specific endpoint to /api/v1/chat/stream with context.role="student". All SSE event types and rendering logic remain identical.

## Purpose

Provides unified REST endpoints for Agent conversation streaming (SSE), conversation lifecycle management (list, history, create, delete, reset), and approval-based execution resumption, serving all four Personas through a single `/api/v1/chat/` path prefix.

## ADDED Requirements

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

### Requirement: Conversation listing

The system SHALL expose GET /api/v1/chat/conversations that returns conversation threads from the checkpoint database, filtered by an optional prefix query parameter (default "t-"). Each conversation SHALL include thread_id, title (first 50 chars of first user message), preview (first 100 chars), last_at (ISO timestamp), and message_count.

#### Scenario: List teacher conversations
- **WHEN** GET /api/v1/chat/conversations?prefix=t- is called
- **THEN** the system SHALL return all threads starting with "t-" sorted by last_at descending

#### Scenario: Empty conversation list
- **WHEN** GET /api/v1/chat/conversations?prefix=x- is called and no threads match
- **THEN** the system SHALL return `{conversations: [], total: 0}`

### Requirement: Conversation history retrieval

The system SHALL expose GET /api/v1/chat/history/{thread_id} that returns the full message history for a conversation thread, extracted from the LangGraph checkpoint, classified by role (user/assistant).

#### Scenario: Retrieve existing conversation history
- **WHEN** GET /api/v1/chat/history/t-1723456789000 is called
- **THEN** the system SHALL return all messages from that thread's latest checkpoint, each with role and content

#### Scenario: Non-existent thread returns empty
- **WHEN** GET /api/v1/chat/history/nonexistent is called
- **THEN** the system SHALL return `{messages: []}`

### Requirement: New conversation creation

The system SHALL expose POST /api/v1/chat/new that generates a new thread_id in format `{prefix}-{Unix毫秒时间戳}` and returns it. The prefix SHALL default to "m-" unless overridden.

#### Scenario: Create new teacher conversation
- **WHEN** POST /api/v1/chat/new is called with prefix="t-"
- **THEN** the system SHALL return `{thread_id: "t-1723456789000"}` where the timestamp is the current Unix time in milliseconds

### Requirement: Conversation deletion

The system SHALL expose DELETE /api/v1/chat/conversations/{thread_id} that removes all checkpoint data (writes and checkpoints) for the given thread_id from the checkpoint database.

#### Scenario: Delete existing conversation
- **WHEN** DELETE /api/v1/chat/conversations/t-1723456789000 is called
- **THEN** the system SHALL remove all rows with that thread_id from the checkpoint database and return `{success: true}`

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

### Requirement: Conversation reset

The system SHALL expose POST /api/v1/chat/reset that clears all messages for the given thread_id from the checkpoint, effectively starting a fresh conversation while keeping the same thread_id.

#### Scenario: Reset active conversation
- **WHEN** POST /api/v1/chat/reset is called with thread_id="t-1723456789000"
- **THEN** the checkpointer SHALL write an empty messages array for that thread_id

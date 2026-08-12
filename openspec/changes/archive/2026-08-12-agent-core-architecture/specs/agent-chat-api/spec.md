## Purpose

Provides unified REST endpoints for Agent conversation streaming (SSE), conversation lifecycle management (list, history, create, delete, reset), and approval-based execution resumption, serving all four Personas through a single `/api/v1/chat/` path prefix.

## ADDED Requirements

### Requirement: Unified SSE chat streaming endpoint

The system SHALL expose a single POST /api/v1/chat/stream endpoint that accepts a user message, thread_id, and context (containing role, user_id, and optional student_id/class_id), and streams SSE events from the Agent engine. The persona SHALL be determined by context.role (teacher/student/tutor/parent). The request body SHALL be JSON with fields: message, thread_id, context.

#### Scenario: Teacher persona chat stream
- **WHEN** POST /api/v1/chat/stream is called with context.role="teacher" and message "出5道氧化还原选择题"
- **THEN** the system SHALL load the Teacher persona Agent, execute the ReAct loop, and stream SSE events back

#### Scenario: Student persona chat stream
- **WHEN** POST /api/v1/chat/stream is called with context.role="student" and message "帮我讲解离子方程式"
- **THEN** the system SHALL load the Student persona Agent, inject student context into the System Message, and stream SSE events back

#### Scenario: Invalid role rejected
- **WHEN** POST /api/v1/chat/stream is called with context.role="admin"
- **THEN** the system SHALL return HTTP 400 with detail "Invalid persona role"

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

The system SHALL expose POST /api/v1/chat/resume that receives a thread_id and approval decision (approved/rejected), loads the checkpoint, and resumes the Agent execution from the paused state.

#### Scenario: Resume after approval
- **WHEN** POST /api/v1/chat/resume is called with thread_id and decision="approved"
- **THEN** the system SHALL load the checkpoint, inject the approval into the pending tool call, and continue the SSE stream

#### Scenario: Resume after rejection
- **WHEN** POST /api/v1/chat/resume is called with thread_id and decision="rejected"
- **THEN** the system SHALL load the checkpoint, mark the pending tool call as rejected, and have the Agent inform the user the operation was cancelled

### Requirement: Conversation reset

The system SHALL expose POST /api/v1/chat/reset that clears all messages for the given thread_id from the checkpoint, effectively starting a fresh conversation while keeping the same thread_id.

#### Scenario: Reset active conversation
- **WHEN** POST /api/v1/chat/reset is called with thread_id="t-1723456789000"
- **THEN** the checkpointer SHALL write an empty messages array for that thread_id

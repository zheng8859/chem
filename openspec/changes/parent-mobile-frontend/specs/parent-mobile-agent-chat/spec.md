## Purpose

Provide an AI-powered learning advisor for parents via a floating button that opens a bottom sheet with SSE-based streaming chat, enabling parents to ask natural-language questions about their child's chemistry learning.

## ADDED Requirements

### Requirement: Floating AI button and bottom sheet

The system SHALL provide a floating "AI" button on the dashboard that opens a bottom sheet chat panel.

#### Scenario: Open AI panel
- **WHEN** the parent taps the floating AI button
- **THEN** a bottom sheet SHALL slide up covering the lower 60% of the screen with an overlay behind it, and the floating button SHALL hide

#### Scenario: Close AI panel
- **WHEN** the parent taps the overlay, the close button, or drags the sheet handle down
- **THEN** the bottom sheet SHALL slide down, the overlay SHALL fade out, and the floating button SHALL reappear

### Requirement: Quick question chips

The system SHALL display shortcut question chips at the top of the AI panel that the parent can tap to send a pre-written query without typing.

#### Scenario: Tap a quick question chip
- **WHEN** the parent taps a chip (e.g., "孩子最近学习怎么样？")
- **THEN** the system SHALL send that text as a message to the AI agent

#### Scenario: Chips remain after sending
- **WHEN** a quick question is sent via a chip tap
- **THEN** the chips SHALL remain visible for further use

### Requirement: SSE streaming chat

The system SHALL stream AI responses via `ChemSSE.connect()` to `POST /api/v1/parent/agent/chat` with the selected child's `student_id`.

#### Scenario: Send a message and receive streaming reply
- **WHEN** the parent types a message or taps a chip and submits
- **THEN** the system SHALL send `{message, thread_id, student_id}` to the SSE endpoint
- **AND** the user message SHALL appear immediately in the chat
- **AND** the system SHALL display "AI 正在思考..." during the thinking phase
- **AND** text chunks received via `text` SSE events SHALL appear progressively in a reply bubble
- **AND** tool call/result phases SHALL show a brief status indicator (e.g., "正在查询学习数据...")

#### Scenario: Tool call visibility
- **WHEN** the SSE stream emits a `tool_call` event
- **THEN** the chat SHALL show a subtle indicator (e.g., "🔍 正在获取数据...") without revealing raw JSON

#### Scenario: Stream completion
- **WHEN** the SSE `done` event fires
- **THEN** the system SHALL save the `thread_id` for conversation continuity
- **AND** the input field SHALL re-enable for the next message

#### Scenario: Stream error
- **WHEN** the SSE emits an `error` event or the connection fails
- **THEN** the chat SHALL display "AI 助手暂时无法回复，请稍后重试"
- **AND** the input field SHALL re-enable for retry

### Requirement: KaTeX rendering in AI responses

The system SHALL render LaTeX formulas (e.g., `$H_2O$`, `$Fe^{3+}$`) in AI response messages using KaTeX.

#### Scenario: AI response contains chemical formula
- **WHEN** the AI response includes text like "$H_2SO_4$"
- **THEN** the system SHALL render it as a properly formatted chemical formula via `ChemAPI.renderLatex()`

#### Scenario: AI response has no LaTeX
- **WHEN** the AI response contains only plain text
- **THEN** the system SHALL display it as-is with no rendering overhead

### Requirement: Conversation history management

The system SHALL allow parents to view, switch, create, and delete conversation threads.

#### Scenario: View conversation list
- **WHEN** the parent taps the history icon in the AI panel header
- **THEN** the system SHALL fetch `GET /api/v1/parent/agent/conversations` and display threads sorted by last active time

#### Scenario: Switch to an existing conversation
- **WHEN** the parent taps a past conversation in the list
- **THEN** the system SHALL load `GET /api/v1/parent/agent/history/{thread_id}`, display past messages, and set `thread_id` for subsequent sends

#### Scenario: Create new conversation
- **WHEN** the parent taps "新建对话"
- **THEN** the system SHALL call `POST /api/v1/parent/agent/new`, clear the chat view, and use the new `thread_id`

#### Scenario: Delete conversation
- **WHEN** the parent long-presses or swipes to delete a conversation
- **THEN** the system SHALL call `DELETE /api/v1/parent/agent/conversations/{thread_id}` and remove it from the list

### Requirement: Input state management

The system SHALL manage input field state during the send/stream/receive lifecycle.

#### Scenario: Input disabled during streaming
- **WHEN** the AI is streaming a response (state = connecting or streaming)
- **THEN** the send button and input field SHALL be disabled

#### Scenario: Input enabled after completion
- **WHEN** the stream completes or errors out
- **THEN** the send button and input SHALL re-enable

#### Scenario: Empty message prevention
- **WHEN** the parent taps send with an empty input
- **THEN** the system SHALL not send the request

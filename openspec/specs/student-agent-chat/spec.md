## Purpose

Provides the SSE-based AI tutoring chat experience for students: a streaming Agent dialogue endpoint on the backend filtered to the Student persona, and a real-time chat client on the frontend that handles 11 SSE event types, renders tool-execution cards, and manages conversation history.

## ADDED Requirements

### Requirement: Agent SSE streaming endpoint

The system SHALL expose an SSE endpoint that accepts a student message and streams Agent execution events back in real time, filtered to the Student persona's 7-tool whitelist.

#### Scenario: Student sends a message and receives streaming response
- **WHEN** a student sends POST to the SSE chat endpoint with message "帮我讲解氧化还原反应" and a valid thread_id
- **THEN** the system SHALL stream `phase`(thinking) → `tool_call` → `tool_result` → `text`(streaming) → `done` events via SSE in order

#### Scenario: Student persona tool filtering
- **WHEN** a Student persona chat session is created
- **THEN** the Agent SHALL only have access to chemistry_tutor, simulate_experiment, web_search, ionic_equation_tutor, stoichiometry_tutor, redox_tutor, equilibrium_tutor, and periodic_law_tutor

#### Scenario: Non-student persona rejected
- **WHEN** a request to the student SSE endpoint specifies persona other than "student"
- **THEN** the system SHALL reject with HTTP 403

### Requirement: Student context injection into Agent System Message

The system SHALL query student profile data (name, class, barrier_profile, practice stats) and inject it as a System Message before each Agent invocation for the Student persona.

#### Scenario: Profile injected on first message of a thread
- **WHEN** a student starts a new chat thread
- **THEN** the first Agent call SHALL include a System Message containing the student's name, class name, barrier profile distribution, and cumulative practice count

#### Scenario: Profile reuse within same thread
- **WHEN** a student sends a second message in the same thread_id within the same server session
- **THEN** the system SHALL reuse the previously loaded student context without re-querying the database

### Requirement: Frontend SSE client event parsing

The frontend SHALL establish a fetch-based readable stream connection to the chat SSE endpoint and dispatch structured events to the UI layer.

#### Scenario: Parse all 11 SSE event types
- **WHEN** the frontend receives SSE data containing `phase`, `tool_call`, `tool_result`, `text`, `component`, `navigate`, `populate`, `action`, `exam_images`, `error`, and `done` event lines
- **THEN** it SHALL parse each event into {type, data} and invoke the corresponding handler

#### Scenario: Phase event updates status bar
- **WHEN** a `phase` event with state "executing" arrives
- **THEN** the chat UI SHALL display "执行中..." with a real-time elapsed timer in the status bar

#### Scenario: Text dedup against tool output
- **WHEN** the LLM echoes tool output text that overlaps > 70% with the previous `tool_result` content
- **THEN** the frontend SHALL skip rendering the duplicated text chunk

### Requirement: Chat bubble and tool card rendering

The chat UI SHALL render user messages, AI text bubbles, and tool-execution cards with distinct visual styles.

#### Scenario: User message bubble
- **WHEN** the student sends a message
- **THEN** a right-aligned bubble with white background and border SHALL appear immediately in the chat area

#### Scenario: AI text bubble with KaTeX
- **WHEN** a `text` event delivers content containing LaTeX like `$H_2O$`
- **THEN** the AI bubble SHALL render it with KaTeX after the text stream completes

#### Scenario: Tool call card with timer
- **WHEN** a `tool_call` event arrives for tool "chemistry_tutor"
- **THEN** a card with "⚡ 化学辅导" header and a real-time elapsed timer (monospace, red) SHALL appear in the chat area

#### Scenario: Tool result renders structured card
- **WHEN** a `tool_result` event with success=true arrives
- **THEN** the timer SHALL stop and the result content SHALL render inside the tool card

### Requirement: Quick chips for preset actions

The chat input area SHALL display horizontally scrollable quick-action chips that send preset messages.

#### Scenario: Chip click sends preset message
- **WHEN** the student taps the "帮我讲解这个知识点" chip
- **THEN** the chip text SHALL be submitted as a user message to the SSE endpoint

#### Scenario: Chips persist after sending
- **WHEN** a message is sent via chip
- **THEN** all 5 quick chips SHALL remain visible and tappable above the input area

### Requirement: Conversation history management

The system SHALL support listing, loading, creating, and deleting conversation threads via the side drawer.

#### Scenario: Load conversation list on drawer open
- **WHEN** the student opens the sidebar drawer
- **THEN** the system SHALL fetch GET /api/v1/chat/conversations?prefix=s- and display threads sorted by last_at descending

#### Scenario: Switch to existing conversation
- **WHEN** the student taps a conversation item in the drawer
- **THEN** the system SHALL load GET /api/v1/chat/history/{thread_id} and render the full message history into the chat area

#### Scenario: Create new conversation
- **WHEN** the student taps the "+" new-chat button
- **THEN** the system SHALL call POST /api/v1/chat/new, clear the chat area, and set the new thread_id as active

#### Scenario: Delete conversation
- **WHEN** the student long-presses a conversation item and confirms deletion
- **THEN** the system SHALL call DELETE /api/v1/chat/conversations/{thread_id} and remove the item from the drawer list

### Requirement: SSE connection lifecycle

The frontend SHALL manage SSE connection state and handle disconnection gracefully.

#### Scenario: Send lock prevents duplicate messages
- **WHEN** a message is being sent and the student taps send again
- **THEN** the second send SHALL be ignored until the first SSE stream completes

#### Scenario: Connection error shows retry
- **WHEN** the SSE fetch fails with a network error
- **THEN** the UI SHALL display "连接失败，请重试" with a retry button that resends the last message

#### Scenario: Abort on page navigation
- **WHEN** the student navigates away from the chat page while an SSE stream is active
- **THEN** the AbortController SHALL cancel the in-flight fetch

### Requirement: Approval card rendering

The chat UI SHALL render confirmation/cancel cards when the Agent enters the awaiting_approval phase.

#### Scenario: Approval card displayed
- **WHEN** a `phase` event with state "awaiting_approval" arrives
- **THEN** a yellow-bordered card with "确认" and "取消" buttons SHALL appear in the chat area

#### Scenario: Confirm resumes execution
- **WHEN** the student taps "确认"
- **THEN** the system SHALL POST to the resume endpoint and the SSE stream SHALL continue from the approval checkpoint

### Requirement: Migration to unified chat API

The student Agent chat SHALL use the unified POST /api/v1/chat/stream endpoint with context.role="student" instead of a student-specific SSE endpoint. All existing SSE event handling and rendering requirements remain unchanged.

#### Scenario: Student chat uses unified endpoint
- **WHEN** a student sends a message via the chat UI
- **THEN** the frontend SHALL POST to /api/v1/chat/stream with context.role="student" and a student-specific thread_id prefix "s-"

#### Scenario: Conversation management uses unified endpoints
- **WHEN** the student opens the conversation drawer
- **THEN** the frontend SHALL call GET /api/v1/chat/conversations?prefix=s- instead of a student-specific endpoint

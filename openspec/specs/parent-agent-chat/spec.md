## Purpose

Provides an SSE-based AI chat agent for parents, reusing the existing v2 ReAct Agent engine with the Parent persona (defined in document 30-Agent对话系统设计). The agent answers parent questions about their child's chemistry learning using plain language, with tools for weekly reports, barrier diagnosis, and student memory retrieval.

## ADDED Requirements

### Requirement: Parent agent SSE chat endpoint

The system SHALL serve parent chat through the unified POST /api/v1/chat/stream endpoint with context.role="parent". The parent's selected child SHALL be resolved from context.student_id in the request body.

#### Scenario: Parent starts a chat
- **WHEN** a parent sends POST /api/v1/chat/stream with context.role="parent", message "孩子最近学了什么化学知识", thread_id, and context.student_id
- **THEN** the system SHALL: (1) validate parent identity from JWT, (2) resolve the child from context.student_id, (3) assemble the Parent persona Agent, (4) inject {student_context}, (5) stream standardized SSE events

#### Scenario: Parent without bound children
- **WHEN** a parent with no active bindings attempts to chat
- **THEN** the system SHALL return 400 with detail "请先绑定子女"

#### Scenario: Agent uses appropriate tools based on question
- **WHEN** a parent asks "哪些知识点比较薄弱"
- **THEN** the agent SHALL call diagnose_barrier and return the child's barrier distribution in parent-friendly language

### Requirement: Parent agent persona constraints

The system SHALL enforce the Parent persona rules during chat: use plain language (no educational jargon), encourage rather than criticize, never reveal other students' information, never cause anxiety. The parent's currently selected child's profile SHALL be injected as {student_context} into the system prompt.

#### Scenario: No rankings in parent agent response
- **WHEN** a parent asks how their child compares to classmates
- **THEN** the agent SHALL NOT provide rankings or comparisons; it SHALL respond with the child's own progress perspective

#### Scenario: Chemistry terms converted to plain language
- **WHEN** the agent describes the child's learning content
- **THEN** it SHALL convert chemistry terminology to everyday language (e.g., "氧化还原" → "学习物质与氧气反应的过程")

#### Scenario: Child profile injected into system prompt
- **WHEN** a parent chat session starts for a bound child
- **THEN** the system SHALL inject {student_context} containing child name, barrier type, and practice count into the Agent's system prompt

### Requirement: Parent agent conversation management

The system SHALL support listing, retrieving history, creating, and resetting conversations through the unified /api/v1/chat/ endpoints, filtered to parent-owned conversations by thread_id prefix "p-".

#### Scenario: List parent conversations
- **WHEN** GET /api/v1/chat/conversations?prefix=p- is called
- **THEN** the system SHALL return conversations with thread_id prefix "p-", filtered to the authenticated parent's conversations

#### Scenario: Get conversation history
- **WHEN** GET /api/v1/chat/history/{thread_id} is called
- **THEN** the system SHALL return the full message history for that thread_id

### Requirement: Preset prompt chips

The system SHALL support five preset parent prompts that map to specific agent tools.

#### Scenario: Knowledge overview prompt
- **WHEN** parent sends "孩子最近学了什么化学知识"
- **THEN** the agent SHALL use memory_student_get to retrieve recent learning activity and describe it in plain language

#### Scenario: Weak points prompt
- **WHEN** parent sends "哪些知识点比较薄弱"
- **THEN** the agent SHALL use diagnose_barrier to check weak knowledge points and describe them supportively

#### Scenario: Home support prompt
- **WHEN** parent sends "怎么在家帮孩子学化学"
- **THEN** the agent SHALL use web_search and child context to suggest specific, practical family activities

#### Scenario: Learning status prompt
- **WHEN** parent sends "孩子的学习状态怎么样"
- **THEN** the agent SHALL use weekly_report to generate a natural-language status summary

#### Scenario: Alert check prompt
- **WHEN** parent sends "有什么需要我注意的吗"
- **THEN** the agent SHALL use diagnose_barrier and memory_student_get to identify any concerning patterns

### Requirement: Migration to full ReAct Agent engine

The parent Agent chat SHALL use the v2 ReAct Agent engine (LangGraph create_react_agent) with Parent persona tools, instead of the current bare llm_chat_with_tools() call. The backend SHALL go through the full Gateway → Planner → ReAct → Guard → SSE pipeline.

#### Scenario: Parent chat uses ReAct engine
- **WHEN** a parent sends a message via POST /api/v1/chat/stream with context.role="parent"
- **THEN** the system SHALL load the Parent persona Agent, run the full ReAct loop with Guard, and stream standardized SSE events (phase, tool_call, tool_result, text, done)

#### Scenario: Parent persona tool filtering via YAML
- **WHEN** the Parent persona Agent is built
- **THEN** it SHALL use the Parent YAML configuration's available_skills intersected with TOOL_META to determine the tool set

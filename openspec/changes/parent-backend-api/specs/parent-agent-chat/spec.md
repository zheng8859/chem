## Purpose

Provides an SSE-based AI chat agent for parents, reusing the existing v2 ReAct Agent engine with the Parent persona (defined in document 30-Agent对话系统设计). The agent answers parent questions about their child's chemistry learning using plain language, with tools for weekly reports, barrier diagnosis, and student memory retrieval.

## ADDED Requirements

### Requirement: Parent agent SSE chat endpoint

The system SHALL provide an SSE streaming endpoint for parent-agent conversations, reusing the existing v2 ReAct Agent engine with Parent persona tools.

#### Scenario: Parent starts a chat
- **WHEN** a parent sends POST /api/v1/parent/agent/chat with message "孩子最近学了什么化学知识" and thread_id
- **THEN** the system SHALL: (1) validate parent identity from JWT, (2) resolve the currently selected child from the request context, (3) assemble the Parent persona Agent with tools weekly_report, diagnose_barrier, memory_student_get, web_search, and browser tools, (4) inject {student_context} with child name, barrier type, and practice count, (5) stream SSE events (phase, tool_call, tool_result, text, done)

#### Scenario: Parent without bound children
- **WHEN** a parent with no active bindings attempts to chat
- **THEN** the system SHALL return 400 with detail "请先绑定子女"

#### Scenario: Agent uses appropriate tools based on question
- **WHEN** a parent asks "哪些知识点比较薄弱"
- **THEN** the agent SHALL call diagnose_barrier and return the child's barrier distribution in parent-friendly language

### Requirement: Parent agent persona constraints

The system SHALL enforce the Parent persona rules during chat: use plain language (no educational jargon), encourage rather than criticize, never reveal other students' information, never cause anxiety.

#### Scenario: No rankings in parent agent response
- **WHEN** a parent asks how their child compares to classmates
- **THEN** the agent SHALL NOT provide rankings or comparisons; it SHALL respond with the child's own progress perspective

#### Scenario: Chemistry terms converted to plain language
- **WHEN** the agent describes the child's learning content
- **THEN** it SHALL convert chemistry terminology to everyday language (e.g., "氧化还原" → "学习物质与氧气反应的过程")

### Requirement: Parent agent conversation management

The system SHALL support listing, retrieving history, creating, and resetting conversations for parent agents, consistent with existing teacher/student conversation management endpoints.

#### Scenario: List parent conversations
- **WHEN** GET /api/v1/parent/agent/conversations is called
- **THEN** the system SHALL return conversations with thread_id prefix "p-", filtered to the authenticated parent's conversations

#### Scenario: Get conversation history
- **WHEN** GET /api/v1/parent/agent/history/{thread_id} is called
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

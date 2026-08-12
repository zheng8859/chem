## Purpose

Provides the core Agent reasoning engine that processes natural language user input through a Gateway → Planner → ReAct loop → Guard pipeline, streaming results as structured SSE events to the frontend.

## ADDED Requirements

### Requirement: Gateway Provider selection

The system SHALL classify incoming user messages to select the appropriate LLM provider before the Agent engine is invoked. Messages containing image/OCR-related keywords SHALL route to the vision-capable provider; all other messages SHALL route to the default reasoning provider.

#### Scenario: Vision provider selected for image-related message
- **WHEN** a user message contains "图片", "照片", "图像", "识别", "OCR", or "上传"
- **THEN** the system SHALL route the request to the MiMo vision-capable LLM provider

#### Scenario: Default provider selected for text message
- **WHEN** a user message contains only text without any vision-related keywords
- **THEN** the system SHALL route the request to the default reasoning LLM provider

### Requirement: Planner goal decomposition

The system SHALL decompose every user message into a structured Plan before entering the ReAct loop, using an LLM call with the available tool list. Single-intent messages SHALL fall back to a single-step Plan. A Plan SHALL contain at most 6 steps, each with step number, skill name, arguments, dependencies, and description. Failed LLM calls or parse errors SHALL produce a single-step fallback Plan via keyword matching.

#### Scenario: Complex goal decomposed into steps
- **WHEN** a user sends "诊断三班的氧化还原掌握情况，然后给薄弱学生出针对性练习题"
- **THEN** the Planner SHALL return a multi-step Plan with diagnose_barrier (step 1) and generate_questions (step 2, depends_on=[1])

#### Scenario: Single-intent message produces single-step Plan
- **WHEN** a user sends "出5道氧化还原选择题"
- **THEN** the Planner SHALL fall back to a single-step Plan containing show_exam_workbench or generate_questions

#### Scenario: LLM failure triggers keyword fallback
- **WHEN** the Planner LLM call fails or returns unparseable output
- **THEN** the system SHALL build a single-step Plan by matching Chinese keywords against available tools

#### Scenario: Step dependency injection
- **WHEN** step 2's args contain `${step_1.student_id}`
- **THEN** the system SHALL replace the placeholder with the actual value from step 1's execution result before invoking step 2

### Requirement: ReAct Agent engine (v2 single-Agent)

The system SHALL use LangGraph create_react_agent to run a single ReAct loop. The Agent SHALL receive the full tool set filtered by the active Persona (via intersection of Persona YAML available_skills and TOOL_META registration), and SHALL select tools autonomously based on their docstrings. The recursion limit SHALL be 12. Checkpoint persistence SHALL use AsyncSqliteSaver backed by a dedicated SQLite database.

#### Scenario: Agent selects correct tool from filtered set
- **WHEN** the Teacher persona Agent receives "诊断一下张三的化学学习障碍"
- **THEN** the Agent SHALL select diagnose_barrier from the available Teacher tool set within the first 2 ReAct rounds

#### Scenario: Agent runs multiple tools in sequence
- **WHEN** the user requests an action chain like "搜索真题 → 出题 → 保存题库"
- **THEN** the Agent SHALL execute search_exam_bank, then generate_questions, then save_to_bank in that order

#### Scenario: Recursion limit exhausted
- **WHEN** the ReAct loop reaches 12 iterations without producing a final response
- **THEN** the system SHALL send an SSE error event with message "处理超时，Agent重试次数用尽。请重试或换个方式提问。" and terminate the stream

#### Scenario: Checkpoint saved after each Agent invocation
- **WHEN** the Agent completes a tool execution or generates text
- **THEN** the system SHALL persist the updated conversation state to the checkpoint SQLite database

### Requirement: Guard four-layer safety

The system SHALL wrap every tool invocation in a four-layer Guard check executing in order: (L1) prerequisite parameter validation, (L2) per-conversation call limit enforcement, (L3) duplicate call detection by tool name + sorted args, (L4) approval gating for destructive operations. Guard metadata (call_limit, requires_approval, prerequisites) SHALL be read from the TOOL_META registry. The GuardState SHALL be request-scoped—a new instance per Agent call.

#### Scenario: Missing prerequisites blocked
- **WHEN** search_exam_bank is called with keyword length ≤ 2 characters
- **THEN** the system SHALL return error "missing_prerequisites" and the LLM SHALL ask the user for more specific search terms

#### Scenario: Call limit exceeded
- **WHEN** assign_adaptive_practice is called a second time in the same conversation
- **THEN** the system SHALL return error "limit_exceeded" and the LLM SHALL proceed with the result from the first call

#### Scenario: Duplicate call skipped
- **WHEN** the same tool with the same sorted arguments is called twice in the same request
- **THEN** the system SHALL return error "dedup_skipped" and skip execution

#### Scenario: Destructive operation blocked pending approval
- **WHEN** delete_bank is called without prior approval
- **THEN** the system SHALL return error "requires_approval_blocked", pause the Agent, and emit an SSE phase event with state "awaiting_approval"

#### Scenario: Approved operation proceeds
- **WHEN** the user confirms the approval card and the resume endpoint is called
- **THEN** the Agent SHALL resume from the checkpoint and re-execute the previously blocked tool call

### Requirement: SSE event adapter

The system SHALL convert Agent execution progress into a structured SSE event stream with exactly 10 event types: phase, tool_call, tool_result, text, component, navigate, populate, action, exam_images, error, and done. The adapter SHALL strip `_component` and `_route` fields from tool return values at the Guard layer, routing them to SSE component/navigate events respectively while returning only business data to the LLM. The adapter SHALL implement text deduplication—when LLM streamed text overlaps > 70% with the previous tool_result content, the overlapping portion SHALL be skipped.

#### Scenario: Full event sequence for a tool-invoking message
- **WHEN** a user message triggers a tool call
- **THEN** the SSE stream SHALL emit events in order: phase(thinking) → tool_call → phase(executing) → tool_result → phase(reply) → text (streaming) → done

#### Scenario: _component field stripped and emitted as SSE event
- **WHEN** show_exam_workbench returns `{result: "ok", _component: {type: "exam-workbench", params: {...}}}`
- **THEN** the SSE adapter SHALL emit a component event with the _component data and return only `{result: "ok"}` to the LLM

#### Scenario: _route field stripped and emitted as navigate event
- **WHEN** a tool returns `{result: "ok", _route: {page: "exam-v2", params: {...}}}`
- **THEN** the SSE adapter SHALL emit a navigate event and return only `{result: "ok"}` to the LLM

#### Scenario: Text dedup skips echoed tool output
- **WHEN** an LLM text stream begins with content that overlaps > 70% with the previous tool_result
- **THEN** the overlapping portion SHALL NOT be sent as text SSE events

#### Scenario: Tutor tool marks response as complete
- **WHEN** a tutoring tool returns JSON containing "guidance" or "step" keys
- **THEN** the SSE adapter SHALL mark the response as complete and skip all subsequent LLM text for that round

### Requirement: Dependency injection container

The system SHALL provide a dependency injection container (AgentContext) holding student_id, student_profile, persona, episodic memory, and provider_name, accessible to all tool functions during execution.

#### Scenario: Tool accesses student context during execution
- **WHEN** diagnose_barrier is invoked for a Teacher persona session with a specific student_id
- **THEN** the tool SHALL be able to read student_id and persona from AgentContext without receiving them as explicit function parameters

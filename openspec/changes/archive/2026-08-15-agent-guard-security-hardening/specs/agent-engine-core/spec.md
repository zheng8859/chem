## MODIFIED Requirements

### Requirement: Guard four-layer safety

The system SHALL enforce a layered Guard check on every tool invocation within the ReAct loop, executing inline before the tool function is called, in this order: (L0) cross-role interception and registry validation, (L1) prerequisite parameter validation, (L2) per-conversation call limit enforcement, (L3) duplicate call detection by tool name + sorted args, (L4) approval gating for destructive operations. Guard metadata (call_limit, requires_approval, prerequisites, prerequisite_any_of, prerequisite_min_length, persona) SHALL be read from the TOOL_META registry. The GuardState SHALL be request-scoped—a new instance per Agent call—and SHALL persist the calling user's user_id for downstream ownership checks. A tool call that fails any layer SHALL NOT execute its tool function; the rejection reason SHALL be returned to the LLM as a structured error so the LLM can adapt.

L0 SHALL reject a tool call whose tool is absent from the TOOL_META registry (fail-closed), and SHALL reject a call where the tool's declared persona allow-list does not include the active persona. When the Guard wrapper cannot read a valid guard_state from the request, it SHALL refuse to execute the tool (fail-closed) rather than skipping the Guard checks.

L1 prerequisite validation SHALL reject missing parameters, empty-string parameters, parameters failing a declared length threshold (e.g., search_exam_bank `keyword` length < 3), and SHALL support OR-conditions where at least one of several parameters must be present (e.g., `diagnose_barrier` requires `student_id` OR `class_id` OR `student_name`). For presence checks, the numeric value 0 SHALL be treated as "not provided" only for ID-sentinel parameters, matching the convention that an ID of 0 is meaningless; this convention SHALL be documented in the guard module.

#### Scenario: Missing prerequisites blocked
- **WHEN** search_exam_bank is called with keyword length < 3 characters
- **THEN** the system SHALL return error "missing_prerequisites" and the LLM SHALL ask the user for more specific search terms

#### Scenario: OR-condition prerequisite validated
- **WHEN** diagnose_barrier is called with neither student_id nor class_id nor student_name present
- **THEN** the system SHALL return error "missing_prerequisites" and SHALL NOT execute the tool

#### Scenario: Call limit exceeded
- **WHEN** assign_adaptive_practice is called a second time in the same conversation
- **THEN** the system SHALL return error "limit_exceeded" and the LLM SHALL proceed with the result from the first call

#### Scenario: Duplicate call skipped
- **WHEN** the same tool with the same sorted arguments is called twice in the same request
- **THEN** the system SHALL return error "dedup_skipped" and skip execution

#### Scenario: Destructive operation blocked pending approval
- **WHEN** delete_bank is called without prior approval
- **THEN** the system SHALL pause the Agent before the tool executes, return error "requires_approval_blocked", emit an SSE phase event with state "awaiting_approval", and SHALL NOT execute the tool until the resume endpoint confirms approval

#### Scenario: Approved operation proceeds
- **WHEN** the user confirms the approval card and the resume endpoint is called with decision "approved"
- **THEN** the Agent SHALL resume from the interrupted state and execute the previously blocked tool call

#### Scenario: Rejected operation cancelled
- **WHEN** the user cancels the approval card and the resume endpoint is called with decision "rejected"
- **THEN** the Agent SHALL resume, inform the user the operation was cancelled, and SHALL NOT execute the blocked tool call

#### Scenario: Cross-role tool call blocked at L0
- **WHEN** a tool whose persona allow-list excludes the active persona is invoked (bypassing tool-set filtering)
- **THEN** the system SHALL reject the call with an L0 error and SHALL NOT execute the tool function

#### Scenario: Unregistered tool blocked fail-closed
- **WHEN** a tool call references a tool name not present in the TOOL_META registry
- **THEN** the system SHALL reject the call (fail-closed) and SHALL NOT execute the tool function

#### Scenario: Missing guard state refused fail-closed
- **WHEN** the Guard wrapper cannot read a valid guard_state from the request state
- **THEN** the system SHALL refuse to execute the tool and return a structured error, rather than bypassing the Guard checks

### Requirement: SSE event adapter

The system SHALL convert Agent execution progress into a structured SSE event stream with exactly 10 event types: phase, tool_call, tool_result, text, component, navigate, populate, action, exam_images, error, and done. The adapter SHALL strip `_component` and `_route` fields from tool return values at the Guard layer, routing them to SSE component/navigate events respectively while returning only business data to the LLM. Stripping SHALL handle tool results whose content is a JSON string OR a plain dict object, so that a tool returning a dict (rather than a pre-serialized string) does not leak `_component`/`_route` to the LLM or suppress the component/navigate events. The `_component` payload SHALL contain a `type` field (the component name) and an optional `props` field (component payload). The navigate event payload SHALL carry `page` and `params` at the top level (not wrapped in a `route` key). The adapter SHALL implement text deduplication—when LLM streamed text overlaps > 70% with the previous tool_result content, the overlapping portion SHALL be skipped. Stripped component/navigate payloads SHALL be cleared from GuardState after emission so subsequent resume streams do not re-emit them.

#### Scenario: Full event sequence for a tool-invoking message
- **WHEN** a user message triggers a tool call
- **THEN** the SSE stream SHALL emit events in order: phase(thinking) → tool_call → phase(executing) → tool_result → phase(reply) → text (streaming) → done

#### Scenario: _component field stripped and emitted as SSE event
- **WHEN** show_exam_workbench returns `{result: "ok", _component: {type: "exam-workbench", props: {...}}}`
- **THEN** the SSE adapter SHALL emit a component event with the _component data and return only `{result: "ok"}` to the LLM

#### Scenario: _route field stripped and emitted as navigate event
- **WHEN** a tool returns `{result: "ok", _route: {page: "exam-v2", params: {...}}}`
- **THEN** the SSE adapter SHALL emit a navigate event whose payload carries `page` and `params` at the top level, and return only `{result: "ok"}` to the LLM

#### Scenario: Dict-form tool result stripped
- **WHEN** a tool returns a ToolMessage whose content is a dict `{result: "ok", _component: {type: "exam-workbench"}}` rather than a JSON string
- **THEN** the Guard SHALL strip `_component` into GuardState, emit a component event, and return only `{result: "ok"}` to the LLM

#### Scenario: Text dedup skips echoed tool output
- **WHEN** an LLM text stream begins with content that overlaps > 70% with the previous tool_result
- **THEN** the overlapping portion SHALL NOT be sent as text SSE events

#### Scenario: Tutor tool marks response as complete
- **WHEN** a tutoring tool returns JSON containing "guidance" or "step" keys
- **THEN** the SSE adapter SHALL mark the response as complete and skip all subsequent LLM text for that round

#### Scenario: Stripped fields not re-emitted on resume
- **WHEN** a component/navigate payload has been emitted once and the stream is later resumed
- **THEN** the resumed stream SHALL NOT re-emit the already-emitted component/navigate events

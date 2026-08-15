## MODIFIED Requirements

### Requirement: SSE event adapter

The system SHALL convert Agent execution progress into a structured SSE event stream with exactly 10 event types: phase, tool_call, tool_result, text, component, navigate, populate, action, exam_images, error, and done. The adapter SHALL strip `_component` and `_route` fields from tool return values at the Guard layer, routing them to SSE component/navigate events respectively while returning only business data to the LLM. The `_component` payload SHALL contain a `type` field (the component name) and an optional `props` field (component payload). The navigate event payload SHALL carry `page` and `params` at the top level (not wrapped in a `route` key). The adapter SHALL implement text deduplication—when LLM streamed text overlaps > 70% with the previous tool_result content, the overlapping portion SHALL be skipped.

#### Scenario: Full event sequence for a tool-invoking message
- **WHEN** a user message triggers a tool call
- **THEN** the SSE stream SHALL emit events in order: phase(thinking) → tool_call → phase(executing) → tool_result → phase(reply) → text (streaming) → done

#### Scenario: _component field stripped and emitted as SSE event
- **WHEN** show_exam_workbench returns `{result: "ok", _component: {type: "exam-workbench", props: {...}}}`
- **THEN** the SSE adapter SHALL emit a component event with the _component data and return only `{result: "ok"}` to the LLM

#### Scenario: _route field stripped and emitted as navigate event
- **WHEN** a tool returns `{result: "ok", _route: {page: "exam-v2", params: {...}}}`
- **THEN** the SSE adapter SHALL emit a navigate event whose payload carries `page` and `params` at the top level, and return only `{result: "ok"}` to the LLM

#### Scenario: Text dedup skips echoed tool output
- **WHEN** an LLM text stream begins with content that overlaps > 70% with the previous tool_result
- **THEN** the overlapping portion SHALL NOT be sent as text SSE events

#### Scenario: Tutor tool marks response as complete
- **WHEN** a tutoring tool returns JSON containing "guidance" or "step" keys
- **THEN** the SSE adapter SHALL mark the response as complete and skip all subsequent LLM text for that round

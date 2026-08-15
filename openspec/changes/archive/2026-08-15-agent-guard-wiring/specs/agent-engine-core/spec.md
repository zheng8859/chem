## MODIFIED Requirements

### Requirement: Guard four-layer safety

The system SHALL enforce a four-layer Guard check on every tool invocation within the ReAct loop, executing inline before the tool function is called: (L1) prerequisite parameter validation, (L2) per-conversation call limit enforcement, (L3) duplicate call detection by tool name + sorted args, (L4) approval gating for destructive operations. Guard metadata (call_limit, requires_approval, prerequisites) SHALL be read from the TOOL_META registry. The GuardState SHALL be request-scoped—a new instance per Agent call. A tool call that fails any layer SHALL NOT execute its tool function; the rejection reason SHALL be returned to the LLM as a structured error so the LLM can adapt. L1 prerequisite validation SHALL reject missing parameters, empty-string parameters, parameters failing a declared length threshold (e.g., search_exam_bank `keyword` length ≤ 2), and SHALL support OR-conditions where at least one of several parameters must be present (e.g., `diagnose_barrier` requires `student_id` OR `class_id`).

#### Scenario: Missing prerequisites blocked
- **WHEN** search_exam_bank is called with keyword length ≤ 2 characters
- **THEN** the system SHALL return error "missing_prerequisites" and the LLM SHALL ask the user for more specific search terms

#### Scenario: OR-condition prerequisite validated
- **WHEN** diagnose_barrier is called with neither student_id nor class_id present
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

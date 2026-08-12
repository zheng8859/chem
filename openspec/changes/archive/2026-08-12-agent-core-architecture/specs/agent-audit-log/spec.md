## Purpose

Records all Agent tool executions in a structured audit log for debugging, compliance, and quality analysis, using an in-memory ring buffer and JSONL file append with best-effort write semantics.

## ADDED Requirements

### Requirement: Audit log entry structure

The system SHALL record each tool execution as a JSON object with fields: timestamp (ISO 8601), persona (current role), skill_name (tool name), args (with sensitive fields redacted), result_summary (truncated to 200 characters), duration_ms (float), and error (optional string, present only on failure).

#### Scenario: Successful tool execution logged
- **WHEN** search_exam_bank completes in 450ms with 5 results
- **THEN** the audit log SHALL contain an entry with skill_name="search_exam_bank", duration_ms=450.0, result_summary truncated to 200 chars, and no error field

#### Scenario: Failed tool execution logged
- **WHEN** diagnose_barrier throws an exception
- **THEN** the audit log SHALL contain an entry with skill_name="diagnose_barrier", error containing the exception message, and duration_ms recorded

### Requirement: Sensitive field redaction

The system SHALL redact the values of sensitive argument fields (password, phone, parent_phone, token, api_key, secret) by replacing them with "***" before writing to the audit log.

#### Scenario: Password field redacted
- **WHEN** a tool is called with args containing `{"password": "secret123", "name": "test"}`
- **THEN** the audit log SHALL record `{"password": "***", "name": "test"}`

### Requirement: Ring buffer and file persistence

The system SHALL maintain an in-memory ring buffer (deque, maxlen=100) of recent audit entries and SHALL append each entry as a JSON line to a disk file at data/audit/agent_audit.jsonl. Both operations SHALL use best-effort—any write failure SHALL be silently caught and logged without blocking the main Agent flow.

#### Scenario: Buffer wraps at 100 entries
- **WHEN** 101 tool calls have been executed
- **THEN** the ring buffer SHALL contain the 100 most recent entries (oldest entry dropped)

#### Scenario: Disk write failure does not block
- **WHEN** appending to the JSONL file fails due to disk full
- **THEN** the tool execution SHALL complete successfully and the error SHALL be logged without raising an exception

### Requirement: Audit logger singleton

The system SHALL provide a process-wide singleton AuditLogger instance, initialized at application startup, accessible to all Guard-wrapped tool invocations.

#### Scenario: AuditLogger accessible during tool execution
- **WHEN** any tool is executed through the Guard layer
- **THEN** the tool SHALL be able to log its execution via the singleton AuditLogger without importing or creating a new instance

## Context

See proposal.md for motivation and scope.

**Current architecture**: FastAPI + SQLAlchemy async + LangGraph Agent. The backend uses a 3-layer auth model (middleware → `get_current_user` → `require_permission`), but student self-data access currently relies on ad-hoc `resolve_student_id` calls without consistent role enforcement.

**New tables needed**: `LearningPlan` + `LearningPlanTask` (1:N), `Notification` (standalone). All use the existing `Base` declarative model and Alembic migration flow.

**Agent infrastructure**: LangGraph ReAct agent v2 with Persona YAML configs + tool metadata registry. The `memory_student_get` tool exists but Store is not populated. The tutoring tools follow a factory pattern.

## Goals / Non-Goals

**Goals:**
- Expose student self-view data (stats, diagnosis, learning plan, notifications) through consistent REST endpoints
- Auto-create notifications when teachers perform key actions
- Populate LangGraph Store with diagnosis + plan data for Agent context
- Inject student profile into Agent System Message for personalized conversations
- Register 2 missing chemistry tutoring tools
- Enforce student self-data isolation via shared dependency `require_student_self`

**Non-Goals:**
- No student-facing UI changes (this change is backend only)
- No new external dependencies
- No real-time push notifications (poll-based only)
- No teacher-to-student manual messaging
- No knowledge heatmap endpoint (deferred)

## Decisions

### D1: Student self-data authorization — shared dependency over per-endpoint checks

**Chosen**: New `require_student_self(student_id: int, user: UserContext, db: AsyncSession) -> int` dependency that verifies the user is a student, maps Account.id → Student.id, and enforces `user.user_id == student_id`. Returns the database `Student.id`.

**Rationale**: Avoids duplicating the same check across 8+ new endpoints. Consistent error responses (403). Composable with existing `get_current_user`.

**Alternatives considered**: Extending `ROLE_PERMISSIONS` matrix with `self_data` pseudo-resource — rejected because the matrix is resource×action, not resource×owner.

### D2: Learning plan model — one active plan per student

**Chosen**: `LearningPlan` table with `is_active` boolean. On creation, the service sets all existing active plans for the student to `is_active=false` in the same transaction. Tasks stored as child `LearningPlanTask` rows.

**Rationale**: Matches the product design (teacher assigns, student executes). Simple query: `WHERE student_id = ? AND is_active = true`.

**Alternatives considered**: Version-numbered plans (plan v1, v2...) — rejected because there's no requirement to view historical plan data through REST. Single mutable plan per student — rejected because we need an audit trail of past plans.

### D3: Notification trigger — inline hook vs. event bus

**Chosen**: Inline best-effort write in the service method. When `PracticeService.create_practice` succeeds, it calls `NotificationService.create(...)` wrapped in try/except. Same for `LearningPlanService`.

**Rationale**: No event bus infrastructure exists. The project's architecture principle is "SQLite state tables, not message queues" (see CLAUDE.md §6.9). Inline writes are simple and sufficient for MVP scale.

**Alternatives considered**: FastAPI background tasks — rejected because they don't participate in the DB transaction and can fire even when the parent operation rolls back. APScheduler polling — rejected as overengineered for this use case.

### D4: Agent student context injection — direct DB read vs. REST call

**Chosen**: Direct database/SQLAlchemy query inside the Agent factory function's `_build_system_prompt`. When persona is "student", query diagnosis, stats, and learning plan from the database and format into the System Message.

**Rationale**: Agent and REST API share the same process and DB connection pool. Avoiding REST calls eliminates latency (Agent already has DB access through the checkpointer) and prevents circular dependency (Agent → REST → Agent).

**Alternatives considered**: REST API call from Agent to `/api/v1/diagnosis/student/{id}` etc. — rejected because of added HTTP overhead and architectural layering concerns (Agent shouldn't depend on REST layer).

### D5: Store write — diagnosis pipeline hook point

**Chosen**: Add a best-effort Store write after the existing `Student.barrier_profile` update in `DiagnosisService`. Use the existing `AsyncSqliteStore` instance (already initialized as a module-level singleton).

**Rationale**: The Store is already declared and initialized (see Agent design §9.5), just not written to. Minimal code change — one `store.put(...)` call inside try/except.

### D6: Tutoring tool registration — factory pattern reuse

**Chosen**: Create `periodic_law_tutor` and `organic_tutor` using the existing `_make_tutoring_tool` factory function, with 7 parameters (name, title, step_guidance, step2_guidance, docstring, default_msg, step_titles). Register in TOOL_META with `persona=["student"]` and `call_limit=5`. Add to Student persona's YAML `available_skills`.

## Risks / Trade-offs

- **[Store write failure]** → Mitigation: Best-effort pattern; logged but never blocks. The main spec (diagnosis profile in `Student.barrier_profile`) is the source of truth; Store is a cache for Agent convenience.
- **[Notification table growth]** → Mitigation: 30-day retention with scheduled cleanup (can reuse existing APScheduler). At ~50 students × ~5 notifications/week, negligible for MVP.
- **[System Message token budget]** → Mitigation: Student profile injection is capped at ~500 tokens. The existing context trimming (30-message threshold, §8 of Agent design) already handles overflow.
- **[DB migration ordering]** → Mitigation: New tables have no FK to existing tables beyond `student_id`. Migration is additive only.

## Migration Plan

1. Run Alembic migration to create `learning_plans`, `learning_plan_tasks`, `notifications` tables
2. Deploy new code (backward compatible — all new endpoints are additive)
3. No data migration needed (tables start empty)
4. Rollback: revert code, optionally drop new tables

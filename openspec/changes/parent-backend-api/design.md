## Context

The ChemAI project already has:
- **Data models**: Account, Parent, Student (with `bind_code`), StudentParentBinding, ParentNotification, Notification — all defined in `app/models/user.py` and `app/models/homework.py`
- **Auth**: Unified phone login supporting all three roles, parent registration with bind_code validation at `POST /api/auth/register/parent`
- **Agent**: v2 ReAct engine with Parent persona (tools: `weekly_report`, `diagnose_barrier`, `memory_student_get`, `web_search`, 5 browser tools) — defined in document 30
- **Scheduler**: `_run_notify_parents()` Cron at 20:00 for overdue review notifications
- **Student-side notification API**: `app/api/v1/notification.py` with student self-data isolation
- **Homework API**: `app/api/v1/homework.py` with binding CRUD and parent notification CRUD mixed with teacher report routes

The existing parent-related code is fragmented across three route files (`user.py`, `homework.py`, `notification.py`) with no dedicated parent service layer. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Consolidate all parent-facing REST endpoints under a single `app/api/v1/parent.py` router with prefix `/api/v1/parent`
- Migrate binding and parent notification routes out of `homework.py`
- Add student-side bind code registration endpoint
- Build child data aggregation service (practice stats, barrier distribution, learning timeline)
- Build weekly report generation service with LLM prompt engineering and DB caching
- Add parent Agent SSE endpoint reusing existing v2 ReAct engine
- Add `require_parent_binding()` permission dependency
- Align `ParentNotification` fields and expand `NotificationType` enum

**Non-Goals:**
- External LMS connectors (DingTalk, WeCom, LTI 1.3, SFTP, Webhook)
- New Agent tools beyond the Parent persona's existing 9-tool set
- Parent registration without bind code (bind code remains mandatory)
- Real-time WebSocket — SSE is used for Agent, REST for everything else

## Decisions

### D1: Single parent router file at `/api/v1/parent`

Parent endpoints are currently scattered across `user.py` (admin CRUD), `homework.py` (bindings, notifications, reports), and `auth.py` (registration). All new and migrated parent-facing endpoints consolidate into `app/api/v1/parent.py` with `APIRouter(prefix="/parent", tags=["parent"])`.

**Why**: Single file for discoverability and consistent auth checking. Existing admin CRUD at `/parents` (in `user.py`) remains — it serves admin management, not the parent-facing API.

**Alternatives considered**: Separate files per sub-domain (parent_bind.py, parent_report.py, etc.) — rejected because the parent API surface is small (~12 endpoints) and splitting would add navigation overhead without benefit.

### D2: Dedicated ParentService + WeeklyReportService

Two new service classes rather than extending HomeworkService:

- `ParentService` — child data aggregation, binding operations (migrated from HomeworkService), parent notification CRUD (migrated from HomeworkService)
- `WeeklyReportService` — LLM prompt construction, report generation, DB caching/dedup

**Why**: HomeworkService already handles exam reports and binding logic. Adding child data aggregation and weekly reports would make it a god class. Separate services keep responsibilities clear and testable.

**Alternatives considered**: Extend HomeworkService — rejected due to growing scope; Single ParentService for everything — rejected because weekly report generation involves LLM calls and has different error handling (retry, fallback) than DB CRUD.

### D3: WeeklyReport as a new DB model

Rather than storing weekly reports in ParentNotification.body or generating fresh each time, a dedicated `WeeklyReport` table is created:

```python
class WeeklyReport(Base, TimestampMixin):
    __tablename__ = "weekly_report"
    id: int (PK)
    student_id: int (FK → student.id)
    week_start: date
    week_end: date
    summary: str (≤60 chars)
    detail: str (≤120 chars)
    advice: str (≤80 chars)
    no_data: bool
    generated_at: datetime
    generated_by: str  # "auto" | "manual"
    __table_args__ = (UniqueConstraint("student_id", "week_start"),)
```

**Why**: DB caching enables idempotent generation (same request within a week returns cached report) and historical lookup. Storing in ParentNotification.body would mix notification concerns with report data.

**Alternatives considered**: No storage — rejected because design doc requires dedup; Redis cache — rejected because project doesn't use Redis and reports are infrequent (weekly/student) making DB caching sufficient.

### D4: ParentAgentService wrapping existing Agent engine

Parent agent SSE endpoint wraps the existing v2 ReAct engine factory (`app/agent/`), not a separate LLM call path:

```
POST /api/v1/parent/agent/chat
  → resolve parent's selected child from request context
  → inject {student_context} into Parent persona system prompt
  → create_react_agent(persona="parent", tools=parent_tools)
  → stream SSE events
```

**Why**: Reuses existing Guard (4-layer safety), Gateway (intent classification), context management, checkpointer, and audit logging. The Parent persona and its tools already exist in the agent registry.

**Alternatives considered**: Direct LLM completion — rejected because it wouldn't support tool use or multi-turn conversation; New standalone agent — rejected because it would duplicate the engine infrastructure.

### D5: Two migration types for enum changes

`NotificationType` enum expansion (3 → 8 values: 5 new parent types + 3 existing) and `ParentNotification` field changes (is_read → read_at) are handled as:

- **SQLite-compatible**: is_read column dropped, read_at added (via Alembic migration with column rename + data migration)
- **Enum expansion**: Uses SQLAlchemy `String(30)` not native enum, so new values can be added without DDL changes
- **Backward compatibility**: Existing ParentNotification records with is_read=true have their created_at set as read_at during migration

### D6: `require_parent_binding()` as a dependency factory

```python
def require_parent_binding():
    """Factory: validates parent has active binding to {student_id} in URL path.
    
    Returns (parent_db_id, student_db_id) for service layer use.
    Steps:
    1. Verify JWT role == "parent"
    2. Resolve Account.id → Parent.id
    3. Extract student_id from URL path params
    4. Query StudentParentBinding(student_id, parent_id, status=active)
    5. Return (parent_db_id, student_db_id) or raise 403
    """
```

**Why**: Consistent with existing `require_student_self()` pattern in deps.py. Factory pattern allows FastAPI dependency injection at the route level.

### D7: Route consolidation plan

| Old route (homework.py) | New route (parent.py) | Migration |
|--------------------------|----------------------|-----------|
| POST /bindings | POST /parent/bind | Direct delete + create |
| GET /bindings | GET /parent/children | Direct delete (different response shape) |
| DELETE /bindings/{id} | DELETE /parent/bind/{id} | Direct delete + create |
| GET /notifications | GET /parent/notifications | Direct delete + create |
| POST /notifications/{id}/read | PUT /parent/notifications/{id}/read | Direct delete + create |

No frontend code calls any of these old routes (verified by grep). No redirects needed.

## Risks / Trade-offs

- **[Risk] LLM weekly report quality varies by provider** → Mitigation: Structured JSON output format with field length constraints (summary ≤60, detail ≤120, advice ≤80 chars). no_data short-circuit avoids LLM call entirely when student has no practice data.
- **[Risk] Weekly report Cron may spike LLM costs** → Mitigation: Cron fires Monday 08:00 but only for students with active parent bindings AND practice activity that week. Estimated: ~10-50 reports/week for initial deployment, not thousands.
- **[Risk] ParentNotification retention (90 days) differs from student Notification (30 days)** → Acceptable: parent usage is monthly (2-4 times), so 30 days would expire notifications before the parent sees them.
- **[Risk] Migration deletes homework.py routes without warning** → Mitigation: Zero frontend consumers confirmed. Test files updated as part of tasks.md.
- **[Trade-off] `related_id` on ParentNotification is polymorphic (can reference different entity types)** → Acceptable: Same pattern as Notification.related_id. No FK constraint for flexibility at the cost of referential integrity.

## Migration Plan

1. Create new files (parent.py, parent_service.py, weekly_report_service.py, schemas/parent.py, WeeklyReport model)
2. Add `require_parent_binding()` to deps.py
3. Expand NotificationType enum
4. Create Alembic migration for ParentNotification field changes + WeeklyReport table
5. Update homework.py: remove binding and notification routes, keep only `POST /reports/send-to-students/{exam_id}`
6. Update main.py: add `include_router(parent_router)`
7. Update test files: redirect old route references to new paths
8. Add Cron job for weekly report generation (scheduler.py)

Rollback: Revert the commit. Data migration is additive (new columns, new table), so rollback is a simple Alembic downgrade.

## Open Questions

None. All design decisions were resolved during the grilling session (9 decisions aligned with user).

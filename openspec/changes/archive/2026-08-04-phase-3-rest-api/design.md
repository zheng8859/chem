## Context

Phase 2 established 27 SQLAlchemy models, 60+ Pydantic schemas, JWT auth, and RBAC middleware. The `app/api/v1/` directory currently contains only `auth.py` (login/register/refresh). `app/services/` has only `auth_service.py`. The schema layer (`app/schemas/`) is comprehensive — all Create/Read/Update models and business request/response shapes are already defined.

The API layer is the missing link between the data models and any consumer (frontend, Agent tools, MCP server).

## Goals / Non-Goals

**Goals:**
- Full CRUD endpoints for all 27 tables across 7 domain modules
- Consistent REST conventions: URL structure, status codes, error format, pagination
- Multi-tenant data isolation enforced at the service layer
- RBAC enforcement via existing `require_permission` dependency on every protected endpoint
- Reuse existing Pydantic schemas without duplication

**Non-Goals:**
- WebSocket or real-time endpoints (not in scope for REST API phase)
- Agent chat/SSE endpoints (Phase 4 — Agent system)
- LLM pipeline implementation (stub only — actual pipelines built in later phases)
- File upload handling for OCR (endpoint defined, actual file processing stubbed)
- MCP tool server endpoints (separate module: `app/api/mcp/`)

## Decisions

### 1. Router organization: one file per domain

**Choice:** 7 router files under `app/api/v1/` — `org.py`, `user.py`, `teaching.py`, `diagnosis.py`, `homework.py`, `ocr.py`, `question_bank.py` — plus an `__init__.py` that aggregates them into a single `v1_router`.

**Why:** Matches the existing models/ and schemas/ directory structure. Each file is self-contained and ~100-200 lines. A single monolithic router would be unmanageable. Each router file has its own `prefix` and `tags` for OpenAPI grouping.

**Alternative considered:** One router per entity (20+ files). Rejected — too granular; closely related entities (e.g., School + Grade + Class) share query patterns and are naturally co-located.

### 2. Service layer: thin routers, logic in services

**Choice:** Each domain gets a service file in `app/services/` (e.g., `org_service.py`). Routers handle HTTP concerns (status codes, response wrapping) and delegate to services for database operations.

**Why:** Follows the existing `auth_service.py` pattern. Keeps routers testable in isolation (mock the service). Enables Agent tools to call services directly without going through HTTP.

**Pattern:**
```
router → service function (AsyncSession, Pydantic models) → SQLAlchemy query
router returns SuccessResponse[data] or ErrorResponse
```

### 3. URL structure: mixed nested/flat

**Choice:** Nest where parent context is required, flat otherwise.

| Pattern | Example |
|---------|---------|
| Nested | `/schools/{id}/grades`, `/grades/{id}/classes`, `/classes/{id}/students` |
| Flat | `/exams`, `/questions`, `/knowledge-points`, `/bindings` |
| Scoped by query param | `/exams?class_id={id}`, `/warnings?class_id={id}` |

**Why:** Nesting enforces the org hierarchy constraint at the URL level (you can't list classes without specifying a grade). Flat with query params is more flexible for entities that can be filtered across multiple dimensions.

### 4. Multi-tenant data isolation

**Choice:** Service-layer filtering. Every query that returns school-scoped data checks `UserContext.school_id` and applies the appropriate JOIN/filter chain.

**Why:** The RBAC matrix in `deps.py` already authorizes by resource+action. Data-level isolation (ensuring teacher A can't see school B's students) is enforced in the service, not middleware, because the filtering logic varies by entity (some filter by school_id, some by teacher's assigned classes).

**Pattern:**
```python
async def list_students(db, class_id, user: UserContext):
    # Verify class belongs to user's school
    cls = await get_class(db, class_id)
    await verify_school_access(db, cls.grade_id, user.school_id)
    # Query scoped to class
    return await db.execute(select(Student).where(Student.class_id == class_id))
```

### 5. Pagination: consistent offset/limit

**Choice:** All list endpoints accept `limit` (default 20, max 100) and `offset` (default 0) query params, returning `PaginatedResponse[Item]` with `items`, `total`, `limit`, `offset`.

**Why:** Reuses the existing `PaginationParams` and `PaginatedResponse` from `schemas/base.py`. Cursor-based pagination is unnecessary for the expected data volumes (classroom scale, not internet scale).

### 6. Error handling

**Choice:** Use FastAPI `HTTPException` with consistent Chinese error messages. 404 for not-found, 400 for validation, 403 for permission denied, 401 for unauthenticated.

**Why:** The existing `ErrorResponse` schema is available for structured errors. Chinese messages match the existing auth endpoints and the product's primary user base.

### 7. Stub strategy for LLM-dependent endpoints

**Choice:** Endpoints that depend on LLM pipelines (AI question generation, LLM grading, adaptive practice assignment, OCR processing) are implemented as stubs that return valid response shapes with placeholder data and a "not implemented" warning in the response message.

**Why:** Unblocks frontend integration and API contract testing without requiring the full LLM infrastructure. The response shapes are contractually stable; only the internal implementation changes later.

## Risks / Trade-offs

- **[Risk] Router files grow too large** → Mitigation: each domain router is ~150 lines; split into sub-routers if any exceeds 300 lines.
- **[Risk] N+1 queries in nested responses** → Mitigation: use SQLAlchemy `selectinload` for eager loading; add query count assertions in integration tests.
- **[Risk] Stub endpoints mask missing functionality** → Mitigation: every stub response includes `"warning": "功能开发中"` in the message field; integration tests assert the warning is present until the real implementation replaces it.
- **[Trade-off] Mixed URL patterns (nested + flat)** → Some inconsistency is acceptable because it reflects genuine domain constraints (org hierarchy is strict; exam filtering is flexible).

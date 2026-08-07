## Context

The `chemai-backend` has 7 existing SQLAlchemy model files, a basic JWT auth service, and an RBAC permission matrix in `deps.py`. A 45-question domain-modeling grilling session identified misalignments between the code, the CONTEXT.md glossary, and the authentication contracts. This design resolves those misalignments with specific technical decisions.

See `proposal.md` for the full motivation and change list.

The project uses: SQLAlchemy 2.0 (async), FastAPI, SQLite (WAL mode), bcrypt + jose for JWT, Alembic for migrations.

## Goals / Non-Goals

**Goals:**
- Align all 9 model files with the domain glossary exactly
- Unify authentication to phone-based login across all three roles
- Implement JWT payload carrying both identity role and permission sub-role
- Add the new ExamPaper entity with a two-layer exam lifecycle
- Add the 3×6 diagnosis matrix fields to StudentAnswer
- Add PracticeSession and variant question tracking
- Keep the existing RBAC matrix in deps.py operational with the new sub_role field

**Non-Goals:**
- Frontend changes (login pages, student activation UI) — they are downstream consumers of the stabilized API contracts
- ChromaDB vector retrieval changes — knowledge graph hierarchy via parent_id is structural only
- LLM prompt engineering for variant generation — the variant_dimensions JSON field is a storage contract; prompt design is separate
- Spaced repetition scheduling logic — just the model (ReviewTask + ReviewHistory) stays as-is

## Decisions

### D1: Account.username → Account.phone

- **Choice**: Rename the column to `phone`, enforce UNIQUE, use as login credential for all roles
- **Rationale**: All three roles (teacher, student, parent) in Chinese secondary education identify by phone number. A separate username adds no value and creates confusion
- **Alternatives**: Keep username + add phone as optional — rejected because two login identifiers per user creates ambiguity

### D2: JWT sub_role separation

- **Choice**: `role` (Account.role: teacher/student/parent) + `sub_role` (Teacher.sub_role: system_admin/academic_admin/subject_lead/teacher | null)
- **Rationale**: identity ≠ permissions. Mixing them forces a DB lookup on every authenticated request (defeating JWT's purpose) or pollutes the identity field's semantics
- **Impact**: `create_access_token()` gains `sub_role` parameter; `create_refresh_token()` encodes both fields; `UserContext` gains `sub_role: str | None`

### D3: LoginRequest drops role field

- **Choice**: Login endpoint accepts only phone + password; system resolves role from Account table
- **Rationale**: The old `request.role != account.role` error gave different messages for "wrong role" vs "wrong password", creating a username enumeration oracle. Removing the field eliminates the vector
- **Alternatives**: Keep role but use uniform error messages — rejected because it still leaks via timing differences

### D4: Three separate registration flows

- **Choice**: Teacher → POST /api/auth/apply (creates Account+Teacher+TeacherApplication, pending status). Student → teacher batch-creates via POST /api/students. Parent → POST /api/auth/register/parent (requires bind_code)
- **Rationale**: Each role has fundamentally different registration prerequisites (school+approval, class assignment, bind code). A unified `/register` endpoint with optional fields creates a confusing API
- **Alternatives**: Single /register with role-specific nested objects — rejected as over-engineering for three flows

### D5: ExamPaper + ExamRecord two-layer model

- **Choice**: ExamPaper (template, status: draft→published→archived) → ExamRecord (instance, status: pending→in_progress→grading→completed→archived, +cancelled from any active state). New join table `exam_paper_question` with `score: float`
- **Rationale**: Separating "what to test" from "how it went" enables paper reuse across classes, versioning (v1→v2), and independent lifecycle management
- **Alternatives**: ExamRecord directly references Question list — rejected because it forces copy-paste for multi-class exams

### D6: Student.school_id redundancy

- **Choice**: Add `school_id` FK to Student (denormalized from Class→Grade→School chain)
- **Rationale**: Enables `UNIQUE(school_id, student_id)` constraint at the DB level and avoids 3-table JOIN for every data-isolation query. The denormalization chain is near-static (class transfers are rare)
- **Risk**: Class transfer requires updating both class_id and school_id — mitigated by a service-layer method that always updates both atomically

### D7: Async post-diagnosis hook

- **Choice**: After diagnosis saves to StudentAnswer, trigger async update of consecutive_wrong_count, consecutive_correct_count, and Student.barrier_profile
- **Rationale**: The compute is small (per-student aggregation), but blocking the diagnosis API response on it is unnecessary latency. Async ensures the API returns quickly while stats update in the background
- **Implementation**: FastAPI BackgroundTasks or a simple asyncio.create_task within the request lifecycle (MVP — no message queue)

### D8: Variant questions stored in Question table

- **Choice**: LLM-generated variant questions saved to Question table with `variant_of_question_id` FK + `variant_dimensions` JSON, `source=ai_generated`
- **Rationale**: Downstream systems (ReviewTask, diagnosis, analytics) require valid question_id FKs. Storing variants outside the Question table forces every consumer to handle nullable question_id
- **Cleanup**: Variants are first-class Question records; periodic cleanup by variant_of_question_id + age if table growth becomes an issue

### D9: Three-tier difficulty + competition

- **Choice**: `Difficulty` enum: easy, medium, hard, competition. Competition is excluded from ZPD automatic allocation
- **Rationale**: The original 5-tier system (easy-medium, medium-hard) created ambiguity between adjacent tiers. Three tiers are sufficient for adaptive selection; competition tier is manual-only
- **Impact**: CONTEXT.md difficulty table updated; historical questions may need Difficulty value migration

### D10: Five question types

- **Choice**: QuestionType enum: 选择题 (choice), 填空题 (fill_blank), 计算题 (calculation), 方程式配平 (equation_balancing), 实验探究 (experiment_inquiry)
- **Rationale**: Chinese chemistry exams map cleanly to these five categories. The original 8 CONTEXT.md types were too granular for question generation and audit
- **Migration**: Existing `question.question_type` strings must be mapped to new enum values

## Risks / Trade-offs

- **[Risk] TeacherApplication password_hash stored in application row** → If application is rejected and the teacher re-applies with the same phone, the second application's password_hash overwrites nothing (new Account row). Mitigation: Account is created once per phone; re-application reuses the same Account with a new TeacherApplication
- **[Risk] Student school_id denormalization drift** → If a class is moved to a different grade/school via raw SQL, Student.school_id goes stale. Mitigation: class transfer goes through a service method that updates both; add an Alembic data migration check
- **[Risk] Refresh token sub_role staleness** → If a teacher's sub-role changes (promotion from teacher to subject_lead), existing refresh tokens still carry the old sub_role. Mitigation: refresh tokens expire in 7 days; accept that role changes take up to 7 days to fully propagate
- **[Trade-off] ApprovalRequest vs ConversationCheckpoint JSON** → Standalone ApprovalRequest adds a table but enables querying pending approvals and auditing historical decisions. JSON blob approach would be simpler but unqueryable. Chose structured table for audit compliance

## Migration Plan

1. **Create Alembic migration**: Add new columns (phone rename, student_id, school_id FK, is_activated, misconception_category, diagnosed_by, etc.), new tables (exam_paper, exam_paper_question, practice_session, approval_request, knowledge_point_relation), and new enums
2. **Data migration**: Map existing `question.question_type` strings to new 5-type enum. Map existing `question.difficulty` values. Set `Account.phone` = `Account.username` for existing rows
3. **Deploy backend**: FastAPI restarts pick up new models and auth logic automatically
4. **Verify**: Run `pytest tests/` — all existing tests should pass; add new tests for auth and models
5. **Rollback**: Alembic downgrade reverts schema; old code reads `username` normally (column rename is reversible)

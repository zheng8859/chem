## Why

The `phase-2/data-model` branch needs to land the data model and authentication infrastructure that was designed but not yet implemented. The grilling session resolved 45 domain decisions that affect 7 existing model files, the auth service, JWT security, and RBAC permission matrix. Without these changes, the existing models are misaligned with the domain glossary and authentication contracts.

## What Changes

- **BREAKING**: Rename `Account.username` to `Account.phone` — login credential unified across all three roles
- **BREAKING**: Remove `LoginRequest.role` — system resolves role from DB, closing a user-enumeration vector
- **BREAKING**: Teacher registration no longer self-serve — goes through `TeacherApplication` with `password_hash` and `school_id` FK; Account + Teacher created on application submission (status=pending)
- **BREAKING**: Student registration decoupled — students are batch-created by teachers, then self-activate on first login
- **BREAKING**: Parent independent login endpoint removed — all roles use unified `/api/auth/login`
- Add `sub_role` to JWT payload and `UserContext` — separates identity role (Account.role) from permission role (Teacher.sub_role)
- Add `student_id` (学号), `school_id` FK, `is_activated` to Student model; remove `Student.phone`
- Remove `phone` from Teacher and Parent; single source of truth is `Account.phone`
- Add `ExamPaper` entity with draft/published/archived state machine; `ExamRecord` gains `exam_paper_id` FK and independent pending→completed state machine
- Add `exam_paper_question` join table with `score` field
- Add `misconception_category` enum, `diagnosed_by`, `diagnosis_overridden_at` to `StudentAnswer`
- Add `PracticeSession` entity for adaptive practice tracking
- Add `variant_of_question_id` and `variant_dimensions` JSON to `Question`
- Add `KnowledgePoint.parent_id` for hierarchical knowledge graph navigation
- Add `ApprovalRequest` entity for agent approval gate
- Consolidate question types to 5-enum: 选择题/填空题/计算题/方程式配平/实验探究
- Consolidate difficulty to 3-tier + competition: easy/medium/hard/competition
- Async post-diagnosis hook updates consecutive counts + barrier profile
- Refresh token carries `school_id` + `sub_role` to avoid data loss on token rotation
- Implement RBAC permission matrix via `require_permission` dependency
- Alembic migration for all schema changes

## Capabilities

### New Capabilities

- `data-model`: SQLAlchemy ORM models for all domain entities across 9 model files (org, user, teaching, diagnosis, question_bank, homework, ocr, agent_memory, exam_paper) matched to the domain glossary
- `auth-system`: Unified phone-based login, JWT with sub_role, refresh token rotation, TeacherApplication approval flow, student batch-creation + activation
- `rbac-permissions`: Role-based access control matrix (4 teacher sub-roles + student + parent) via `require_permission` FastAPI dependency
- `exam-lifecycle`: ExamPaper (template) + ExamRecord (instance) two-layer state machine with paper-question scoring
- `diagnosis-engine`: 3×6 orthogonal diagnosis matrix (barrier type × misconception category), async post-diagnosis hook, teacher override tracking
- `adaptive-practice`: PracticeSession persistence with variant question generation metadata

### Modified Capabilities

<!-- No existing specs to modify — this is the first spec-level change -->

## Impact

- **Models**: 7 existing files modified, 1 new file (`exam_paper.py`), 3 intermediate join tables
- **Auth**: `app/core/security.py`, `app/services/auth_service.py`, `app/schemas/auth.py`, `app/api/v1/auth.py`, `app/api/deps.py`
- **Enums**: `app/core/enums.py` — add MisconceptionCategory, ExamPaperStatus, ExamRecordStatus, QuestionType; remove EasyMedium/MediumHard difficulty values
- **Migration**: New Alembic revision for all schema changes
- **CONTEXT.md**: Updated to reflect renamed terms and consolidated vocabulary
- **Frontend**: Login pages must remove role selector; student activation page needed

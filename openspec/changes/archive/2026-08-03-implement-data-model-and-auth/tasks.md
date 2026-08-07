## 1. Core Enums

- [x] 1.1 Add MisconceptionCategory enum (6 values: chemical_equilibrium, redox, mole_calculation, organic_chemistry, chemical_notation, structure_of_matter)
- [x] 1.2 Add QuestionType enum (5 values: choice, fill_blank, calculation, equation_balancing, experiment_inquiry)
- [x] 1.3 Add ExamPaperStatus enum (draft, published, archived)
- [x] 1.4 Add ExamRecordStatus enum (pending, in_progress, grading, completed, archived, cancelled)
- [x] 1.5 Add PracticeSessionStatus enum (in_progress, completed, abandoned)
- [x] 1.6 Add ApprovalStatus enum (pending, approved, rejected, expired)
- [x] 1.7 Add DiagnosisSource enum (ai_rule, ai_llm, teacher)
- [x] 1.8 Consolidate Difficulty enum to 3 tiers + competition (easy, medium, hard, competition)
- [x] 1.9 Verify: `pytest tests/unit/test_enums.py -v` — all enums importable, values match spec

## 2. Account & Auth Models

- [x] 2.1 Rename Account.username to Account.phone (column rename in user.py, unique constraint kept)
- [x] 2.2 Remove phone from Teacher model, remove phone from Student model, remove phone from Parent model
- [x] 2.3 Add student_id (String, school-level unique) to Student model
- [x] 2.4 Add school_id FK (School) to Student model with UniqueConstraint(school_id, student_id)
- [x] 2.5 Add is_activated (Boolean, default False) to Student model
- [x] 2.6 Add password_hash to TeacherApplication model
- [x] 2.7 Add school_id FK (School) to TeacherApplication model
- [x] 2.8 Update TeacherApplication status to use ApplicationStatus enum consistently
- [x] 2.9 Delete Class.head_teacher_id — use TeacherClassSubject.is_head_teacher as single source of truth
- [x] 2.10 Verify: `pytest tests/unit/test_models_user.py -v` — Account.phone unique, Student.school_id+student_id unique, is_activated default, TeacherApplication.password_hash

## 3. Teaching & Diagnosis Models

- [x] 3.1 Add misconception_category (MisconceptionCategory enum, nullable) to StudentAnswer
- [x] 3.2 Add diagnosed_by (DiagnosisSource enum, nullable) to StudentAnswer
- [x] 3.3 Add diagnosis_overridden_at (DateTime, nullable) to StudentAnswer
- [x] 3.4 Change StudentAnswer.exam_record_id to nullable (for practice answers)
- [x] 3.5 Add variant_of_question_id FK (self-referential, nullable) to Question
- [x] 3.6 Add variant_dimensions (JSON, nullable) to Question
- [x] 3.7 Update Question.question_type to use QuestionType enum (replace string)
- [x] 3.8 Add parent_id FK (self-referential, nullable) to KnowledgePoint for hierarchical tree
- [x] 3.9 Verify: `pytest tests/unit/test_models_teaching.py -v` — StudentAnswer diagnosis fields writable, exam_record_id nullable, variant fields on Question, KnowledgePoint.parent_id

## 4. Exam Paper Model

- [x] 4.1 Create ExamPaper model (name, total_score, duration_minutes, status: ExamPaperStatus, teacher_id FK) in new file app/models/exam_paper.py
- [x] 4.2 Create ExamPaperQuestion join model (exam_paper_id FK, question_id FK, sort_order, score: Float)
- [x] 4.3 Add exam_paper_id FK (nullable) to ExamRecord
- [x] 4.4 Add status (ExamRecordStatus) to ExamRecord
- [x] 4.5 Add relationships on ExamRecord → ExamPaper, ExamPaper → questions
- [x] 4.6 Verify: `pytest tests/unit/test_models_exam_paper.py -v` — ExamPaper state machine (draft→published→archived), ExamRecord state machine (pending→in_progress→grading→completed, cancel from any active state)

## 5. Practice Session Model

- [x] 5.1 Create PracticeSession model (student_id FK, barrier_type FK, knowledge_point_tags JSON, questions_served, questions_correct, status) in teaching.py
- [x] 5.2 Verify: `pytest tests/unit/test_models_practice.py -v` — PracticeSession creation, status transitions (in_progress→completed/abandoned)

## 6. Approval Request Model

- [x] 6.1 Create ApprovalRequest model (thread_id, tool_name, tool_params JSON, status: ApprovalStatus, requested_by FK Teacher, approved_by FK Teacher nullable, approved_at nullable, expires_at) in agent_memory.py
- [x] 6.2 Verify: `pytest tests/unit/test_models_approval.py -v` — ApprovalRequest creation, status transitions (pending→approved/rejected/expired)

## 7. JWT Security Updates ⚠️ P0 BLOCKING

- [x] 7.1 Add sub_role parameter to create_access_token()
- [x] 7.2 Add sub_role and school_id to create_refresh_token()
- [x] 7.3 Update create_token_pair() to accept and pass sub_role
- [x] 7.4 Verify: `pytest tests/unit/test_jwt.py -v` — access token payload contains user_id, role, sub_role, school_id, type; refresh token payload contains same metadata

## 8. Auth Service Updates

- [x] 8.1 Rewrite login() to accept phone + password only (no role in request), resolve role from DB
- [x] 8.2 Resolve Teacher.sub_role during login and pass to create_token_pair
- [x] 8.3 Resolve Student school_id via Class→Grade→School chain during login
- [x] 8.4 Replace unified register() with apply() method — creates Account+Teacher(pending)+TeacherApplication atomically
- [x] 8.5 Add student_batch_create() — creates Account+Student(is_activated=False) with initial password
- [x] 8.6 Add student_activate() — on first login, set is_activated=True
- [x] 8.7 Add parent_register() — validates bind_code, creates Account(role=parent)+Parent+StudentParentBinding
- [x] 8.8 Update refresh_token() to decode sub_role and school_id from refresh token payload
- [x] 8.9 Verify: `pytest tests/unit/test_auth_service.py -v` — login returns tokens with sub_role; login rejects pending teacher; apply creates 3 records atomically; parent_register with valid/invalid bind_code; student_activate sets is_activated; refresh preserves sub_role+school_id

## 9. Auth Schemas Updates

- [x] 9.1 Update LoginRequest: remove role field, keep phone + password only
- [x] 9.2 Add TeacherApplyRequest: phone, password, name, school_id
- [x] 9.3 Add StudentBatchCreateRequest: list of {name, student_id, initial_password}
- [x] 9.4 Add ParentRegisterRequest: phone, password, bind_code
- [x] 9.5 Update TokenResponse: add sub_role (nullable), school_id (nullable)
- [x] 9.6 Remove ParentLoginRequest from schemas/homework.py (dead code after unified login)
- [x] 9.7 Verify: `pytest tests/unit/test_schemas_auth.py -v` — LoginRequest validates phone+password only; TokenResponse serializes sub_role+school_id

## 10. Auth API Updates

- [x] 10.1 Update POST /api/auth/login to match new LoginRequest schema
- [x] 10.2 Add POST /api/auth/apply (teacher application registration)
- [x] 10.3 Add POST /api/auth/register/parent (parent registration with bind_code)
- [x] 10.4 Add POST /api/students/batch (teacher batch-creates students)
- [x] 10.5 Keep POST /api/auth/refresh (updated internally)
- [x] 10.6 Verify: `pytest tests/integration/test_auth_api.py -v` — full login flow for teacher/student/parent; apply + approve flow; student batch create + activate flow; parent register + bind flow; refresh token cycle

## 11. Permission Middleware Updates ⚠️ P0 BLOCKING

- [x] 11.1 Add sub_role field to UserContext dataclass
- [x] 11.2 Update get_current_user() to extract sub_role from JWT payload
- [x] 11.3 Update check_permission() to use sub_role (fallback to role if null) for matrix lookup
- [x] 11.4 Lighten auth_middleware (main.py) — remove JWT decode; only check Authorization header presence; full decode stays in get_current_user
- [x] 11.5 Verify: `pytest tests/unit/test_deps.py -v` — UserContext carries sub_role; check_permission grants admin access with sub_role=system_admin; check_permission denies teacher access to school:delete; require_permission raises 403 for unauthorized; get_current_user returns 401 for missing/invalid token

## 12. Alembic Migration

- [x] 12.1 Generate single alembic revision with --autogenerate covering all structural changes
- [x] 12.2 Add data migration in same upgrade(): map existing question.question_type strings to new enum values
- [x] 12.3 Add data migration in same upgrade(): map existing question.difficulty strings
- [x] 12.4 Add data migration in same upgrade(): copy Account.username → Account.phone
- [x] 12.5 Verify: `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` — round-trip clean; data intact after downgrade

## 13. CONTEXT.md Update

- [x] 13.1 Update difficulty section: 5 tiers → 3 tiers + competition
- [x] 13.2 Update question types section: 8 types → 5 types (选择题/填空题/计算题/方程式配平/实验探究)
- [x] 13.3 Update Account terminology: username → phone
- [x] 13.4 Add ExamPaper and ExamRecord distinction to glossary
- [x] 13.5 Add PracticeSession to glossary
- [x] 13.6 Add ApprovalRequest to glossary
- [x] 13.7 Add diagnosed_by and diagnosis_overridden_at to diagnosis concepts
- [x] 13.8 Verify: manual review of CONTEXT.md — all 42 terms from proposal map to correct definitions

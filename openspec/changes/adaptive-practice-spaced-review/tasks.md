## 1. Database Layer — Models & Migration

- [ ] 1.1 Add `VariantQuestion` model to `app/models/diagnosis.py` (fields: id, original_question_id FK→Question, content, question_type, options, answer, analysis, knowledge_point_tags, difficulty, generated_at, expires_at)
- [ ] 1.2 Add `PracticeSessionQuestion` model to `app/models/teaching.py` (fields: id, practice_session_id FK→PracticeSession, question_id FK→Question, sort_order, unique constraint on session+question)
- [ ] 1.3 Extend `PracticeSession` model in `app/models/teaching.py`: add `practice_id` (String, unique), `title` (String), `question_count` (Integer), `deadline` (DateTime, nullable)
- [ ] 1.4 Add `barrier_type` (JSON, nullable) and `weak_knowledge_points` (JSON, nullable) columns to `Student` model in `app/models/user.py`
- [ ] 1.5 Change `ReviewTask.level` default from `1` to `0`, update comment to reflect 0-5 range
- [ ] 1.6 Update model `__init__.py` exports for new/changed models
- [ ] 1.7 Generate Alembic migration: `alembic revision --autogenerate -m "add variant_question, practice_session_question, extend practice_session and student, review_task level to 0"`
- [ ] 1.8 Run `alembic upgrade head` and verify tables exist in SQLite

## 2. Engine Layer — chemistry_memory/

- [ ] 2.1 Implement `zpd_engine.py`: `compute_zpd_difficulty(answers: list[bool]) -> str` — 30-window accuracy → easy/medium/hard mapping, cold start (<5 answers) → medium
- [ ] 2.2 Implement `zpd_engine.py`: `extract_weak_knowledge_points(wrong_answers: list[dict]) -> list[str]` — aggregate by knowledge_point tag, return top N
- [ ] 2.3 Implement `zpd_engine.py`: `identify_dominant_barrier(barrier_type: dict | None) -> str` — max score key extraction, default "concept"
- [ ] 2.4 Implement `strategy_matrix.py`: `apply_strategy(barrier: str, zpd_difficulty: str) -> dict` — difficulty offset, knowledge point preference, question type distribution per barrier
- [ ] 2.5 Implement `spaced_repetition.py`: `SPIRAL_REVIEW_DAYS = {0:0, 1:1, 2:3, 3:7, 4:14}` and `compute_next_review(level: int) -> timedelta`
- [ ] 2.6 Implement `spaced_repetition.py`: `evaluate_level_change(level: int, consecutive_correct: int, consecutive_wrong: int, is_correct: bool) -> dict` — upgrade/downgrade algorithm per design D6
- [ ] 2.7 Implement `variant_generator.py`: `build_variant_prompt(question: dict, count: int) -> str` — constructs LLM prompt for same-KP same-difficulty different-surface variants
- [ ] 2.8 Write unit tests for all engine functions (pytest, no DB needed)

## 3. Service Layer — app/services/

- [ ] 3.1 Create `app/services/adaptive_practice_service.py`: `AdaptivePracticeService` class with `__init__(db: AsyncSession, llm_service)`
- [ ] 3.2 Implement `AdaptivePracticeService.create_practice(student_id, kp_override, question_count)` — full 7-step pipeline: read student profile → ZPD calc → weak KPs → determine KPs → RAG search → LLM generate → parse questions → create PracticeSession + PracticeSessionQuestion records → create Question records (source=ai_generated)
- [ ] 3.3 Implement `AdaptivePracticeService.get_student_tasks(student_id) -> dict` — returns pending/completed practice tasks with metadata
- [ ] 3.4 Implement `AdaptivePracticeService.submit_practice(practice_id, answers) -> dict` — creates StudentAnswer records, triggers auto-sync, returns score/accuracy/per-question results
- [ ] 3.5 Implement `AdaptivePracticeService.get_practice_effect(student_id) -> dict` — compares last 2 sessions, returns improvement rate
- [ ] 3.6 Create `app/services/review_service.py`: `ReviewService` class, migrate `list_pending_reviews()` and `complete_review()` from `DiagnosisService` (update to use new spaced_repetition engine)
- [ ] 3.7 Implement `ReviewService.sync_review_tasks(student_id, wrong_question_ids)` — deduplication by (student_id, question_id), pull-back from completed to level 0
- [ ] 3.8 Implement `ReviewService.get_wrong_questions(student_id, limit, offset, kp_filter) -> dict` — aggregated from StudentAnswer JOIN Question, sorted by wrong_count DESC
- [ ] 3.9 Implement `ReviewService.generate_variants(question_id, count)` — check VariantQuestion cache → call LLM if insufficient → store in VariantQuestion table → return
- [ ] 3.10 Implement `ReviewService.create_training_session(student_id, question_ids) -> dict` — ephemeral session with session_id
- [ ] 3.11 Implement `ReviewService.submit_training(session_id, student_id, answers) -> dict` — score, accuracy, graded learning suggestion
- [ ] 3.12 Implement `ReviewService.mark_mastered(student_id, question_id)` — complete or create ReviewTask at level 5
- [ ] 3.13 Create `app/services/daily_practice_service.py`: `DailyPracticeService` class
- [ ] 3.14 Implement `DailyPracticeService.run_daily_scheduler()` — for each approved student: barrier-based KP selection → bank query with priority → LLM gap fill → create ExamRecord(type=daily_practice) per student
- [ ] 3.15 Implement `DailyPracticeService.notify_parents_of_overdue_reviews()` — check ReviewTask overdue counts → create ParentNotification for bound parents
- [ ] 3.16 Update `DiagnosisService`: remove `complete_review()` and `list_pending_reviews()`, add forwarding import from ReviewService if needed for backward compat
- [ ] 3.17 Write integration tests for all service methods (pytest + test DB)

## 4. API Layer — app/api/v1/

- [ ] 4.1 Create `app/api/v1/practice.py` router with prefix `/api/practice`
- [ ] 4.2 Implement `GET /api/practice/student/{uid}/tasks` — returns pending/completed tasks per spec
- [ ] 4.3 Implement `POST /api/practice/submit` — submit answers, trigger auto-sync, return results
- [ ] 4.4 Implement `GET /api/practice/effect/{student_id}` — practice improvement tracking
- [ ] 4.5 Create `app/api/v1/review.py` router with prefix `/api/review`
- [ ] 4.6 Implement `GET /api/review/student/{id}/due` — due/overdue ReviewTasks with question content
- [ ] 4.7 Implement `POST /api/review/submit` — submit review result, return updated level and next date
- [ ] 4.8 Implement `GET /api/review/wrong/list` — paginated wrong question list
- [ ] 4.9 Implement `POST /api/review/wrong/{question_id}/master` — mark question as mastered
- [ ] 4.10 Implement `POST /api/review/wrong-topic/variant/generate` — generate variants for a question
- [ ] 4.11 Implement `POST /api/review/wrong-topic/training/create` — create ephemeral training session
- [ ] 4.12 Implement `POST /api/review/wrong-topic/training/submit` — submit training results
- [ ] 4.13 Implement `GET /api/review/wrong-topic/knowledge-points` — list KPs with wrong questions
- [ ] 4.14 Remove old review endpoints from `app/api/v1/diagnosis.py` (`/api/v1/diagnosis/reviews/*`, `/api/v1/diagnosis/practice/assign`)
- [ ] 4.15 Register new routers in `app/main.py`
- [ ] 4.16 Write API integration tests for all endpoints (pytest + TestClient)

## 5. Daily Practice Scheduler

- [ ] 5.1 Configure APScheduler in `app/infrastructure/scheduler.py` (or create if absent)
- [ ] 5.2 Register `DailyPracticeService.run_daily_scheduler` as Cron job: `0 8 * * *` (08:00 UTC)
- [ ] 5.3 Ensure scheduler starts with FastAPI lifespan (`@app.on_event("startup")`)
- [ ] 5.4 Write scheduler integration test (mock time, verify ExamRecord created for all students)

## 6. Cleanup & Verification

- [ ] 6.1 Run full test suite: `pytest tests/ -v` — ensure all existing tests still pass
- [ ] 6.2 Run OpenSpec validate: `openspec validate --change adaptive-practice-spaced-review`
- [ ] 6.3 Verify API docs at `/docs` — all new endpoints visible with correct schemas
- [ ] 6.4 Manual smoke test: create practice → submit answers → verify ReviewTask auto-created → complete review → verify level change

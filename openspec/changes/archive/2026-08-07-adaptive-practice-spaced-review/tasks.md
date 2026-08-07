## 1. Database Layer — Models & Migration

- [x] 1.1 Add `VariantQuestion` model to `app/models/diagnosis.py`
- [x] 1.2 Add `PracticeSessionQuestion` model to `app/models/teaching.py`
- [x] 1.3 Extend `PracticeSession` model in `app/models/teaching.py`
- [x] 1.4 Add `weak_knowledge_points` column to `Student` model
- [x] 1.5 Change `ReviewTask.level` default from `1` to `0`, add `consecutive_correct`/`consecutive_wrong`
- [x] 1.6 Update model `__init__.py` exports
- [x] 1.7 Generate Alembic migration
- [x] 1.8 Run `alembic upgrade head` and verify tables exist

## 2. Engine Layer — chemistry_memory/

- [x] 2.1 Implement `zpd_engine.py`: `compute_zpd_difficulty(answers: list[bool]) -> str` — 30-window accuracy → easy/medium/hard mapping, cold start (<5 answers) → medium
- [x] 2.2 Implement `zpd_engine.py`: `extract_weak_knowledge_points(wrong_answers: list[dict]) -> list[str]` — aggregate by knowledge_point tag, return top N
- [x] 2.3 Implement `zpd_engine.py`: `identify_dominant_barrier(barrier_type: dict | None) -> str` — max score key extraction, default "concept"
- [x] 2.4 Implement `strategy_matrix.py`: `apply_strategy(barrier: str, zpd_difficulty: str) -> dict` — difficulty offset, knowledge point preference, question type distribution per barrier
- [x] 2.5 Implement `spaced_repetition.py`: `SPIRAL_REVIEW_DAYS = {0:0, 1:1, 2:3, 3:7, 4:14}` and `compute_next_review(level: int) -> timedelta`
- [x] 2.6 Implement `spaced_repetition.py`: `evaluate_level_change(level: int, consecutive_correct: int, consecutive_wrong: int, is_correct: bool) -> dict` — upgrade/downgrade algorithm per design D6
- [x] 2.7 Implement `variant_generator.py`: `build_variant_prompt(question: dict, count: int) -> str` — constructs LLM prompt for same-KP same-difficulty different-surface variants
- [x] 2.8 Write unit tests for all engine functions (pytest, no DB needed)

## 3. Service Layer — app/services/

- [x] 3.1 Create `app/services/adaptive_practice_service.py`: `AdaptivePracticeService` class with `__init__(db: AsyncSession, llm_service)`
- [x] 3.2 Implement `AdaptivePracticeService.create_practice(student_id, kp_override, question_count)` — full 7-step pipeline: read student profile → ZPD calc → weak KPs → determine KPs → RAG search → LLM generate → parse questions → create PracticeSession + PracticeSessionQuestion records → create Question records (source=ai_generated)
- [x] 3.3 Implement `AdaptivePracticeService.get_student_tasks(student_id) -> dict` — returns pending/completed practice tasks with metadata
- [x] 3.4 Implement `AdaptivePracticeService.submit_practice(practice_id, answers) -> dict` — creates StudentAnswer records, triggers auto-sync, returns score/accuracy/per-question results
- [x] 3.5 Implement `AdaptivePracticeService.get_practice_effect(student_id) -> dict` — compares last 2 sessions, returns improvement rate
- [x] 3.6 Create `app/services/review_service.py`: `ReviewService` class, migrate `list_pending_reviews()` and `complete_review()` from `DiagnosisService` (update to use new spaced_repetition engine)
- [x] 3.7 Implement `ReviewService.sync_review_tasks(student_id, wrong_question_ids)` — deduplication by (student_id, question_id), pull-back from completed to level 0
- [x] 3.8 Implement `ReviewService.get_wrong_questions(student_id, limit, offset, kp_filter) -> dict` — aggregated from StudentAnswer JOIN Question, sorted by wrong_count DESC
- [x] 3.9 Implement `ReviewService.generate_variants(question_id, count)` — check VariantQuestion cache → call LLM if insufficient → store in VariantQuestion table → return
- [x] 3.10 Implement `ReviewService.create_training_session(student_id, question_ids) -> dict` — ephemeral session with session_id
- [x] 3.11 Implement `ReviewService.submit_training(session_id, student_id, answers) -> dict` — score, accuracy, graded learning suggestion
- [x] 3.12 Implement `ReviewService.mark_mastered(student_id, question_id)` — complete or create ReviewTask at level 5
- [x] 3.13 Create `app/services/daily_practice_service.py`: `DailyPracticeService` class
- [x] 3.14 Implement `DailyPracticeService.run_daily_scheduler()` — for each approved student: barrier-based KP selection → bank query with priority → LLM gap fill → create ExamRecord(type=daily_practice) per student
- [x] 3.15 Implement `DailyPracticeService.notify_parents_of_overdue_reviews()` — check ReviewTask overdue counts → create ParentNotification for bound parents
- [x] 3.16 Update `DiagnosisService`: remove `complete_review()` and `list_pending_reviews()`, add forwarding import from ReviewService if needed for backward compat
- [x] 3.17 Write integration tests for all service methods (pytest + test DB)

## 4. API Layer — app/api/v1/

- [x] 4.1 Create `app/api/v1/practice.py` router with prefix `/api/practice`
- [x] 4.2 Implement `GET /api/practice/student/{uid}/tasks` — returns pending/completed tasks per spec
- [x] 4.3 Implement `POST /api/practice/submit` — submit answers, trigger auto-sync, return results
- [x] 4.4 Implement `GET /api/practice/effect/{student_id}` — practice improvement tracking
- [x] 4.5 Create `app/api/v1/review.py` router with prefix `/api/review`
- [x] 4.6 Implement `GET /api/review/student/{id}/due` — due/overdue ReviewTasks with question content
- [x] 4.7 Implement `POST /api/review/submit` — submit review result, return updated level and next date
- [x] 4.8 Implement `GET /api/review/wrong/list` — paginated wrong question list
- [x] 4.9 Implement `POST /api/review/wrong/{question_id}/master` — mark question as mastered
- [x] 4.10 Implement `POST /api/review/wrong-topic/variant/generate` — generate variants for a question
- [x] 4.11 Implement `POST /api/review/wrong-topic/training/create` — create ephemeral training session
- [x] 4.12 Implement `POST /api/review/wrong-topic/training/submit` — submit training results
- [x] 4.13 Implement `GET /api/review/wrong-topic/knowledge-points` — list KPs with wrong questions
- [x] 4.14 Remove old review endpoints from `app/api/v1/diagnosis.py` (`/api/v1/diagnosis/reviews/*`, `/api/v1/diagnosis/practice/assign`)
- [x] 4.15 Register new routers in `app/main.py`
- [x] 4.16 Write API integration tests for all endpoints (pytest + TestClient)

## 5. Daily Practice Scheduler

- [x] 5.1 Configure APScheduler in `app/infrastructure/scheduler.py` (or create if absent)
- [x] 5.2 Register `DailyPracticeService.run_daily_scheduler` as Cron job: `0 8 * * *` (08:00 UTC)
- [x] 5.3 Ensure scheduler starts with FastAPI lifespan (`@app.on_event("startup")`)
- [x] 5.4 Write scheduler integration test (mock time, verify ExamRecord created for all students)

## 6. Cleanup & Verification

- [x] 6.1 Run full test suite: `pytest tests/ -v` — ensure all existing tests still pass
- [x] 6.2 Run OpenSpec validate: `openspec validate --changes adaptive-practice-spaced-review`
- [x] 6.3 Verify API docs at `/docs` — all new endpoints visible with correct schemas
- [ ] 6.4 Manual smoke test: create practice → submit answers → verify ReviewTask auto-created → complete review → verify level change

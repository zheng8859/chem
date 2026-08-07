## Why

The "diagnose → practice → review" closed loop is the core value engine of ChemAI. While the diagnosis engine and exam workbench are built, the **adaptive practice** (ZPD-based personalized question assignment) and **spaced review** (Ebbinghaus-driven long-term memory consolidation) subsystems exist only as stubs (`assign_practice_stub` returns a UUID without creating real data). Teachers cannot actually assign differentiated practice, students receive no personalized review reminders, and wrong questions are not automatically synced into a review schedule. This change fills that gap, turning the diagnosis output into actionable practice and review.

## What Changes

- **NEW** `chemistry_memory/` engine layer: ZPD difficulty calculator (30-question sliding window, 3-tier mapping), adaptive strategy matrix (barrier → difficulty/question type mapping), Ebbinghaus spaced repetition upgrade/downgrade rules, and variant question generation logic
- **NEW** `app/services/` orchestration layer: `AdaptivePracticeService` (ZPD + LLM question generation + session management) and `ReviewService` (extracted from DiagnosisService + expanded with wrong question training + automatic sync)
- **NEW** REST API routers: `app/api/v1/practice.py` (task list, submit, effect tracking) and `app/api/v1/review.py` (due tasks, wrong question list, variant generation, training sessions, mastery marking)
- **NEW** `VariantQuestion` table for isolated variant storage, and `PracticeSessionQuestion` M2M join table
- **MODIFIED** `ReviewTask.level`: default changes from `1` to `0`, aligning with the 6-level Ebbinghaus model (0-5, where 0 = initial learning, 5 = mastered)
- **MODIFIED** `PracticeSession` model: added `practice_id`, `title`, `question_count`, `deadline` fields
- **NEW** APScheduler daily practice job: pushes 10-question daily exercises to every student at 08:00 UTC, with per-student barrier-type-based knowledge point selection
- **MOVED** `complete_review()` and `list_pending_reviews()` from `DiagnosisService` to `ReviewService`
- **BREAKING** variant questions are stored in a dedicated `VariantQuestion` table (with 90-day reuse window) instead of the `Question` main table, preventing pollution of exam analytics and difficulty calibration data
- **BREAKING** `ReviewTask.level` field semantics change (1-6 → 0-5); no production data affected

## Capabilities

### New Capabilities

- `zpd-difficulty-engine`: ZPD difficulty calculation using a 30-question sliding window, 3-tier mapping (easy/medium/hard), weak knowledge point extraction (Top N from all-time wrong answers), and dominant barrier type identification from Student.barrier_type JSON
- `spaced-review-engine`: Ebbinghaus 6-level spiral review (Level 0 through 5), upgrade/downgrade rules with consecutive correct/error counters, auto-sync from wrong answers with deduplication, overdue detection, and mastery marking
- `wrong-question-training`: Wrong question listing (sorted by error count), LLM-generated variant questions (3 at a time, same knowledge point + same difficulty + different surface form), isolated VariantQuestion storage, ephemeral training sessions, and learning suggestion grading
- `daily-practice-scheduler`: APScheduler Cron job at 08:00 UTC, barrier-type-based knowledge point selection per student, idempotent per-day deduplication, and parent notification for pending review tasks
- `practice-review-api`: REST endpoints for practice task list, practice submission with per-question results, practice effect tracking, due review task list, review submission with level change feedback, wrong question list with pagination, variant generation, training session create/submit, and mastery marking

### Modified Capabilities

- `adaptive-practice`: **BREAKING** — variant questions now stored in a dedicated `VariantQuestion` table (90-day reuse, cross-student sharing) instead of the `Question` table with `variant_of_question_id`. This isolates training data from exam analytics. PracticeSession gains `practice_id`, `title`, `question_count`, and `deadline` fields. PracticeSession-question relationship formalized via `PracticeSessionQuestion` M2M join table.
- `data-model`: **BREAKING** — `ReviewTask.level` default changes from `1` to `0`, level cap changes from `6` to `5`, aligning semantics with the 6-level Ebbinghaus model. New `VariantQuestion` table added. New `PracticeSessionQuestion` join table added. `PracticeSession` extended with structured fields. `Student` model gains `barrier_type` (JSON) and `weak_knowledge_points` (JSON) fields if not already present.

## Impact

- **Code**: `app/models/diagnosis.py` (ReviewTask, new VariantQuestion), `app/models/teaching.py` (PracticeSession extended, new PracticeSessionQuestion), `app/services/diagnosis_service.py` (review methods extracted), `app/services/` (2 new service files), `chem_skills/chemistry_memory/` (4 new engine files), `app/api/v1/` (2 new router files, diagnosis.py trimmed), `app/api/v1/teaching.py` (practice/submit updated), `app/core/enums.py` (unchanged, existing enums sufficient), `app/infrastructure/scheduler.py` (new or updated)
- **Database**: 3 new tables (`variant_question`, `practice_session_question`, migration for ReviewTask.level default), column additions to `practice_session` (practice_id, title, question_count, deadline), potential JSON columns on `student` (barrier_type, weak_knowledge_points)
- **LLM costs**: Each adaptive practice assignment calls LLM once per student (question generation + optional RAG). Each variant generation calls LLM once (3 variants). Daily practice scheduler uses LLM only to fill gaps (priority: existing bank → LLM supplement)
- **Dependencies**: `chemistry_memory/` engines are pure-function libraries with zero external dependencies; service layer depends on SQLAlchemy async session, LLM provider abstracted through existing `app/llm/` interface

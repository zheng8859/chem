## Context

The existing codebase has:
- `ReviewTask` + `ReviewHistory` models in `diagnosis.py`, with `complete_review()` and `list_pending_reviews()` in `DiagnosisService`
- `PracticeSession` model in `teaching.py` (minimal fields: barrier_type, knowledge_point_tags, questions_served, questions_correct, status)
- `StudentAnswer`, `Question`, `ExamRecord` models fully built
- `chemistry_memory/` directory exists but contains only an empty `__init__.py`
- `assign_practice_stub()` in DiagnosisService returns a UUID without real data
- No ZPD calculation, no variant generation, no auto-sync, no daily scheduler

See `proposal.md` for motivation (the why). This document covers architecture and approach (the how).

## Goals / Non-Goals

**Goals:**
- Pure-function engine layer in `chemistry_memory/` for ZPD, strategy matrix, spaced repetition rules, and variant generation — testable without DB or FastAPI
- Service orchestration layer in `app/services/` that wires engines to DB queries and LLM calls
- Separate REST routers for practice and review domains
- Isolated VariantQuestion storage to keep training data out of analytics
- ReviewTask level alignment to the 6-level Ebbinghaus model (0-5)
- Daily practice scheduler with bank-first question sourcing and barrier-type-based knowledge point selection

**Non-Goals:**
- Per-knowledge-point progress tracking (future iteration per design doc §7)
- ZPD difficulty level change trajectory visualization (future iteration)
- Customizable review intervals (fixed 6-level model)
- WebSocket support (practice/review are request-response)
- Student-facing frontend integration (API-only delivery per decision)

## Decisions

### D1: Engine-Service Layering

```
chem_skills/chemistry_memory/          app/services/
(pure functions, zero DB/HTTP deps)    (async, depends on DB session + llm)
─────────────────────────────────────  ─────────────────────────────────
zpd_engine.py       ZPD calc          adaptive_practice_service.py
strategy_matrix.py  Barrier→strategy  review_service.py
spaced_repetition.py Level rules      daily_practice_service.py
variant_generator.py Variant prompts
```

**Rationale**: Aligns with existing project structure where `chem_skills/` houses chemistry domain engines (exam generation, diagnosis, parsing). Pure functions in the engine layer can be unit-tested with simple input/output assertions. Service layer handles DB I/O, LLM calls, and transaction management.

**Alternative considered**: All-in `app/services/` — rejected because it would mix domain algorithms with infrastructure concerns, making the ZPD and spaced-repetition rules harder to test in isolation.

### D2: VariantQuestion Isolation

Variants are stored in a dedicated `VariantQuestion` table, NOT in the `Question` table. Key design:
- `original_question_id` FK to `Question.id`
- `expires_at = created_at + 90 days` for reuse window
- Queried by `original_question_id + expires_at > now()` for cross-student reuse
- Excluded from ALL analytics queries (no UNION, no JOIN with Question in stats)

**Rationale**: The user explicitly identified that mixing training variants with real exam questions would pollute error-rate statistics, difficulty calibration, and class performance reports. A separate table provides hard isolation at the storage layer. 90-day reuse balances LLM cost savings against content freshness.

**Alternative considered**: Flag column on Question (`is_variant=true`) — rejected because analytics queries can accidentally include variants, and the Question table already has `variant_of_question_id` for a different purpose (exam question variants that DO participate in analytics).

### D3: ReviewTask Level Alignment (0–5)

`ReviewTask.level` defaults to `0` (was `1`), with these semantics:
- Level 0: Initial learning, next_review = now (immediate availability)
- Level 1: 1st review, next_review = now + 1 day
- Level 2: 2nd review, next_review = now + 3 days
- Level 3: 3rd review, next_review = now + 7 days
- Level 4: 4th review, next_review = now + 14 days
- Level 5: Mastered, next_review = NULL, status = completed

SPIRAL_REVIEW_DAYS = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14}

**Rationale**: The Level 0 "趁热打铁" step is pedagogically critical — the steepest part of the Ebbinghaus curve. Zero production data means zero migration cost.

**Alternative considered**: Keep model at level 1-6, map internally — rejected because it creates a permanent mental translation layer between code and design docs.

### D4: Practice Data Routing

| Data type | Storage | Rationale |
|-----------|---------|-----------|
| Personalized adaptive practice | `PracticeSession` + `PracticeSessionQuestion` | One-to-one, per student |
| Daily practice | `ExamRecord(type=daily_practice)` | One-per-student but class-scoped, uses existing ExamRecord structure |
| Formal exams | `ExamRecord(type=monthly)` | Class-level, existing flow |
| Homework | `ExamRecord(type=homework)` | Class-level, existing flow |

**Rationale**: Adaptive practice is fundamentally per-student (different ZPD → different questions), so it belongs in the 1:1 PracticeSession model. Daily practice is class-scoped (same knowledge points for all students in a class, just different barrier-based topic selection), so it fits ExamRecord's class-level structure.

### D5: Auto-Sync Trigger Point

ReviewTask auto-sync from wrong answers triggers at `POST /api/practice/submit` (practice submission). The sync runs synchronously within the submission transaction for correctness, but the LLM diagnosis update (barrier_type recalculation) runs asynchronously per existing design.

**Rationale**: ReviewTask creation is a deterministic DB operation (check existence + insert), not an LLM call, so it can run synchronously without impacting response time. The LLM diagnosis stage is async per the existing architecture.

### D6: Upgrade/Downgrade Algorithm

```
complete_review(task_id, is_correct):
  1. Load task
  2. Record ReviewHistory(level=task.level, result=is_correct)
  3. If is_correct:
       task.consecutive_correct += 1
       task.consecutive_wrong = 0
       If task.consecutive_correct >= 2 AND task.level < 5:
         task.level += 1
         task.consecutive_correct = 0
     Else (wrong):
       task.consecutive_wrong += 1
       If task.consecutive_correct == 1:  // single correct then wrong → no downgrade
         task.consecutive_correct = 0
       Else if task.level > 0:
         task.level -= 1
         task.consecutive_wrong = 0
       task.consecutive_correct = 0
  4. task.next_review_date = now() + SPIRAL_REVIEW_DAYS[task.level]
  5. If task.level == 5: task.status = completed, task.next_review_date = NULL
```

### D7: API Router Split

| Router file | Prefix | Responsibilities |
|-------------|--------|-----------------|
| `app/api/v1/practice.py` | `/api/practice` | Task list, submit, effect tracking |
| `app/api/v1/review.py` | `/api/review` | Due tasks, submit, wrong list, master, variant, training |

Diagnosis-related review endpoints (`/api/v1/diagnosis/reviews/*`) are removed from `diagnosis.py` and migrated to `review.py`.

### D8: Daily Practice Question Sourcing

```
For each student at 08:00 UTC:
  1. Determine knowledge points from barrier_type
  2. SELECT * FROM Question WHERE knowledge_point_tags && target_kps
     AND difficulty='medium' AND audit_status='passed'
     ORDER BY RANDOM() LIMIT 10
  3. If count < 10:
       gap = 10 - count
       Call LLM to generate 'gap' questions
       Store generated questions in Question table (source=daily_practice)
  4. Create ExamRecord with question_stats JSON
```

## Risks / Trade-offs

- **[Risk] LLM generation failures during daily practice** → If LLM is unavailable, fall back to serving however many bank questions are available (even if fewer than 10). Log the shortfall for monitoring.
- **[Risk] VariantQuestion table growth** → 90-day reuse window limits growth. A periodic cleanup job can purge expired variants older than 180 days.
- **[Risk] complete_review() migration breaks DiagnosisService** → All callers (API + agent tools) are updated atomically in the same change. The old method is replaced with a forwarding call during the transition.
- **[Trade-off] VariantQuestions never participate in audit** → This means a poorly-generated variant could have factual errors. Mitigation: basic structural validation on LLM output (required fields present, answer is one of the options for choice questions) before storing.
- **[Trade-off] Daily practice uses same ExamRecord structure** → question_stats JSON carries metadata but actual Question assignment is deferred. If the student opens a daily practice from 3 days ago and the LLM hasn't generated the gap questions yet, they may see fewer than 10 questions. Acceptable for MVP.

## Migration Plan

1. **Alembic migration** creates: `variant_question` table, `practice_session_question` table, adds columns to `practice_session` (practice_id, title, question_count, deadline), adds columns to `student` (barrier_type JSON, weak_knowledge_points JSON), alters `review_task.level` default from 1 to 0
2. **No data migration needed** — zero production data
3. **Rollback**: downgrade migration removes new tables/columns, restores old defaults
4. **Code deployment order**: Models → Engines → Services → API routers → Scheduler → Remove old diagnosis review endpoints

## Open Questions

None. All design decisions were resolved during the grilling session.

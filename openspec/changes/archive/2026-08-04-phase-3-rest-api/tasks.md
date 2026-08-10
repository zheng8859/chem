## 1. Foundation

- [x] 1.1 Create `app/api/v1/__init__.py` — aggregate all 7 routers + auth into single `v1_router`
- [x] 1.2 Register `v1_router` in `app/main.py` under `/api/v1` prefix
- [x] 1.3 Add common pagination helper `get_pagination_params` as FastAPI dependency in `app/api/deps.py`
- [x] 1.4 Create `app/services/__init__.py` if missing

## 2. Org API (org-api)

- [x] 2.1 Create `app/services/org_service.py` — `create_school`, `get_school`, `list_schools`, `update_school`, `delete_school` with school_id isolation
- [x] 2.2 Create `app/services/org_service.py` — `create_grade`, `get_grade`, `list_grades_by_school`, `update_grade`, `delete_grade`
- [x] 2.3 Create `app/services/org_service.py` — `create_class`, `get_class`, `list_classes_by_grade`, `update_class`, `delete_class`
- [x] 2.4 Add `get_org_tree` service function returning nested school→grades→classes JSON
- [x] 2.5 Create `app/api/v1/org.py` — router with `/schools`, `/schools/{id}/grades`, `/grades/{id}/classes`, `/org/tree` endpoints, RBAC via `require_permission`
- [x] 2.6 Write integration tests for org endpoints (CRUD + tree + 403 for unauthorized)

## 3. User API (user-api)

- [x] 3.1 Create `app/services/user_service.py` — `list_accounts`, `get_teacher_applications`, `approve_teacher_application`, `reject_teacher_application`
- [x] 3.2 Create `app/services/user_service.py` — `create_student`, `get_student`, `list_students_by_class`, `update_student`, `delete_student`, `get_student_profile`
- [x] 3.3 Create `app/services/user_service.py` — `create_parent`, `get_parent`, `update_parent`, `list_parents`
- [x] 3.4 Create `app/services/user_service.py` — `create_assignment`, `list_teacher_assignments`, `delete_assignment`
- [x] 3.5 Add `verify_school_access` helper in `app/services/user_service.py` — validate that a class/grade belongs to user's school
- [x] 3.6 Create `app/api/v1/user.py` — router with `/accounts`, `/teacher-applications`, `/students`, `/students/me`, `/parents`, `/teacher-assignments` endpoints
- [ ] 3.7 Write integration tests for user endpoints (student CRUD, teacher approval flow, assignment lifecycle)

## 4. Question Bank API (question-bank-api)

- [x] 4.1 Create `app/services/question_bank_service.py` — `create_question_set`, `list_question_sets`, `update_question_set`, `delete_question_set`
- [x] 4.2 Create `app/services/question_bank_service.py` — `add_item`, `list_items`, `reorder_item`, `remove_item` (items embed full question data)
- [x] 4.3 Create `app/services/question_bank_service.py` — `list_historical_exams` with source/year/difficulty/knowledge_point filters
- [x] 4.4 Create `app/api/v1/question_bank.py` — router with `/question-sets`, `/question-sets/{id}/items`, `/historical-exams` endpoints
- [ ] 4.5 Write integration tests for question bank (folder CRUD, item add/remove/reorder, historical exam filters)

## 5. Teaching API (teaching-api)

- [x] 5.1 Create `app/services/teaching_service.py` — `create_exam`, `get_exam`, `list_exams_by_class`, `update_exam`, `delete_exam` with error_stats aggregation
- [x] 5.2 Create `app/services/teaching_service.py` — `create_question`, `get_question`, `list_questions` with filters, `update_question`, `delete_question`
- [x] 5.3 Create `app/services/teaching_service.py` — `generate_questions_stub` (returns `{"warning": "LLM pipeline not implemented", "questions": []}`)
- [x] 5.4 Create `app/services/teaching_service.py` — `submit_answer` (auto-grade against question.answer), `list_answers_by_exam`, `list_answers_by_student`
- [x] 5.5 Create `app/services/teaching_service.py` — `trigger_grading_stub` (returns grading_job_id with status "pending")
- [x] 5.6 Create `app/api/v1/teaching.py` — router with `/exams`, `/exams/{id}/answers`, `/questions`, `/questions/generate`, `/practice/submit`, `/grading/run`
- [ ] 5.7 Write integration tests for teaching endpoints (exam CRUD, question CRUD, answer submit with auto-grade)

## 6. Diagnosis API (diagnosis-api)

- [x] 6.1 Create `app/services/diagnosis_service.py` — `get_barrier_config`, `update_barrier_config` (auto-create default if missing)
- [x] 6.2 Create `app/services/diagnosis_service.py` — `list_knowledge_points` with category filter
- [x] 6.3 Create `app/services/diagnosis_service.py` — `get_class_diagnosis` (aggregate barrier distribution + per-student items)
- [x] 6.4 Create `app/services/diagnosis_service.py` — `list_pending_reviews`, `complete_review` (level up/down logic + ReviewHistory recording)
- [x] 6.5 Create `app/services/diagnosis_service.py` — `list_warnings` with class/resolved/severity filters, `resolve_warning`
- [x] 6.6 Create `app/services/diagnosis_service.py` — `assign_practice_stub` (returns practice_session_id with random question selection)
- [x] 6.7 Create `app/api/v1/diagnosis.py` — router with `/diagnosis/barrier-config`, `/knowledge-points`, `/diagnosis/class/{class_id}/exam/{exam_id}`, `/reviews/*`, `/warnings/*`, `/practice/assign`
- [ ] 6.8 Write integration tests for diagnosis endpoints (barrier config auto-create, review level progression, warning resolve)

## 7. Homework API (homework-api)

- [x] 7.1 Create `app/services/homework_service.py` — `create_binding` (validate bind_code), `list_bindings_by_parent`, `list_bindings_by_student`, `delete_binding`
- [x] 7.2 Create `app/services/homework_service.py` — `create_notification`, `list_notifications_by_parent`, `mark_notification_read`
- [x] 7.3 Create `app/services/homework_service.py` — `send_exam_reports` (create ParentNotification for each bound parent of exam participants)
- [x] 7.4 Create `app/api/v1/homework.py` — router with `/bindings`, `/notifications`, `/reports/send-to-students/{exam_id}`
- [ ] 7.5 Write integration tests for homework endpoints (valid/invalid bind_code, notification read, report dispatch)

## 8. OCR API (ocr-api)

- [x] 8.1 Create `app/services/ocr_service.py` — `create_upload_session`, `get_session`, `list_sessions_by_teacher` with task stats aggregation
- [x] 8.2 Create `app/services/ocr_service.py` — `list_tasks_by_session`, `get_task`
- [x] 8.3 Create `app/services/ocr_service.py` — `list_submissions_by_exam`, `get_submission`
- [x] 8.4 Create `app/services/ocr_service.py` — `batch_upload_stub` (creates session + placeholder OCR tasks)
- [x] 8.5 Create `app/api/v1/ocr.py` — router with `/ocr/sessions`, `/ocr/sessions/{id}/tasks`, `/ocr/tasks/{id}`, `/ocr/submissions`, `/ocr/tasks/batch`
- [ ] 8.6 Write integration tests for OCR endpoints (session lifecycle, task listing, batch upload stub)

## 9. Polish

- [x] 9.1 Run full test suite and fix any regressions
- [x] 9.2 Verify OpenAPI docs at `/docs` show all 8 route groups with correct schemas
- [x] 9.3 Run `openspec validate --change "phase-3-rest-api" --strict` and fix any issues

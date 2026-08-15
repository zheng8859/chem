# 任务 — 辅导、OCR 与记忆 Agent 工具组

## 1. 记忆工具修复与测试（Group C）

- [x] 1.1 写 `tests/unit/test_memory_tools.py`：覆盖 `memory_student_get` 读取诊断历史（最近 5 条）、读取学习计划、无数据返回空列表/None、以及 `memory_teacher_get` 无偏好记录时返回默认值（RED）
- [x] 1.2 修复 `agent/tools/memory_tools.py::memory_student_get` 的 import bug：改用 `store.read_diagnosis_history(db, student_id)` 与 `store.read_learning_plan_summary(db, student_id)`，通过 `MainSession()` 打开会话（GREEN）
- [x] 1.3 在 `app/agent/store.py` 新增 `read_teacher_preference(db, teacher_id)`：读 `LongTermMemory` 中 `teacher_id` 匹配且 `memory_type == teacher_preference` 的最新一条
- [x] 1.4 实现 `memory_teacher_get` 真实读取：调用 `read_teacher_preference`，无记录时返回默认值 `{"teaching_style": "balanced", "difficulty_preference": "auto", "class_configuration": {}}`（GREEN）
- [x] 1.5 消除命名碰撞：grep `app.agent.tools.memory_student_get` 调用点后，将辅助函数改名（如 `fetch_student_memory`）并更新引用

## 2. 通用辅导工具（Group A — 通用/实验/配平）

- [x] 2.1 写 `tests/unit/test_tutoring_tools.py`：覆盖 `chemistry_tutor` 教师/学生双模式、`simulate_experiment` 结构完整性、`balance_equation` 成功/引擎不可用/配平失败三态（RED）
- [x] 2.2 补 `simulate_experiment`：返回非空的 `steps`/`equations`/`safety_notes` 结构与 `_component`（experiment-card）标记（GREEN）
- [x] 2.3 固化 `balance_equation` 确定性：确认走确定性配平引擎、失败时返回 `verified=false` 且不抛未捕获异常

## 3. 专题辅导工具测试（Group A — 6 专题）

- [x] 3.1 写 `make_tutoring_tool` 工厂三态测试：entry（无输入引导）→ step（返回当前步骤引导）→ complete（所有步骤完成）流转
- [x] 3.2 写 6 专题工具结构测试：`ionic_equation_tutor`/`stoichiometry_tutor`/`redox_tutor`/`equilibrium_tutor`/`organic_tutor`/`periodic_law_tutor` 各自的 step_prompts 数量与 persona/call_limit 元数据

## 4. OCR 工具测试（Group B）

- [x] 4.1 写 `tests/integration/test_ocr_agent_tools.py`：覆盖 `query_ocr_progress` 批次查询/教师全量/全部完成态
- [x] 4.2 覆盖 `grade_answer_sheets`：批改已完成任务、答案来源优先级（教师录入 > 题库匹配）、空批次返回结构化错误不抛异常
- [x] 4.3 覆盖 `save_grading_results`：保存 + 触发诊断、审批门控、未注册学号跳过计入 `skipped_count`

## 5. 家长报告工具测试（Group D）

- [x] 5.1 写 `tests/integration/test_parent_report_tools.py`：覆盖 `generate_parent_report` 报告生成、学生无数据返回说明、内容过滤（报告不含具体错题内容）
- [x] 5.2 覆盖 `send_report_to_parent`：发送通知返回状态、需确认门控

## 6. 结构清理

- [x] 6.1 grep 确认无 `from app.chem_skills` import 后，删除 `app/chem_skills/` 空目录树
- [x] 6.2 全量跑 `pytest` 确认无回归

## 7. 验收

- [x] 7.1 16 个工具相关测试全部通过（`pytest -k "tutoring or memory or ocr or parent or tutor"`）
- [x] 7.2 跑 `run_evals --tier l1,l2` 确认全量 Evals 无劣化

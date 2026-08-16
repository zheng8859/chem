# ChemAI 验收清单（acceptance-checklist）

- **验收分支**：`phase-7/ship`
- **验收日期**：2026-08-16
- **验收人**：Claude Code（gstack `/qa-only` 全量 QA）
- **目标环境**：http://127.0.0.1:8000（SQLite 文件库 + FastAPI 8000 直接 serve 前端）
- **结论**：**不能发布** —— 存在 2 个 CRITICAL + 1 个 HIGH 未解决，三条用户旅程均被阻断

---

## 一、执行摘要

| 项 | 数值 |
|---|---|
| 健康分（加权） | **68 / 100** |
| 页面数 | 19 个静态 HTML（文档口径 14 页，见下「页面映射」） |
| 页面通过率 | **89.5%**（17 PASS + 1 WARN + 2 FAIL / 19）—— 目标 ≥90%，**未达标** |
| 未认证 401 门禁 | **16/16 受保护端点统一 401** ✅（全模块一致） |
| 问题总数 | 6（CRITICAL ×2、HIGH ×1、MEDIUM ×2、LOW ×1） |
| 三条用户旅程 | **0/3 走通**（教师/学生/家长全部被阻断） |

### 阻断性问题（必须先清零）

| ID | 严重度 | 问题 | 影响 |
|---|---|---|---|
| ISSUE-001 | CRITICAL | exam-v2.html 读 `access_token`（应为 `chemai_token`）→ 登录后 3×401 | 出题工作台完全不可用 |
| ISSUE-002 | CRITICAL | `teacher` 表 0 行 → `/panel/classes` 403「教师档案不存在」 | 教师仪表盘「加载失败」 |
| ISSUE-003 | HIGH | demo 数据未种子化（题库/试卷/预警全空） | 核心业务无数据可演示 |
| ISSUE-004 | MEDIUM | 登录页演示账号文案与实际不符（13800000000/demo123456 vs 13800000001/test123） | 按提示登录失败 |
| ISSUE-005 | MEDIUM | ocr-v2.html 潜伏 `access_token` bug | 上传交互时 401 |
| ISSUE-006 | LOW | 外部字体 404（cormorant garamond woff2） | 字体回退，不影响功能 |

---

## 二、14 页面 Checklist

> **架构偏差**：文档 60 期望 Vue3 SPA（路由 `/teacher/chat` 等 14 页），实际实现为 **19 个静态 HTML**（`/pages/<name>.html`）。14 页中 **12 页有对应实现，2 页缺失**（教师端「Agent 对话主页」、学生端「AI 对话页」—— 后端已有 `/chat` 与 `/parent/agent/chat` 端点，但无前端 chat 页面）。

### 教师端（文档口径 6 页）

| 文档页面 | 实际文件 | 加载 | 核心交互 | 判定 |
|---|---|---|---|---|
| Agent 对话主页 | ❌ **缺失**（无 chat.html） | — | — | **MISSING** |
| 出题工作台 | `pages/exam-v2.html` | 200 | ❌ 登录后 3×401（token key bug） | **FAIL** |
| 学情面板 | `pages/teacher.html` | 200 | ❌ 403「教师档案不存在」→加载失败 | **FAIL** |
| 学生管理 | `pages/students.html` | 200 | 空态（1 学生） | PASS |
| 障碍诊断 | `pages/diag.html` / `diagnosis.html` | 200 | — | PASS |
| OCR 批改 | `pages/ocr-v2.html`（`ocr.html` 为旧版） | 200 | ⚠️ 潜伏 token bug | WARN |

### 学生端（文档口径 6 页，均为移动端 `pages/m/*.html`）

| 文档页面 | 实际文件 | 加载 | 核心交互 | 判定 |
|---|---|---|---|---|
| 登录页 | `m/login.html` | 200 | 登录 API 200 ✅ | PASS |
| AI 对话页 | ❌ **缺失** | — | — | **MISSING** |
| 练习页 | `m/practice.html` | 200 | 空态（0 题目） | PASS |
| 错题本 | `m/wrong.html` | 200 | 空态 | PASS |
| 复习页 | `m/review.html` | 200 | 空态 | PASS |
| 个人报告页 | `m/report.html` | 200 | 空态 | PASS |

### 家长端（文档口径 2 页）

| 文档页面 | 实际文件 | 加载 | 核心交互 | 判定 |
|---|---|---|---|---|
| 登录页 | `m/parent-login.html` | 200 | — | PASS |
| 主面板（概览/学习报告/消息） | `m/parent.html` | 200 | — | PASS |

### 额外页面（文档口径之外）

| 文件 | 说明 | 判定 |
|---|---|---|
| `login.html` | 教师/学生桌面登录入口 | PASS |
| `index.html` | 桌面落地页 | PASS |
| `warnings.html` | 预警中心 | PASS（空态） |
| `m/index.html` | 移动端落地页 | PASS |
| `m/variant.html` | 变式题训练 | PASS |

---

## 三、全部 API 端点

> 扫描范围：`chemai-backend/app/api/v1/*.py`。基础前缀 `/api/v1`。
> **实测口径**：未认证 401 门禁已对 16 个代表性端点（覆盖全部模块）统一验证，全部一致返回 401。下表中「已实测」指本次 QA 明确打通的调用；其余端点标注「⬜ 待测」，其 401/422/404 分项未逐一执行。

### 认证与账号

| 方法 | 路径 | 状态 |
|---|---|---|
| POST | `/auth/login` | ✅ 已实测 200（教师/学生/家长） |
| POST | `/auth/apply` | ⬜ 待测 |
| POST | `/auth/register/parent` | ⬜ 待测 |
| POST | `/auth/refresh` | ⬜ 待测 |
| POST | `/auth/activate` | ⬜ 待测 |
| GET | `/accounts` | ✅ 未认证 401 |
| GET | `/teacher-applications` | ✅ 未认证 401 |
| POST | `/teacher-applications/{id}/approve` | ⬜ 待测 |
| POST | `/teacher-applications/{id}/reject` | ⬜ 待测 |
| POST | `/students` | ⬜ 待测 |
| GET | `/students/me` | ⬜ 待测 |
| GET | `/classes/{class_id}/students` | ⬜ 待测 |
| GET/PATCH/DELETE | `/students/{student_id}` | ⬜ 待测 |
| POST | `/parents` | ⬜ 待测 |
| GET | `/parents` | ⬜ 待测 |
| GET/PATCH | `/parents/{parent_id}` | ⬜ 待测 |
| POST/GET/DELETE | `/teacher-assignments` | ⬜ 待测 |

### 出题工作台 / 教学

| 方法 | 路径 | 状态 |
|---|---|---|
| POST/GET | `/exams` | ✅ 未认证 401（GET）；前端调用因 token bug 401 |
| GET/PATCH/DELETE | `/exams/{exam_id}` | ⬜ 待测 |
| GET | `/exams/{exam_id}/export` | ⬜ 待测 |
| POST/GET/DELETE | `/exams/{exam_id}/questions` | ⬜ 待测 |
| POST | `/exams/{exam_id}/publish` | ⬜ 待测 |
| POST | `/exams/{exam_id}/finalize` | ⬜ 待测 |
| POST | `/questions/import` | ⬜ 待测 |
| GET | `/exams/{exam_id}/answers` | ⬜ 待测 |
| POST/GET | `/questions` | ✅ 未认证 401（GET） |
| GET/PATCH/DELETE | `/questions/{question_id}` | ⬜ 待测 |
| POST | `/questions/generate` | ⬜ 待测 |
| POST | `/practice/answer` | ⬜ 待测 |
| POST | `/grading/run` | ⬜ 待测 |
| GET | `/students/{student_id}/answers` | ⬜ 待测 |
| POST | `/reports/send-to-students/{exam_id}` | ⬜ 待测 |

### 题库管理

| 方法 | 路径 | 状态 |
|---|---|---|
| POST/GET | `/question-sets` | ✅ 未认证 401（GET）；前端调用因 token bug 401 |
| PATCH/DELETE | `/question-sets/{set_id}` | ⬜ 待测 |
| POST/GET | `/question-sets/{set_id}/items` | ⬜ 待测 |
| PATCH | `/question-sets/items/{item_id}/reorder` | ⬜ 待测 |
| DELETE | `/question-sets/items/{item_id}` | ⬜ 待测 |
| GET | `/historical-exams` | ✅ 前端调用因 token bug 401 |

### 四维审核引擎

| 方法 | 路径 | 状态 |
|---|---|---|
| POST | `/audit/equation` | ⬜ 待测 |
| POST | `/audit/extract` | ⬜ 待测 |

### 学情面板

| 方法 | 路径 | 状态 |
|---|---|---|
| GET | `/panel/classes` | ❌ 已实测 403「教师档案不存在」 |
| GET | `/panel/class/{class_id}` | ⬜ 待测 |
| GET | `/panel/class/{class_id}/student/{student_id}` | ⬜ 待测 |
| GET | `/panel/class/{class_id}/knowledge-points` | ⬜ 待测 |
| GET | `/panel/class/{class_id}/barriers` | ⬜ 待测 |
| GET | `/panel/class/{class_id}/concern-students` | ⬜ 待测 |
| GET | `/panel/class/{class_id}/exam-trend` | ⬜ 待测 |

### 障碍诊断

| 方法 | 路径 | 状态 |
|---|---|---|
| GET/PATCH | `/diagnosis/barrier-config` | ⬜ 待测 |
| GET | `/knowledge-points/search` | ⬜ 待测 |
| GET | `/knowledge-points` | ⬜ 待测 |
| GET | `/diagnosis/class/{class_id}/exam/{exam_id}` | ⬜ 待测 |
| POST | `/diagnosis/run-llm/{exam_id}` | ⬜ 待测 |
| PUT | `/diagnosis/override/{student_answer_id}` | ⬜ 待测 |
| GET | `/warnings` | ⬜ 待测 |
| POST | `/warnings/{warning_id}/resolve` | ⬜ 待测 |

### 预警中心

| 方法 | 路径 | 状态 |
|---|---|---|
| GET | `/warning/list` | ✅ 未认证 401 |
| GET | `/warning/stats` | ⬜ 待测 |
| GET | `/warning/{warning_id}` | ⬜ 待测 |
| PATCH | `/warning/{warning_id}/status` | ⬜ 待测 |
| POST | `/warning/check` | ⬜ 待测 |

### 自适应练习 / 错题本 / 复习

| 方法 | 路径 | 状态 |
|---|---|---|
| GET | `/practice/student/{uid}/tasks` | ⬜ 待测 |
| POST | `/practice/submit` | ⬜ 待测 |
| GET | `/practice/effect/{student_id}` | ⬜ 待测 |
| POST | `/practice/assign` | ⬜ 待测 |
| GET | `/practice/wrong/list` | ✅ 未认证 401 |
| POST | `/practice/wrong/{question_id}/master` | ⬜ 待测 |
| POST | `/practice/wrong-topic/variant/generate` | ⬜ 待测 |
| POST | `/practice/wrong-topic/training/create` | ⬜ 待测 |
| POST | `/practice/wrong-topic/training/submit` | ⬜ 待测 |
| GET | `/practice/wrong-topic/knowledge-points` | ⬜ 待测 |
| GET | `/review/student/{id}/due` | ✅ 未认证 401 |
| POST | `/review/submit` | ⬜ 待测 |
| GET | `/student/{student_id}/stats` | ✅ 未认证 401 |
| GET | `/notifications/student/{student_id}` | ⬜ 待测 |
| POST | `/notifications/{id}/student-read` | ⬜ 待测 |

### 学习计划

| 方法 | 路径 | 状态 |
|---|---|---|
| POST | `/learning-plan` | ⬜ 待测 |
| PUT | `/learning-plan/{plan_id}` | ⬜ 待测 |
| GET | `/learning-plan/{student_id}` | ✅ 未认证 401 |
| PATCH | `/learning-plan/tasks/{task_id}/complete` | ⬜ 待测 |

### 家长端

| 方法 | 路径 | 状态 |
|---|---|---|
| POST | `/parent/bind-code/{student_id}` | ⬜ 待测 |
| POST | `/parent/bind` | ⬜ 待测 |
| GET | `/parent/children` | ✅ 未认证 401 |
| DELETE | `/parent/bind/{binding_id}` | ⬜ 待测 |
| GET | `/parent/child/{student_id}/report` | ⬜ 待测 |
| GET | `/parent/child/{student_id}/timeline` | ⬜ 待测 |
| GET | `/parent/child/{student_id}/weekly` | ⬜ 待测 |
| POST | `/parent/child/{student_id}/weekly/generate` | ⬜ 待测 |
| GET | `/parent/notifications` | ⬜ 待测 |
| PUT | `/parent/notifications/{id}/read` | ⬜ 待测 |

### Agent 对话

| 方法 | 路径 | 状态 |
|---|---|---|
| POST | `/chat/stream` | ⬜ 待测（无前端入口） |
| GET | `/chat/conversations` | ✅ 未认证 401 |
| GET | `/chat/history/{thread_id}` | ⬜ 待测 |
| POST | `/chat/new` | ⬜ 待测 |
| DELETE | `/chat/conversations/{thread_id}` | ⬜ 待测 |
| POST | `/chat/resume` | ⬜ 待测 |
| POST | `/chat/reset` | ⬜ 待测 |
| POST | `/parent/agent/chat` | ⬜ 待测 |
| GET | `/parent/agent/conversations` | ⬜ 待测 |
| GET | `/parent/agent/history/{thread_id}` | ⬜ 待测 |
| POST | `/parent/agent/new` | ⬜ 待测 |
| DELETE | `/parent/agent/conversations/{thread_id}` | ⬜ 待测 |

### OCR 批改

| 方法 | 路径 | 状态 |
|---|---|---|
| GET | `/ocr/sessions` | ✅ 未认证 401 |
| GET | `/ocr/sessions/{session_id}` | ⬜ 待测 |
| GET | `/ocr/sessions/{session_id}/tasks` | ⬜ 待测 |
| GET | `/ocr/tasks/{task_id}` | ⬜ 待测 |
| GET | `/ocr/submissions` | ⬜ 待测 |
| GET | `/ocr/submissions/{submission_id}` | ⬜ 待测 |
| POST | `/ocr/tasks/batch` | ⬜ 待测 |
| POST | `/ocr/tasks/{task_id}/retry` | ⬜ 待测 |
| GET | `/ocr/services/status` | ⬜ 待测 |
| POST | `/ocr/grading/run` | ⬜ 待测 |
| GET | `/ocr/grading/results/{batch_id}` | ⬜ 待测 |
| POST | `/ocr/grading/save` | ⬜ 待测 |
| POST | `/ocr/stats` | ⬜ 待测 |

### 组织架构

| 方法 | 路径 | 状态 |
|---|---|---|
| GET/POST | `/schools` | ⬜ 待测 |
| GET/PATCH/DELETE | `/schools/{school_id}` | ⬜ 待测 |
| GET | `/schools/{school_id}/grades` | ⬜ 待测 |
| POST | `/grades` | ⬜ 待测 |
| GET/PATCH/DELETE | `/grades/{grade_id}` | ⬜ 待测 |
| GET | `/grades/{grade_id}/classes` | ⬜ 待测 |
| POST | `/classes` | ⬜ 待测 |
| GET/PATCH/DELETE | `/classes/{class_id}` | ⬜ 待测 |
| GET | `/org/tree` | ✅ 未认证 401 |

### 系统

| 方法 | 路径 | 状态 |
|---|---|---|
| GET | `/health` | ✅ 已实测 200（无需认证） |
| GET | `/`（前端静态） | ✅ 已实测 200 |

**端点合计**：约 150 个（含方法维度）。**未认证 401 门禁**：抽测 16 端点全通过；**完整 401/422/404 矩阵**：未逐一执行，需脚本化补测。

---

## 四、三条用户旅程

### 旅程 1 · 教师：登录 → 出题 → 四维审核 → 发布考试 → 查看学情 → 障碍诊断

| 步骤 | 结果 | 阻断点 |
|---|---|---|
| 登录（13800000001/test123） | ✅ PASS | — |
| 出题工作台 | ❌ FAIL | ISSUE-001：exam-v2 登录后 3×401 |
| 四维审核 | ❌ FAIL | 依赖出题/题目数据，且 ISSUE-003 无题目 |
| 发布考试 | ❌ FAIL | ISSUE-003：`exam_paper=0` 无试卷 |
| 查看学情 | ❌ FAIL | ISSUE-002：403「教师档案不存在」 |
| 障碍诊断 | ❌ FAIL | 依赖考试数据（ISSUE-003） |

**结论：阻断**（第 2 步即失败）

### 旅程 2 · 学生：登录 → AI 对话 → 做练习 → 错题本 → 间隔复习 → 个人报告

| 步骤 | 结果 | 阻断点 |
|---|---|---|
| 登录（13800000002/test123） | ✅ PASS | — |
| AI 对话 | ❌ FAIL | 无前端 chat 页（仅后端 `/chat` 端点） |
| 做练习 | ❌ FAIL | ISSUE-003：`question=0` 无题目 |
| 错题本 | ⚠️ 空态 | 无练习记录 |
| 间隔复习 | ⚠️ 空态 | 无复习数据 |
| 个人报告 | ⚠️ 空态 | 无学习数据 |

**结论：阻断**（AI 对话页缺失 + 无题目数据）

### 旅程 3 · 家长：登录 → 查看概览 → 学习报告 → 消息通知

| 步骤 | 结果 | 阻断点 |
|---|---|---|
| 登录（家长账号） | ✅ PASS | — |
| 查看概览 | ⚠️ 空态 | 3 个家长账号存在，但无子女学习数据 |
| 学习报告 | ⚠️ 空态 | 无报告数据 |
| 消息通知 | ⚠️ 空态 | 无消息 |

**结论：阻断**（缺学习数据，无法展示有效报告）

---

## 五、发布建议

**不能发布** —— 需先清零 2 个 CRITICAL（ISSUE-001 token key、ISSUE-002 教师档案）+ 1 个 HIGH（ISSUE-003 demo 数据种子化），并补齐 2 个缺失的 AI 对话前端页，方可进入 `v1.0.0-rc.1` 打标流程。

### 最小修复清单（按优先级）

1. **ISSUE-001**：`exam-v2.html`（+ `ocr-v2.html`）`access_token` → `chemai_token`。
2. **ISSUE-002 + ISSUE-003**：补全 `seed_test_data.py` / `app/seed.py` 种子链 —— 建 Teacher 档案、题库、试卷、预警、学习数据。
3. **补 2 个 chat 前端页**：教师端 Agent 对话主页 + 学生端 AI 对话页（后端端点已就绪）。
4. **ISSUE-004**：登录页演示账号文案改为 13800000001/test123。
5. **ISSUE-006**：修复 Google Fonts 字体 URL 或改为本地字体。

---

*报告来源：`.gstack/qa-reports/qa-report-localhost-2026-08-16.md` + `.gstack/qa-reports/baseline.json`*

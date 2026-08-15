# 辅导、OCR 与记忆 Agent 工具组

## Why

文档58 定义的 16 个 Agent 工具（辅导 9 + OCR 3 + 记忆 2 + 家长报告 2）代码已基本落地——14 个已实现并接入真实服务（GradingService / ParentService / app.agent.store），但**行为验证为零**：除注册完整性测试外，没有任何针对这些工具的行为测试。文档58 的完成标准（「16 个工具全部 pytest 通过」「OCR 管道状态机封装为对话式操作」「家长报告内容过滤已验证」「记忆跨会话持久化已验证」）一项都未达标。

此外，OCR 3 工具、家长报告 2 工具、通用辅导 3 工具（`chemistry_tutor` / `simulate_experiment` / `balance_equation`）在现有 spec 中只以「工具名单」形式出现（`agent-tools` 的 tool-set 场景），**没有行为契约**——而这正是文档58 要求验证的部分。

## What Changes

- **补行为测试（核心交付）**：为 16 个工具编写行为测试（L1 单元 + L2 集成），覆盖文档24 §11 的 OCR 边界用例、文档29 §安全与权限 的家长内容过滤、文档30 §3.4 的辅导三态流转与配平确定性。
- **补全 2 个占位实现**：
  - `simulate_experiment`（实验模拟）当前返回空壳（`steps=[]`、`equations=[]`），需返回有意义结构。
  - `memory_teacher_get`（教师记忆）当前硬编码 `"balanced"` / `"auto"`，需读取真实教师偏好存储。
- **新增 3 组行为契约 spec**：为 OCR 工具、家长报告工具、通用辅导工具补上行为需求（见 Capabilities）。
- **清理结构噪声**：
  - 删除 `app/chem_skills/` 空目录树（真实引擎在顶层 `chem_skills/`）。
  - 消解 `memory_student_get` 同名两份实现（`agent/tools/memory_tools.py` 注册版 vs `app/agent/tools/memory_student_get.py` 引擎辅助版），统一读路径。

## Capabilities

### New Capabilities
- `agent-ocr-tools`: OCR 批改工具组（`query_ocr_progress` / `grade_answer_sheets` / `save_grading_results`）的三阶段对话式封装行为——进度查询、批量批改、确认保存并触发障碍诊断，来源文档24 §8。
- `agent-parent-report-tools`: 家长报告工具组（`generate_parent_report` / `send_report_to_parent`）的生成、发送与内容过滤行为——家长不可见子女具体错题内容，来源文档30 §3.7 + 文档29 §安全与权限。
- `agent-general-tutoring-tools`: 通用辅导工具组（`chemistry_tutor` / `simulate_experiment` / `balance_equation`）的行为契约——教师/学生双模式讲解、实验模拟结构、方程式确定性配平，来源文档30 §3.4。

### Modified Capabilities
（无。6 专题辅导已在 `agent-chem-tutors`、记忆已在 `agent-student-memory` 中声明，本次仅补测试与实现，需求不变。）

## Impact

- **测试**：新增 `tests/unit/test_tutoring_tools.py`、`tests/unit/test_memory_tools.py`、`tests/unit/test_parent_tools.py`、`tests/unit/test_ocr_tools.py`（或合并为 `test_agent_remaining_tools.py`），以及必要的 `tests/integration/` 用例。
- **代码**：修改 `agent/tools/tutoring_tools.py`（补 `simulate_experiment`）、`agent/tools/memory_tools.py`（补 `memory_teacher_get`）。
- **清理**：删除 `app/chem_skills/`（先 grep 确认无 import）；统一 `memory_student_get` 读路径。
- **不涉及**：REST API 变更、数据库 schema 变更、前端变更、Provider 变更。

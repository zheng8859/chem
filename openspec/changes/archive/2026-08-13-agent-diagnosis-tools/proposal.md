## Why

诊断与学生 Agent 工具组（30号文档 §3.3 的 7 个工具）已在 `agent/tools/diagnosis_tools.py` 落地，但缺少对标 `agent-exam-tools` 的专属规格，且工具签名与设计文档存在多处分歧：`diagnose_barrier` 无姓名解析/班级级、`assign_adaptive_practice` 做成单人而非班级级、`weekly_report` 返回结构化数据而非自然语言周报、`generate_learning_plan` 直接写库而非预览。本变更补齐这些缺口，让「诊断 → 出题 → 练习 → 反馈」闭环在 Agent 对话里真正可用。

## What Changes

- **新增专属规格 `agent-diagnosis-tools`**：固化 7 个诊断与学生工具的行为契约（签名、Persona、call_limit、审批门控、前置条件、`_component`/`_route` 路由）。
- **`diagnose_barrier` 增强**：支持纯数字 ID 与中文姓名两种输入（模糊匹配，多结果返回候选列表），并支持个体/班级两级诊断。
- **`assign_adaptive_practice` 改为班级级为主**：接受 `class_id` 为班级学生批量生成 ZPD 练习（内部按 5 人/批），`student_id` 保留为单生快捷路径兜底。
- **`show_students` 增加障碍过滤**：新增按障碍类型（concept/reading/expression）筛选参数。
- **`generate_learning_plan` 改为预览/路由**：返回 `_route` 跳转指令触发前端抽屉生成，不再直接调用 `create_plan` 写库。
- **`weekly_report` 改为 LLM 生成**：工具内调用 LLM 生成 200 字自然语言周报（通俗语言、不制造焦虑），而非返回原始结构化面板数据。
- **工具元数据对齐设计 30 §3.3**：persona、call_limit、requires_approval、prerequisites 逐项对齐（含收紧 `diagnose_barrier`、`weekly_report` 等的 call_limit）。

## Capabilities

### New Capabilities

- `agent-diagnosis-tools`: 7 个诊断与学生 Agent 工具（diagnose_barrier、show_diagnosis、show_students、weekly_report、assign_adaptive_practice、generate_learning_plan、send_learning_plan）的行为契约与工具元数据。

### Modified Capabilities

（无。诊断 3×6 矩阵、no-confidence 决策、ZPD 引擎已在既有 `diagnosis-engine`、`llm-diagnoser`、`zpd-difficulty-engine` 规格中覆盖，本次不产生 delta。）

## Impact

- **代码**：`agent/tools/diagnosis_tools.py`（主要）；可能新增/复用服务层小方法（名称解析、班级级批处理编排）；`agent/prompts/` Persona YAML 白名单可能同步。
- **规格**：新增 `openspec/specs/agent-diagnosis-tools/spec.md`。
- **测试**：新增/更新 `tests/` 中工具签名与行为的单元、集成测试；现有调用旧签名的测试需同步更新。
- **前端**：`generate_learning_plan` 与 `show_diagnosis`/`show_students` 的 `_route`/`_component` 路由需前端面板支持（若尚未支持则标记为前端待办，不阻断本变更）。

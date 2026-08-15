## 1. 测试先行（RED）

- [x] 1.1 写 `resolve_student_by_identity` 单元测试：纯数字 ID、姓名精确命中、子串命中、多结果返回候选（对应 spec「diagnose_barrier 两级诊断与名称解析」）
- [x] 1.2 写 `diagnose_barrier` 两级诊断测试：数字 ID 个体、姓名唯一命中、姓名多结果候选、class_id 班级级（对应 spec 同名 requirement）
- [x] 1.3 写 `assign_adaptive_practice` 班级级批处理测试：class_id 按 5 人/批、student_id 单生兜底、审批门控拦截（对应 spec「班级级自适应练习」）
- [x] 1.4 写 `weekly_report` LLM 周报测试：生成自然语言周报、无数据时说明、LLM 失败降级结构化数据（对应 spec「LLM 自然语言周报」）
- [x] 1.5 写 `generate_learning_plan` 预览路由测试：返回 `_route`、不产生学习计划记录（对应 spec「预览路由」）
- [x] 1.6 写 `show_students` 障碍过滤透传测试：`barrier` 参数进入 `_component` params（对应 spec「学生列表与障碍过滤」）

## 2. 工具实现（GREEN）

- [x] 2.1 实现 `DiagnosisService.resolve_student_by_identity(db, identity)`：数字→ID 精确查，非数字→姓名精确→子串匹配，多结果排序返回（design D1）
- [x] 2.2 改造 `diagnose_barrier`：新增 `class_id`/`student_name` 参数，名称解析走 2.1，class_id 走 `PanelService.get_barriers`（design D2，无需 exam_id）
- [x] 2.3 改造 `assign_adaptive_practice`：新增 `class_id`，班级学生按每批 5 名顺序调 `create_practice`，返回每生摘要（design D3）
- [x] 2.4 改造 `weekly_report`：取面板数据后调 `llm_chat` 生成 ≤200 字周报，失败降级结构化数据（design D5）
- [x] 2.5 改造 `generate_learning_plan`：移除 `create_plan` 调用，改为返回 `_route`（design D4）
- [x] 2.6 改造 `show_students`：新增 `barrier` 参数透传至 `_component`（design D6）

## 3. 工具元数据对齐

- [x] 3.1 更新 7 个工具的 `@register_tool` 元数据：call_limit 对齐设计 30 §3.3，`assign_adaptive_practice`/`send_learning_plan` 保持 requires_approval（design D7）
- [x] 3.2 检查并同步 Persona YAML 白名单（`agent/prompts/`）与 `diagnose_barrier`/`weekly_report` 的 parent 角色（已正确，无需改动）

## 4. 验证（REFACTOR）

- [x] 4.1 运行新增测试全部通过（`pytest tests/unit -k "diagnosis_tools or resolve_student" -v`）
- [x] 4.2 修复因 call_limit 收紧与签名变更受影响的既有测试（无既有测试断言旧 call_limit/签名，无需修复）
- [x] 4.3 全量测试通过（`pytest tests/ -v`，1593 passed / 51 skipped），覆盖率不劣化
- [x] 4.4 `openspec validate --change agent-diagnosis-tools --strict` 通过

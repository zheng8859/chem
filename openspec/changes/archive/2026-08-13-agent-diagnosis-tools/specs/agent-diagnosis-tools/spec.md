## Purpose

定义诊断与学生 Agent 工具组（30号文档 §3.3 的 7 个工具）的行为契约：障碍诊断（个体/班级两级 + 名称解析）、诊断与学生面板路由、LLM 自然语言周报、班级级自适应练习布置、学习计划的预览与发送，以及这 7 个工具的 Persona 与调用次数元数据。

## ADDED Requirements

### Requirement: diagnose_barrier 两级诊断与名称解析

系统 SHALL 提供 `diagnose_barrier` 工具，接受纯数字 student_id 或中文姓名两种输入。非数字输入时执行模糊匹配，唯一命中直接诊断，多结果返回候选列表；支持个体诊断（返回三维障碍分布与主导类型）与班级诊断（返回全班统计分布）两级。

#### Scenario: 数字 ID 个体诊断
- **WHEN** 教师以纯数字 student_id 调用 diagnose_barrier
- **THEN** 返回该学生的三维障碍分布（concept/reading/expression 占比）、主导障碍类型、薄弱知识点与更新时间

#### Scenario: 中文姓名唯一命中
- **WHEN** 教师以中文姓名调用，且姓名在全班唯一匹配到一名学生
- **THEN** 直接返回该学生的障碍画像，不要求二次确认

#### Scenario: 中文姓名多结果返回候选
- **WHEN** 教师以中文姓名调用，且该姓名匹配到多名学生（如重名）
- **THEN** 返回候选学生列表（含 student_id 与姓名/班级），等待教师指定具体学生

#### Scenario: 班级级诊断
- **WHEN** 教师以 class_id 调用 diagnose_barrier
- **THEN** 返回全班障碍统计分布（各障碍类型为主导的学生人数与占比）

### Requirement: show_diagnosis 诊断面板路由

系统 SHALL 提供 `show_diagnosis` 工具，返回 `_component` 字段（`type` 为 `diagnosis`）以触发前端内联诊断面板（班级障碍分布柱状图、薄弱知识点、需关注学生列表），不执行业务写库。

#### Scenario: 打开诊断面板
- **WHEN** 教师请求展示某班级的诊断面板
- **THEN** 返回 `_component`（`type`="diagnosis"）并在聊天界面内联渲染诊断图表

### Requirement: show_students 学生列表与障碍过滤

系统 SHALL 提供 `show_students` 工具，支持三模式：无班级时列出全部班级；指定班级时返回学生卡片列表；附加障碍过滤条件时按障碍类型（concept/reading/expression）筛选学生。

#### Scenario: 无班级列出班级
- **WHEN** 教师未指定班级
- **THEN** 返回全部班级列表

#### Scenario: 按障碍类型筛选
- **WHEN** 教师指定班级并附带障碍过滤条件（如 `barrier=reading`）
- **THEN** 返回该班级中主导障碍为 reading 的学生卡片列表

#### Scenario: 无过滤列出全班学生
- **WHEN** 教师指定班级但未附带障碍过滤条件
- **THEN** 返回该班级全部学生卡片列表

### Requirement: weekly_report LLM 自然语言周报

系统 SHALL 提供 `weekly_report` 工具，调用 LLM 基于学生/班级的面板数据生成 200 字左右的自然语言周报，使用通俗语言、以鼓励为主、不制造焦虑。

#### Scenario: 生成学生周报
- **WHEN** 教师或家长请求某学生的周报
- **THEN** 工具返回该学生 200 字左右的自然语言周报文本（含练习次数、正确率趋势、薄弱知识点变化）

#### Scenario: 生成班级周报
- **WHEN** 教师请求某班级的周报
- **THEN** 工具返回该班级的自然语言周报概述

#### Scenario: 无足够数据
- **WHEN** 学生/班级缺少练习或诊断数据
- **THEN** 返回「暂无足够数据」的说明，不生成虚假周报

### Requirement: assign_adaptive_practice 班级级自适应练习

系统 SHALL 提供 `assign_adaptive_practice` 工具，接受 `class_id` 为班级学生批量生成符合 ZPD 的个性化练习题，内部按每批最多 5 名学生分批处理；同时保留 `student_id` 作为单生快捷路径。该工具 SHALL 触发审批门控，教师确认后才执行。

#### Scenario: 班级级布置按批处理
- **WHEN** 教师以 class_id 触发班级自适应练习，班级学生数超过 5
- **THEN** 系统按每批 5 名学生分批生成，返回每生 ZPD 难度、主导障碍、薄弱知识点与题目数

#### Scenario: 单生快捷路径
- **WHEN** 教师以 student_id 触发单个学生的自适应练习
- **THEN** 系统为该生生成个性化 ZPD 练习

#### Scenario: 需审批门控
- **WHEN** 教师触发 assign_adaptive_practice 且尚未审批
- **THEN** Guard 拦截执行，返回 requires_approval_blocked，前端展示确认卡片

### Requirement: generate_learning_plan 预览路由

系统 SHALL 提供 `generate_learning_plan` 工具，返回 `_route` 跳转指令（跳转学生管理页并触发学习计划抽屉），不直接调用学习计划服务写库。

#### Scenario: 跳转触发学习计划生成
- **WHEN** 教师请求为某学生生成学习计划
- **THEN** 返回 `_route`（目标为学生管理页），前端加载后自动打开学习计划抽屉触发生成

#### Scenario: 工具不直接写库
- **WHEN** generate_learning_plan 被调用
- **THEN** 工具本身不创建或持久化任何学习计划记录，持久化由前端抽屉确认后经 REST API 完成

### Requirement: send_learning_plan 发送学习计划

系统 SHALL 提供 `send_learning_plan` 工具，将学习计划持久化并通知学生。该工具 SHALL 触发审批门控。

#### Scenario: 发送计划通知学生
- **WHEN** 教师确认发送某学生的学习计划
- **THEN** 系统持久化计划并创建通知（标题「新的学习计划」），学生端可见

#### Scenario: 需审批门控
- **WHEN** 教师触发 send_learning_plan 且尚未审批
- **THEN** Guard 拦截执行，返回 requires_approval_blocked

### Requirement: 工具元数据对齐

系统 SHALL 将这 7 个工具的 Persona 与 call_limit 与设计 30 §3.3 对齐：`diagnose_barrier` 对 teacher 与 parent 可用、call_limit=2；`show_diagnosis` 仅 teacher、call_limit=1；`show_students` 仅 teacher、call_limit=1；`weekly_report` 对 teacher 与 parent 可用、call_limit=2；`assign_adaptive_practice` 仅 teacher、call_limit=1、requires_approval；`generate_learning_plan` 仅 teacher、call_limit=5；`send_learning_plan` 仅 teacher、call_limit=2、requires_approval。

#### Scenario: 工具角色可达性
- **WHEN** 构建 teacher Persona 的 Agent
- **THEN** 其工具集包含上述 7 个工具；构建 parent Persona 时仅含 diagnose_barrier 与 weekly_report 两个诊断类工具

#### Scenario: 调用次数限制
- **WHEN** 同一工具在同一轮对话中超过其 call_limit
- **THEN** Guard 第二层拦截后续调用并返回 limit_exceeded

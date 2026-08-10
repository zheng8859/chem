## Purpose

诊断结果聚合——将多次作答的诊断结果汇总为学生级三维障碍画像（barrier_type JSON）和班级级障碍分布统计，为自适应练习引擎和学习报告提供输入。

## ADDED Requirements

### Requirement: 单生障碍画像聚合

系统 SHALL 对单个学生所有已诊断的错误作答进行计数聚合，生成三维障碍占比 JSON。格式 SHALL 为 `{"concept": 0.00, "reading": 0.00, "expression": 0.00}`，三个值之和为 1.0，保留两位小数。

#### Scenario: 正常聚合
- **WHEN** 学生有 10 条已诊断错误作答，其中 concept 4 条、reading 3 条、expression 3 条
- **THEN** barrier_type JSON 为 `{"concept": 0.40, "reading": 0.30, "expression": 0.30}`

#### Scenario: 无已诊断作答
- **WHEN** 学生没有任何已诊断错误作答
- **THEN** barrier_type JSON 为 `{"concept": 0.00, "reading": 0.00, "expression": 0.00}`

#### Scenario: 教师覆盖的权重
- **WHEN** 学生有诊断记录且其中部分被教师覆盖（diagnosed_by="teacher"）
- **THEN** 被覆盖的记录 SHALL 与 LLM 诊断记录等权计入计数

### Requirement: 班级障碍分布统计

系统 SHALL 对指定考试的所有学生进行班级级聚合，统计各障碍类型的学生人数分布和班级薄弱知识点排名。

#### Scenario: 班级统计
- **WHEN** 查询某班级某考试的所有学生诊断结果
- **THEN** 返回 class_barrier_distribution（concept/reading/expression 各有多少学生以此为主导障碍）和 top_weak_kps（错误率最高的知识点列表）

#### Scenario: 部分学生未诊断
- **WHEN** 班级中部分学生的作答尚未诊断
- **THEN** 诊断聚合仅覆盖已诊断的学生，未诊断学生不参与统计

### Requirement: 聚合触发时机

障碍画像聚合 SHALL 在 LLM 批量诊断完成后自动触发，逐个更新被诊断学生的 Student.barrier_type。

#### Scenario: 批量诊断后自动聚合
- **WHEN** 一批 LLM 诊断结果写入 StudentAnswer 后
- **THEN** 每个被更新的学生其 Student.barrier_type 被重新计算并写入

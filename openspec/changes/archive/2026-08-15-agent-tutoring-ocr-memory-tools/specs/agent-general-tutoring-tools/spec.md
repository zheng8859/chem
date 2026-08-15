## Purpose

定义通用辅导工具组（30 号文档 §3.4 的 3 个工具）的行为契约：通用化学讲解（教师/学生双模式）、实验模拟（结构化步骤与安全注意）、方程式配平（确定性算法，100% 准确，不依赖 LLM）。

## ADDED Requirements

### Requirement: chemistry_tutor 通用化学讲解

系统 SHALL 提供 `chemistry_tutor` 工具，接受 `topic`、`persona` 与可选 `context`，按当前角色返回讲解参数：教师角色 800 字详解模式（含示例与注意事项），学生角色 500 字引导式讲解（苏格拉底式，每次只问一个问题）。

#### Scenario: 教师角色详解
- **WHEN** 教师以 `persona="teacher"` 调用 chemistry_tutor
- **THEN** 返回 `mode="detailed"`、`max_length=800` 与详解引导语

#### Scenario: 学生角色引导
- **WHEN** 学生以 `persona="student"` 调用 chemistry_tutor
- **THEN** 返回 `mode="guided"`、`max_length=500` 与苏格拉底式提问引导语

### Requirement: simulate_experiment 实验模拟

系统 SHALL 提供 `simulate_experiment` 工具，接受 `experiment_name`，返回结构化的实验信息（实验名称、步骤列表、现象描述、化学方程式列表、安全注意事项），供前端渲染为实验卡片。

#### Scenario: 模拟实验返回完整结构
- **WHEN** 教师或学生以实验名称调用 simulate_experiment
- **THEN** 返回含 `name`、`steps`（非空）、`phenomena`、`equations`、`safety_notes` 的实验结构与前端组件标记

#### Scenario: 实验卡片组件标记
- **WHEN** simulate_experiment 返回结果
- **THEN** 结果 SHALL 含 `_component`（`type` 为 experiment-card）以触发前端内联实验卡片渲染

### Requirement: balance_equation 方程式确定性配平

系统 SHALL 提供 `balance_equation` 工具，接受反应物与生成物，调用确定性配平引擎返回配平后的方程式与系数。配平 SHALL 使用确定性算法（100% 准确），SHALL NOT 调用 LLM。引擎不可用或配平失败时 SHALL 返回 `verified=false` 与错误信息，不抛出未捕获异常。

#### Scenario: 配平成功
- **WHEN** 教师或助教以反应物与生成物调用 balance_equation
- **THEN** 返回配平后的方程式、系数与 `verified=true`

#### Scenario: 配平引擎不可用
- **WHEN** 配平引擎未安装或导入失败
- **THEN** 返回 `verified=false` 与错误说明，不抛出未捕获异常

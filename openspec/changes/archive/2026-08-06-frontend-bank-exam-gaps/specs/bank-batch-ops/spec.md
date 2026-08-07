## Purpose

题库批量操作 — 多选题目卡片后批量删除，减少逐题操作次数。

## ADDED Requirements

### Requirement: 题库卡片多选

Tab 2 题库管理的每张题目卡片 SHALL 显示 checkbox。选中卡片后 SHALL 出现底部批量操作栏，显示已选数量和"批量删除"按钮。

#### Scenario: 勾选多张卡片
- **WHEN** 教师勾选 3 张题目卡片
- **THEN** 底部操作栏显示"已选 3 项 [批量删除]"

#### Scenario: 取消所有勾选
- **WHEN** 教师取消所有勾选
- **THEN** 底部操作栏消失

### Requirement: 批量删除

点击"批量删除" SHALL 弹出确认对话框。确认后 SHALL 对每道选中题目调用 `DELETE /api/v1/question-sets/items/{id}` 逐个移除。

#### Scenario: 批量删除确认
- **WHEN** 教师点击"批量删除"并确认
- **THEN** 选中的题目从当前文件夹移除，卡片列表更新，文件夹计数刷新

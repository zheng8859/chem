## Context

三个功能缺口均只涉及 `exam-v2.html` 前端改动，后端 API 已全部就绪。See proposal.md.

## Goals / Non-Goals

**Goals:** Tab 4 导出按钮、Tab 2 checkbox 批量删除、Tab 3 加入考试按钮。
**Non-Goals:** 不新增后端端点、不新增依赖、不动弹框系统。

## Decisions

### 1. 导出：直接触发浏览器下载

**选择:** `<a>` 标签 `href` 指向导出 URL，`download` 属性触发保存。

**替代方案:** `fetch` + Blob → 手动触发下载。更复杂但可加 loading 状态。

**选择 A 标签**：更简单，浏览器原生处理下载进度，无需前端状态管理。

### 2. 批量操作：checkbox + 底部浮动栏

**选择:** 每张卡片加 checkbox（复用 checklist `v-model` 模式），底部条件渲染浮动操作栏。批量删除逐条调 `DELETE /question-sets/items/{id}`。

**理由:** 复用现有 `checkedItems` 模式，不引入新数据结构。批量删除无需新后端端点。

### 3. 加入考试：复用现有 `addQuestionsToExam` checklist 弹窗

**选择:** `addToExam(he)` 调用 `api.get('/exams')` 加载考试列表 → `showModal('select')` → `api.post('/exams/{id}/questions', null, { question_ids: [he.id] })`。

**理由:** 与 Tab 1 题目卡片的"加入考试"逻辑完全相同，只是来源不同。

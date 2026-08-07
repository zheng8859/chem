## 1. Tab 4 考试导出按钮

- [x] 1.1 考试卡片模板加"导出"按钮（仅 `completed` 状态可见）
- [x] 1.2 导出按钮用 `<a>` 标签指向 `GET /api/v1/exams/{id}/export?format=docx&with_answers=false`，加 `download` 属性

## 2. Tab 2 批量操作

- [x] 2.1 题库卡片模板加 checkbox（`v-model="bankChecked[item.id]"`）
- [x] 2.2 新增 `bankChecked` reactive 对象 + `bankCheckedCount` computed
- [x] 2.3 底部条件渲染批量操作栏："已选 N 项 [批量删除]"
- [x] 2.4 `batchRemove` 函数：确认弹窗 → 逐条 `DELETE /question-sets/items/{id}` → 刷新列表和计数

## 3. Tab 3 加入考试

- [x] 3.1 真题卡片模板加"加入考试"按钮
- [x] 3.2 `addHistoryToExam(he)` 函数：`GET /exams` → `showModal('select')` → `POST /exams/{id}/questions`

## 4. 验证

- [x] 4.1 导出：验证点击导出按钮触发 .docx 下载
- [x] 4.2 批量删除：勾选 2 张卡片 → 批量删除 → 验证列表刷新
- [x] 4.3 加入考试：真题加入考试 → 验证考试题目列表增加

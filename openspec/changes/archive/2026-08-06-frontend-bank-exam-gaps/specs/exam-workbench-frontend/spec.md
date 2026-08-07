## ADDED Requirements

### Requirement: 真题卡片加入考试

Tab 3 历史真题库的每张真题卡片 SHALL 提供"加入考试"按钮。点击后 SHALL 弹出 checklist 弹窗列出所有可用考试，教师选择目标考试后 SHALL 调用 `POST /api/v1/exams/{id}/questions` 将真题关联到考试。

#### Scenario: 将真题加入考试
- **WHEN** 教师在真题卡片上点击"加入考试"并选择目标考试
- **THEN** 真题被添加到该考试，Toast 提示"已加入考试"

#### Scenario: 无考试可选时提示
- **WHEN** 教师点击"加入考试"但考试列表为空
- **THEN** Toast 提示"暂无可用考试，请先创建考试"

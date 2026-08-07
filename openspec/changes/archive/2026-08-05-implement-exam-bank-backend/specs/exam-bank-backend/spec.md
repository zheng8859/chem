## Purpose

题库管理后端能力 — 系统预设文件夹保护、考试题目计数、删除安全策略、ChromaDB 向量检索 RAG 上下文接入。

## ADDED Requirements

### Requirement: 系统预设文件夹不可删除

QuestionSet SHALL 包含 `is_system` 字段标识系统预设文件夹。`DELETE /question-sets/{id}` SHALL 校验：当 `is_system=true` 时返回 403 Forbidden。

#### Scenario: 删除系统预设文件夹被拒绝
- **WHEN** 教师尝试删除 `is_system=true` 的文件夹
- **THEN** 返回 403，detail 包含"系统预设文件夹不可删除"

#### Scenario: 删除普通文件夹成功
- **WHEN** 教师删除 `is_system=false` 的文件夹
- **THEN** 文件夹被删除，关联 item 被级联删除，题目实体保留

### Requirement: 考试列表显示题目数

`GET /exams` 列表中的每个考试 SHALL 包含 `question_count` 字段，值为当前考试关联的题目数量。

#### Scenario: 创建考试后题目数为0
- **WHEN** 新创建的考试尚未添加题目
- **THEN** `question_count` 为 0

#### Scenario: 添加题目后题目数更新
- **WHEN** 向考试添加 3 道题目后查询考试列表
- **THEN** `question_count` 为 3

### Requirement: 考试删除安全策略

`DELETE /exams/{id}` SHALL 校验考试状态：`in_progress` 状态禁止删除，仅 `pending` 和 `completed` 状态允许删除。

#### Scenario: 删除进行中的考试被拒绝
- **WHEN** 教师尝试删除 status=`in_progress` 的考试
- **THEN** 返回 403，detail 包含"进行中的考试不可删除"

#### Scenario: 删除已完成的考试成功
- **WHEN** 教师删除 status=`completed` 的考试
- **THEN** 考试记录、题目关联、答题记录被级联删除

### Requirement: 向量检索 RAG 上下文

AI 出题的 `_rag_search` SHALL 优先使用 ChromaDB 向量检索获取相似真题上下文。SHALL 实现两层检索：关键词匹配（初筛 Top-20）→ ChromaDB 向量精筛。ChromaDB 不可用时 SHALL 降级为纯关键词匹配。

#### Scenario: 向量检索返回相似题目
- **WHEN** 调用 `generate_questions` 且 ChromaDB 可用
- **THEN** RAG 上下文包含向量检索返回的相似真题，LLM Prompt 包含"基于以下真题生成变种题"

#### Scenario: ChromaDB 不可用时降级
- **WHEN** ChromaDB 服务不可用
- **THEN** 系统降级为关键词匹配，LLM 调用不受影响，日志记录降级事件

## Purpose

定义出题与题库 Agent 工具组（7 个工具）的行为契约：三级题库搜索、联网搜索、内联出题面板、LLM 出题与四维审核、三实体入库与向量同步、题库列表与删除，以及这些工具的 Persona 与调用次数元数据。

## ADDED Requirements

### Requirement: 三级题库搜索

系统 SHALL 提供 `search_exam_bank` 工具，按三级递进策略搜索题库：第一层关键词匹配（按知识点、难度、题型过滤）；第二层向量召回（ChromaDB 相似度 ≥ 0.6 补充）；第三层联网搜索兜底（前两层不足 3 条且有关键词时触发，结果明确标记为「AI 补充」）。

#### Scenario: 关键词匹配返回结果
- **WHEN** 用户提供的关键词在题库知识点标签中命中达到请求数量（limit）条
- **THEN** 返回命中的题目列表，不触发向量检索或联网搜索

#### Scenario: 关键词不足时向量补充
- **WHEN** 关键词匹配结果少于请求数量且向量检索可用
- **THEN** 系统用向量检索补充结果，按相似度降序排列

#### Scenario: 前两层仍不足时联网兜底
- **WHEN** 关键词匹配与向量检索结果合计仍少于 3 条且提供了关键词
- **THEN** 系统调用联网搜索补充，结果标记为「AI辅助搜索」

### Requirement: 联网搜索

系统 SHALL 提供 `web_search` 工具，执行真实联网搜索并将结果经 LLM 摘要到 400 字以内返回。

#### Scenario: 联网搜索返回摘要
- **WHEN** 用户请求联网搜索某个化学概念或资料
- **THEN** 返回查询词与不超过 400 字的搜索结果摘要

### Requirement: 内联出题面板

系统 SHALL 提供 `show_exam_workbench` 工具，返回 `_component` 字段（`type` 为 `exam-workbench`）以触发前端内联出题面板，不执行业务逻辑。

#### Scenario: 打开出题面板返回组件指令
- **WHEN** 用户表达出题意图但参数不完整
- **THEN** 返回 `_component`（`type`="exam-workbench"）并在聊天界面内联渲染出题面板

### Requirement: LLM 出题与四维审核

系统 SHALL 提供 `generate_questions` 工具，经 RAG 检索 → LLM 生成 → 四维方程式审核 → 重试 → 返回通过审核的题目列表。工具 SHALL 支持 `question_types`（题型）与 `variant_qid`（变体蓝本题）参数。

#### Scenario: 生成题目并通过审核
- **WHEN** 用户提供知识点、难度、数量
- **THEN** 返回经四维审核通过的题目列表，含审核结果

#### Scenario: 方程式审核失败自动重试
- **WHEN** LLM 生成的题目方程式四维审核判定为 blocked
- **THEN** 系统自动重试生成（最多 3 次），仍 blocked 则丢弃该题

#### Scenario: 变体题透传蓝本题
- **WHEN** 用户指定 variant_qid 蓝本题 ID
- **THEN** 系统以该真题为上下文生成变体题，并标记 RAG 来源

### Requirement: 保存到题库三实体入库

系统 SHALL 提供 `save_to_bank` 工具，自动生成题库文件夹名，创建 QuestionSet、逐题创建 Question 并建立 QuestionSetItem 关联，同步向量索引，并返回 `_route` 导航指令。

#### Scenario: 保存题目创建文件夹与关联
- **WHEN** 用户保存若干题目到题库
- **THEN** 系统创建 QuestionSet 文件夹，逐题入库并建立关联，增量同步 ChromaDB

#### Scenario: 保存后返回导航
- **WHEN** 题目保存成功
- **THEN** 返回 `_route`（page 指向题库页）以跳转到题库 Tab

### Requirement: 题库列表与删除

系统 SHALL 提供 `list_banks`（返回题库文件夹名称与题目数）与 `delete_bank`（需审批，删除文件夹及关联但保留题目实体，系统预设文件夹不可删除）。

#### Scenario: 列出题库文件夹
- **WHEN** 用户请求查看题库列表
- **THEN** 返回所有题库文件夹的 ID、名称与题目数量

#### Scenario: 删除题库需审批
- **WHEN** 用户请求删除题库
- **THEN** 触发审批门控，未经教师确认不执行删除

#### Scenario: 系统预设文件夹不可删除
- **WHEN** 用户请求删除系统预设文件夹
- **THEN** 返回拒绝，文件夹保留

### Requirement: 工具元数据对齐

7 个工具的 Persona 与 call_limit SHALL 与设计文档对齐：`web_search` 对全部 4 个角色可用；`save_to_bank`/`list_banks`/`delete_bank`/`generate_questions` 对 tutor 与 teacher 可用；call_limit 分别为 search=3、web=2、workbench=3、save=1、generate=5、list=1、delete=1。

#### Scenario: 工具角色可达性
- **WHEN** 构建 tutor 或 teacher Persona 的 Agent
- **THEN** 其工具集包含上述 7 个工具（save_to_bank 等对 tutor 也可见）

#### Scenario: 调用次数限制
- **WHEN** 同一工具在同一轮对话中超过其 call_limit
- **THEN** Guard 第二层拦截后续调用并返回 limit_exceeded

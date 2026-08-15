## Context

当前 7 个出题/题库工具（`chemai-backend/agent/tools/exam_tools.py`）已注册但实现残缺：3 个运行时崩溃、2 个占位桩、元数据漂移。服务层能力其实已齐备——`VectorSearchService` 已实现三层检索的层 1+层 2、`TeachingService.create_question` / `QuestionBankService` 三实体 CRUD 已就绪、`question_generation_service.generate_questions` 已支持 `question_types` 与 `variant_qid` 透传、`index_questions` 已实现增量向量同步。因此本变更的核心是「把工具层正确接到服务层」，而非新建服务。动机见 proposal.md - Why。

关键约束（来自 CLAUDE.md 与 CONTEXT.md）：
- 简单优先：不引入新外部依赖；联网搜索复用 MiMo 的 search 能力（CONTEXT.md §10.3「MiMo + DeepSeek 总结」），不接 Tavily/SerpAPI。
- 手术式修改：不改服务层签名，只修工具层与 SSE 适配器两处。
- 前端契约已定：`index.html` 的 component handler 读 `comp.type`/`comp.props`，navigate handler 读 `data.page`/`data.params`。

## Goals / Non-Goals

**Goals:**
- 让 7 个工具端到端可用，教师能在对话里完成「搜题 → 出题 → 存库」闭环。
- 统一 SSE `_component`/`_route` 契约到前端已消费的形状。
- 修正 7 个工具的 `persona` 与 `call_limit` 元数据。

**Non-Goals:**
- 不改服务层 API（`question_generation_service`、`question_bank_service`、`vector_search_service` 的既有签名不动）。
- 不改前端出题工作台 4 Tab 的渲染逻辑（`renderExamWorkbench` 硬编码 Tab 保持不变）。
- 不引入新的联网搜索供应商或消息队列。
- 不处理 OCR、考试发布、练习派发等其他工具组。

## Decisions

### D1 — 工具层只做「参数规整 + 调服务层」，不含业务逻辑
每个工具把 LLM 给的松散参数转成 Pydantic schema / 服务层入参，业务规则留在服务层。理由：服务层已被 API 端点和集成测试覆盖，复用即获得正确性；在工具层重写会重复且易漂移。
- 备选：在工具层内联实现三实体入库逻辑 —— 否决，违反「简单优先」且重复服务层。

### D2 — `search_exam_bank` 三层策略与数据源
Tier 1 关键词匹配打在 **Question（题库题目）** 表（`content`/`knowledge_point_tags`/`difficulty`/`question_type`）；Tier 2 用 `search_questions_vector` 对候选集语义重排（相似度 ≥ 0.6 才补充，见 `vector_search_service.SIMILARITY_THRESHOLD`），并对 **HistoricalExam（历年真题）** 用 `VectorSearchService.search_similar` 补充；Tier 3 前两层合计 < 3 且有关键词时调用 `web_search` 兜底并标记「AI辅助搜索」。每条结果带 `source`（`bank`/`historical`/`web`）。
- 备选：只搜 Question 表忽略真题 —— 否决，教师出题依赖真题做 RAG/变体参照（CONTEXT.md §10.5）。

### D3 — `web_search` 用 MiMo search + DeepSeek 摘要
`web_search` 调用 MiMo（`PROVIDER_CONFIG["mimo"]["capabilities"]` 含 `search`）发起带搜索的请求拿原始结果，再用 DeepSeek 摘要到 ≤400 字返回。MiMo 不可用（无 `MIMO_API_KEY`）或调用失败时降级返回现有占位文案，不让 Agent 循环中断。
- 备选：接 Tavily/SerpAPI —— 否决，新增外部依赖与 key，违背简单优先。

### D4 — `save_to_bank` 改批量入库签名
签名从单题字段（`stem/answer/question_type/...`）改为 `questions: list[dict]` + 可选 `bank_name`，一次调用保存多题（匹配 `call_limit=1`）。每题为 `{content, answer, question_type, difficulty, knowledge_points, options, analysis}`。流程：`bank_name` 为空则自动命名（时间戳 + 知识点），`create_question_set` 建文件夹 → 逐题 `create_question`（`source=ai_generated`）→ `add_item` 建关联 → `index_questions` 增量同步 ChromaDB → 返回 `_route`。
- 备选：保留单题签名、Agent 多次调用 —— 否决，与 `call_limit=1` 及「一次存一批」的对话意图冲突。

### D5 — `generate_questions` 透传 `question_types` 与 `variant_qid`，修正审核汇总
工具新增 `question_types: list[str]` 与 `variant_qid: str` 入参并透传服务层（服务层已支持）。审核汇总改用 `QuestionRead` 的 `audit_status` 字段（`q.audit_status == "passed"`）而非对 Pydantic 对象调 `.get("audit_passed")`（当前崩溃点）。
- 备选：在工具层自行解析 RAG/审核 —— 否决，服务层已有 `_parse_llm_response`/`_build_rag_mark`。

### D6 — SSE 契约：`_component` 用 `props`，`_route` 铺平为 `{page, params}`
`_component` 载荷字段统一为 `{type, props}`（对齐前端 `comp.type`/`comp.props`）；`adapter_v2.py` 的 navigate 事件发射铺平为 `{page, params}`（当前误包成 `{route: {...}}`，前端 `handleNavigate` 读的是 `data.page`/`data.params`）。`show_exam_workbench` 与 `save_to_bank` 分别返回 `_component` 与 `_route`。
- 备选：改前端读 `params`/`route` —— 否决，前端是已交付的消费方，且 `agent-engine-core` 主规格本就写 `{page, params}`，是适配器实现跑偏。

### D7 — 元数据对齐
7 工具的 `persona`/`call_limit` 对齐设计：`web_search` 补 `parent`（4 角色全可见）；`save_to_bank`/`list_banks`/`delete_bank`/`generate_questions` 补 `tutor`；call_limit 统一为 search=3、web=2、workbench=3、save=1、generate=5、list=1、delete=1（降低当前 10/20/30 的冗余额度，避免单轮刷屏）。

## Risks / Trade-offs

- [MiMo search 的 `enable_search` 传参方式未经验证] → 用 `model_kwargs`/`extra_body` 传参，失败时降级占位文案；并在集成测试里 mock MiMo 响应验证降级路径，不依赖真实联网。
- [`save_to_bank` 批量入库失败会残留半套数据（文件夹已建、题目部分写入）] → 单事务内顺序写入，异常时回滚；`index_questions` 同步放在事务提交之后，向量索引失败不影响主流程。
- [搜索三层合并后结果可能重复（同一题同时命中关键词与向量）] → 按 `(source, id)` 去重，向量只补充关键词未命中的候选。
- [`call_limit` 大幅调低可能限制合法长对话] → 额度按「单轮对话意图」设计（save/generate/list/delete 均为一次性动作），必要时后续单独调。

## Migration Plan

- 无数据库 schema 迁移：三实体表与 ChromaDB collection（`chemai_questions`）均已存在，`index_questions` 增量写入即可。
- 部署顺序：先合并后端工具层 + 适配器修复 → 前端 `index.html` 的 `handleNavigate`/component 契约本已兼容，无需改前端 → 重启后触发 `index_questions` 增量同步即可。
- 回滚：本变更不改 schema，回滚即 `git revert` 对应 commit；已写入的题目数据无害残留，可后续手动清理。

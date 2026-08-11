## Why

Docs 45-53 已完成 10 个功能模块的后端实现（141 API端点、25 Service、6 Skill Engine）和 14 个前端页面，现有 1305 条 pytest 全部通过。但这些测试覆盖的是"代码正确性"（函数输入输出、API Schema、CRUD），缺乏"AI 内容质量"（出题科学性、诊断准确性、辅导质量）和"系统行为安全"（路由正确性、安全隔离、错误恢复）的评测能力。v0.4.0 的基线数据（L1 覆盖率 51.92%，目标 95%）也表明质量门禁尚未生效。Doc 32（评测体系设计）和 Doc 54（Evals 评测体系搭建）已提供完整的设计规格，需要在 v0.5.0 中实现。

## What Changes

- 新建 **100 条 Golden 样本**（5 化学模块 × 20 样本，含出题/诊断/辅导三类），JSON 格式存储 + SQLite 种子脚本
- 新建 **L1 评测测试 35 道**（规则引擎、置信度融合、状态机、难度评估、工具函数）
- 新建 **L2 评测测试 26 道**（出题 API、诊断 API、对话 API、数据库 CRUD）
- 新建 **L3 质量测试 20 道**（真实 LLM 调用，标记 @slow，验证出题科学性与诊断准确率）
- 新建 **eval_utils.py**（科学性检查、语义相似度、诊断对比、关键词匹配、难度评估、指标聚合 6 个纯函数）
- 新建 **evals conftest.py**（Golden 数据集加载、API client、认证 token fixtures）
- 新建 **pytest.ini**（l1/l2/l3/slow 标记定义）
- 扩展 **run_evals.py**（新增 --run-slow、--save-baseline、--compare 选项，支持 tests/evals/ 路径，HTML 报告输出）
- 新建 **CI workflow**（`.github/workflows/evals-ci.yml`：L1 阻断 + L2/L3 劣化告警）
- 新建 **Golden 数据集 Schema**（`tests/evals/golden_dataset/schema.json`）
- 已有测试和 run_evals.py 框架**不受破坏性变更**

## Capabilities

### New Capabilities

- `evals-golden-dataset`: 100 条化学 Golden 样本的结构化存储（JSON + SQLite），覆盖 5 大化学模块（化学平衡/酸碱盐/氧化还原/有机化学/化学计量），每模块含出题样本（8）、诊断样本（8）、对话辅导样本（4），每条样本包含输入、预期输出、容差参数和评测类型标记
- `evals-quality-gate`: L1/L2/L3 三层质量门禁框架，L1（单元+规则引擎，≥95%通过，阻断合并）、L2（API 集成，≥90%通过，阻断合并）、L3（AI 内容质量 Golden + LLM 评测，≥70%通过，劣化>5%告警），含基线对比、CI 自动运行和 HTML/JSON 报告

### Modified Capabilities

<!-- 无已有 spec 被修改。evals 体系是新增基础设施，不改变现有功能模块的行为 -->

## Impact

- **新增目录**: `tests/evals/`（golden_dataset/ + baseline/ + boundary/ + regression/ 测试文件）
- **新增文件**: `app/utils/eval_utils.py`、`scripts/seed_golden.py`、`pytest.ini`、`.github/workflows/evals-ci.yml`
- **修改文件**: `scripts/run_evals.py`（扩展 CLI 选项和路径，非破坏性）
- **新增数据**: `tests/evals/golden_dataset.db`（SQLite）、`data/evals/baseline.json`（更新至 v0.5.0）
- **依赖**: pytest、pytest-cov、pytest-json-report（已有）；L3 测试需 MIMO_API_KEY / DASHSCOPE_API_KEY 环境变量
- **CI 影响**: 新增 GitHub Actions workflow，每次 PR 触发 L1+L2+L3 评测
- **不影响**: 现有 1305 条测试、现有 API 端点、现有前端页面

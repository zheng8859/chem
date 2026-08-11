## Purpose

为 ChemAI 项目提供 L1/L2/L3 三层质量门禁框架，自动运行评测、对比基线、检测劣化，在 CI 中阻断不合格变更合并。

## ADDED Requirements

### Requirement: 三层评测金字塔

系统 SHALL 按 L1（单元层）、L2（集成层）、L3（质量层）三层组织评测。L1 目标通过率 ≥95%（阻断合并），L2 目标通过率 ≥90%（阻断合并），L3 目标通过率 ≥70%（劣化>5% 告警）。

#### Scenario: L1 通过判定
- **WHEN** L1 测试（单元测试 + 规则引擎）通过率 ≥95% 且覆盖率 ≥95%
- **THEN** L1 verdict 为 passed

#### Scenario: L1 不通过阻断
- **WHEN** L1 测试通过率 < 95% 或覆盖率 < 95%
- **THEN** L1 verdict 为 failed，CI 返回非零退出码阻断合并

#### Scenario: L2 通过判定
- **WHEN** L2 测试（API 集成测试）通过率 ≥90%
- **THEN** L2 verdict 为 passed

#### Scenario: L3 劣化告警
- **WHEN** L3 测试（Golden + LLM 质量评测）通过率较基线下降 > 5%
- **THEN** CI 在 PR 中自动评论告警，但不阻断合并

### Requirement: 分标记运行

系统 SHALL 支持通过 pytest 标记（@pytest.mark.l1、@pytest.mark.l2、@pytest.mark.l3、@pytest.mark.slow）精确选择运行范围。

#### Scenario: 仅运行 L1 标记的测试
- **WHEN** 执行 `pytest -m l1`
- **THEN** 仅运行标记了 @pytest.mark.l1 的测试函数

#### Scenario: L3 慢速测试默认跳过
- **WHEN** 执行 `pytest -m l3` 而不带 --run-slow
- **THEN** 标记了 @pytest.mark.slow 的 L3 测试被自动跳过

#### Scenario: --run-slow 启用 L3 慢速测试
- **WHEN** 执行 `pytest -m l3 --run-slow`
- **THEN** 所有 L3 测试（含 @pytest.mark.slow）全部运行

### Requirement: 基线对比与劣化检测

系统 SHALL 在每次评测后与基线文件（data/evals/baseline.json）对比，检测 L1/L2/L3 通过率的劣化。劣化 ≤5% 为正常波动，>5% 告警，>10% 建议阻断。

#### Scenario: 正常波动不告警
- **WHEN** L3 当前通过率 68%，基数为 70%，劣化 2%
- **THEN** 系统判定为正常波动，不告警

#### Scenario: 严重劣化告警
- **WHEN** L3 当前通过率 62%，基数为 70%，劣化 8%
- **THEN** 系统标记为严重劣化，PR 中自动评论告警

### Requirement: CLI 运行器

系统 SHALL 提供 run_evals.py CLI，支持 --level（l1/l2/l3/all）、--baseline（生成基线）、--ci（CI 严格模式）、--json（JSON 输出）、--run-slow（启用 L3 慢速测试）、--save-baseline（保存结果为新基线）、--compare（对比指定基线文件）和 --output（指定报告输出路径）选项。

#### Scenario: 全量评测运行
- **WHEN** 执行 `python scripts/run_evals.py`
- **THEN** 依次运行 L1、L2、L3，输出各层通过率和 verdict，保存 JSON 报告

#### Scenario: 生成新基线
- **WHEN** 执行 `python scripts/run_evals.py --baseline`
- **THEN** 运行全量评测后更新 data/evals/baseline.json，exit 0

#### Scenario: CI 模式基线对比失败
- **WHEN** 执行 `python scripts/run_evals.py --ci` 且基线对比有指标劣化 >5%
- **THEN** exit 1，输出劣化明细

### Requirement: 评测报告生成

系统 SHALL 每次评测运行后生成结构化报告。JSON 报告保存到 data/evals/reports/，HTML 报告支持 --output 指定路径。

#### Scenario: JSON 报告保存
- **WHEN** 评测运行完成
- **THEN** data/evals/reports/ 目录下生成 eval_{timestamp}.json，包含 meta（工具版本、时间戳、运行层级）、各层测试结果（总数、通过、失败、通过率、耗时）、基线对比结果和 verdict

#### Scenario: HTML 报告输出
- **WHEN** 执行 `python scripts/run_evals.py --output reports/evals.html`
- **THEN** 生成单文件 HTML 报告，含颜色编码（绿/黄/红）、各层通过率卡片、失败明细列表、基线对比趋势

### Requirement: eval_utils 工具函数

系统 SHALL 提供 6 个纯函数工具：check_scientific_accuracy（科学性检查）、keyword_match_ratio（关键词匹配率）、semantic_similarity（语义相似度，基于 SequenceMatcher）、compare_diagnosis（诊断结果比较）、difficulty_match_score（难度匹配得分）、compute_metrics（聚合指标计算）。

#### Scenario: 诊断结果语义匹配
- **WHEN** 实际诊断输出"勒夏特列原理方向混淆"，预期输出"勒夏特列原理中温度效应理解错误"
- **THEN** semantic_similarity() 返回 ≥0.6，compare_diagnosis() 判定为匹配

#### Scenario: 难度精确匹配
- **WHEN** 期望难度 3，实际生成难度 3
- **THEN** difficulty_match_score() 返回 1.0

#### Scenario: 难度差1级部分匹配
- **WHEN** 期望难度 2，实际生成难度 3
- **THEN** difficulty_match_score() 返回 0.7

### Requirement: CI 工作流

系统 SHALL 提供 GitHub Actions 工作流（.github/workflows/evals-ci.yml），包含两个 Job：l1-gate（L1 测试，<95% 通过率时 exit 1 阻断合并）和 l2-l3-evals（依赖 l1-gate 通过，下载历史基线 artifact 并对比，劣化>5% 时自动 PR 评论告警）。

#### Scenario: L1 失败阻断 PR 合并
- **WHEN** L1 测试通过率 < 95%
- **THEN** l1-gate Job 返回失败，PR 显示 "Quality Gate Failed"，阻止合并

#### Scenario: L2/L3 劣化自动评论
- **WHEN** L2 或 L3 劣化 > 5%
- **THEN** l2-l3-evals Job 在 PR 中自动评论，列出劣化指标和幅度，但不阻止合并

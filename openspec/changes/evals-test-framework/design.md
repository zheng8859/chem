## Context

项目已有完整的基础设施：`scripts/run_evals.py`（543 行 CLI 运行器）、`data/evals/baseline.json`（v0.4.0 基线）、`tests/conftest.py`（DB 隔离 + JWT fixtures）、1305 条现有 pytest 测试。本次设计在这个基础上扩展，不重写、不破坏已有结构。详见 proposal.md。

## Goals / Non-Goals

**Goals:**
- 新建 100 条 Golden 样本的 JSON 数据（5 模块 × 20 样本），附带 JSON Schema 校验
- 新建 L1/L2/L3 三层 evals 专用测试文件（81 道）
- 实现 eval_utils.py 6 个纯函数工具
- 扩展 run_evals.py 支持新路径、--run-slow、HTML 报告
- 新建 GitHub Actions CI workflow
- 新建 pytest.ini 定义 l1/l2/l3/slow 标记

**Non-Goals:**
- 不改动已有 1305 条测试的代码或目录结构
- 不实现 Doc 32 的完整 109 场景——本次只做 Doc 54 的 AI 内容质量层（81 道）+ run_evals 框架扩展
- 不重写 run_evals.py——手术式扩展
- 不新建独立的 LLM-as-Judge 评分 LLM 调用——L3 使用已有 LLM provider
- 不实现性能基线场景（PERF-001~008），Phase 3 再做

## Decisions

### 决策 1: 目录结构 — 在 tests/evals/ 下按 Doc 32 的三层组织

```
tests/evals/
├── conftest.py                  # evals 专用 fixtures (Golden加载/API client)
├── golden_dataset/              # 100 Golden 样本数据
│   ├── schema.json              # JSON Schema 校验
│   ├── chemical_equilibrium.json
│   ├── acid_base.json
│   ├── redox.json
│   ├── organic.json
│   └── stoichiometry.json
├── baseline/                    # L1/L2 测试 (对应 Doc 32 基线层)
│   ├── test_l1_rule_engine.py   # L1: 35 道 (规则引擎/置信度/状态机)
│   └── test_l2_api_quality.py   # L2: 26 道 (出题API/诊断API/对话API)
└── regression/                  # L3 测试 (对应 Doc 32 回归层)
    └── test_l3_ai_quality.py    # L3: 20 道 (真实LLM调用, @slow)
```

**理由**: 已有 tests/golden/ 放的是审核引擎 Golden (audit_golden_86 + ocr_pipeline)，是确定性算法测试。新的 AI 内容质量测试分开放置，避免混淆。三层目录结构从 Day 1 就预留给未来的边界层和回归层测试。

**否决的替代方案**: 将 AI Golden 测试混入已有 tests/golden/——会导致 golden/ 目录职责模糊（既测确定性算法又测 LLM 输出质量）。

### 决策 2: 测试标记策略 — 路径驱动 + 标记辅助

**选择**: 保持 run_evals.py 的路径驱动方式（L1=tests/unit, L2=tests/integration, L3=tests/golden+tests/evals），同时在新测试中使用 @pytest.mark 标记实现精确选择。

**run_evals.py 扩展**:
- L1: `pytest tests/unit` → 不变
- L2: `pytest tests/integration` → 不变  
- L3: `pytest tests/golden tests/evals` → 新增 tests/evals 路径
- 新增 `--run-slow` 传递给 pytest 以启用 @slow 标记的测试

**理由**: 不改动已有 1305 条测试（不需要给它们加标记），新测试用显式标记。路径驱动简单可靠，标记辅助提供灵活的选择性运行。

### 决策 3: Golden 数据集存储 — JSON 文件为主，SQLite 为辅

**选择**: JSON 文件作为 Golden 样本的单一数据源（source of truth），seed_golden.py 将 JSON 导入 SQLite 用于程序化查询和运行记录追踪。

**SQLite 表结构**:
```sql
CREATE TABLE golden_samples (
    id TEXT PRIMARY KEY,
    module TEXT NOT NULL,
    category TEXT NOT NULL,
    eval_type TEXT NOT NULL,
    data_json TEXT NOT NULL  -- 完整 JSON 原文
);
CREATE TABLE eval_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    total_samples INTEGER,
    passed INTEGER,
    failed INTEGER,
    pass_rate REAL,
    failed_ids TEXT  -- JSON array
);
```

**理由**: JSON 文件可直接被 pytest 和 eval_utils 加载，零依赖。SQLite 提供查询能力（如"查询所有氧化还原模块的 L3 诊断样本"）和运行记录持久化。

### 决策 4: eval_utils.py 函数设计 — 纯函数，零外部依赖

**选择**: 6 个函数全部为无副作用的纯函数，不依赖数据库、不调 LLM、不读文件系统。

函数签名：
```python
def check_scientific_accuracy(questions: list[dict]) -> float  # 返回 0.0-1.0
def keyword_match_ratio(output: str, keywords: list[str]) -> float  # 返回 0.0-1.0
def semantic_similarity(text_a: str, text_b: str) -> float  # SequenceMatcher, 0.0-1.0
def compare_diagnosis(actual: str, expected: str) -> bool   # 语义匹配 >=0.6
def difficulty_match_score(expected: int, actual: int) -> float  # 精确1.0, 差1级0.7, 差2级0.3
def compute_metrics(results: list[dict]) -> dict  # {pass_rate, avg_score, degradation}
```

**理由**: 纯函数 = 可独立测试、可被 L1 层自身覆盖、零 mock 需求。与 Doc 54 第二章定义的容差参数一一对应。

### 决策 5: L3 测试的 LLM 调用策略 — 使用已有 provider + Mock 回退

**选择**: L3 测试优先使用环境变量中的 API Key（MIMO_API_KEY / DASHSCOPE_API_KEY / DEEPSEEK_API_KEY）调用真实 LLM。无 API Key 时自动跳过 L3 测试，不影响 L1/L2。

**实现**: L3 测试文件使用 `@pytest.mark.slow` + `@pytest.mark.l3` 双标记。通过 conftest.py 的 `--run-slow` 和 API Key 存在性双重检查决定是否执行。

**理由**: L3 测试依赖外部 LLM 服务，不是所有开发环境都配置了 API Key。不应因为缺少 API Key 导致本地开发流程中断。

**否决的替代方案**: 完全 Mock LLM 调用——Mock 测试无法验证真实 AI 输出质量，失去 L3 层的意义。

### 决策 6: run_evals.py 扩展方式 — 手术式加功能

**选择**: 在现有 543 行 run_evals.py 上增加 4 个能力：
1. `run_l3()` 增加 tests/evals 路径
2. 新增 `--run-slow` flag 传递给 pytest
3. 新增 `--save-baseline` flag = 运行 + 保存基线（合并原 --baseline 的快照逻辑）
4. 新增 `--output <path>` 生成 HTML 报告
5. 新增 `--compare <file>` 对比指定基线

**理由**: 现有代码质量好，函数拆分清晰（run_pytest / run_coverage / load_baseline / compare_to_baseline / compute_verdict / save_report），每个都是可独立扩展的单元。

## Risks / Trade-offs

- **[风险] L3 测试因 LLM 随机性导致间歇性失败** → 缓解: L3 不阻断合并，仅告警；通过 Pass@K（多次运行取平均）减少方差；容差参数（±15% 置信度范围）吸收正常波动
- **[风险] Golden 样本的预期输出随产品迭代可能过时** → 缓解: 样本 version 字段标记；每次基线更新时同步审查样本；支持教师人工复核后更新
- **[风险] CI workflow 中 L3 测试消耗 API 费用** → 缓解: L3 仅在 PR 时触发（不在每次 commit）；20 道 L3 测试每次约消耗 API token < 5000；可通过 `--run-slow` 按需运行
- **[风险] eval_utils.semantic_similarity 使用 SequenceMatcher 而非 Embedding** → 缓解: Doc 54 明确指定使用 SequenceMatcher（阈值 0.6），这是有意的简单实现。后续可升级为 Embedding 但不改变接口
- **[风险] SQLite 并发写入** → 缓解: 评测是单进程顺序执行，不存在并发冲突；seed_golden.py 使用幂等 INSERT OR REPLACE

## Open Questions

- L3 测试的 LLM-as-Judge 评分 LLM（Doc 32 维度 7/9/11）本次不做——等 AI 内容质量评测基线稳定后再引入独立的评分 LLM
- HTML 报告的具体样式和模板——实现时参考设计文档的配色系统（Oxford Blue / Teal / 语义色），不需要预先设计

#!/usr/bin/env python3
"""seed_golden — ChemAI Golden 数据集种子脚本 (v0.5.0)

将 tests/evals/golden_dataset/*.json 导入 SQLite 数据库，
用于程序化查询和评测运行记录追踪。

用法:
    python scripts/seed_golden.py              # 导入所有模块
    python scripts/seed_golden.py --validate   # 仅校验 JSON 格式
    python scripts/seed_golden.py --module redox  # 仅导入指定模块
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = PROJECT_ROOT / "chemai-backend" / "tests" / "evals" / "golden_dataset"
DB_PATH = GOLDEN_DIR / "golden_dataset.db"
SCHEMA_PATH = GOLDEN_DIR / "schema.json"

MODULES = [
    "chemical_equilibrium",
    "acid_base",
    "redox",
    "organic",
    "stoichiometry",
]


def validate_json(file_path: Path) -> list[str]:
    """校验单个 JSON 文件的基本结构。返回错误列表。"""
    errors = []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{file_path.name}: JSON 解析失败 — {e}"]

    # 检查 meta
    meta = data.get("meta", {})
    valid_module_names = {"chemical_equilibrium", "acid_base", "redox", "organic", "stoichiometry"}
    if meta.get("module", "") not in valid_module_names:
        errors.append(f"{file_path.name}: meta.module 无效 '{meta.get('module')}'")

    if meta.get("total", 0) != 20:
        errors.append(f"{file_path.name}: meta.total 应为 20，实际 {meta.get('total')}")

    # 检查 samples
    samples = data.get("samples", [])
    if len(samples) != 20:
        errors.append(f"{file_path.name}: 样本数应为 20，实际 {len(samples)}")

    # 逐条检查必填字段
    required_fields = ["id", "module", "category", "eval_type"]
    valid_modules = {"question_generation", "diagnosis", "tutoring"}
    valid_categories = {"化学平衡", "酸碱盐", "氧化还原", "有机化学", "化学计量"}

    for i, sample in enumerate(samples):
        for field in required_fields:
            if field not in sample:
                errors.append(f"{file_path.name}[{i}]: 缺少 {field}")
        if sample.get("module") not in valid_modules:
            errors.append(f"{file_path.name}[{i}]: 无效 module '{sample.get('module')}'")
        if sample.get("category") not in valid_categories:
            errors.append(f"{file_path.name}[{i}]: 无效 category '{sample.get('category')}'")
        if sample.get("eval_type") != "l3":
            errors.append(f"{file_path.name}[{i}]: eval_type 应为 'l3'")

    # 检查三类样本分布
    qg_count = sum(1 for s in samples if s.get("module") == "question_generation")
    diag_count = sum(1 for s in samples if s.get("module") == "diagnosis")
    tut_count = sum(1 for s in samples if s.get("module") == "tutoring")
    if qg_count != 8:
        errors.append(f"{file_path.name}: 出题样本 {qg_count}，期望 8")
    if diag_count != 8:
        errors.append(f"{file_path.name}: 诊断样本 {diag_count}，期望 8")
    if tut_count != 4:
        errors.append(f"{file_path.name}: 辅导样本 {tut_count}，期望 4")

    return errors


def create_db() -> sqlite3.Connection:
    """创建 SQLite 数据库和表结构。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS golden_samples (
            id TEXT PRIMARY KEY,
            module TEXT NOT NULL,
            category TEXT NOT NULL,
            sub_category TEXT,
            eval_type TEXT NOT NULL DEFAULT 'l3',
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS eval_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            total_samples INTEGER NOT NULL,
            passed INTEGER NOT NULL DEFAULT 0,
            failed INTEGER NOT NULL DEFAULT 0,
            pass_rate REAL NOT NULL DEFAULT 0.0,
            failed_ids TEXT DEFAULT '[]',
            notes TEXT DEFAULT ''
        )
    """)
    conn.commit()
    return conn


def seed_module(conn: sqlite3.Connection, module_name: str) -> int:
    """导入单个模块的 Golden 样本到数据库。幂等（INSERT OR REPLACE）。"""
    json_path = GOLDEN_DIR / f"{module_name}.json"
    if not json_path.exists():
        print(f"  ✗ 文件不存在: {json_path}")
        return 0

    data = json.loads(json_path.read_text(encoding="utf-8"))
    samples = data.get("samples", [])
    count = 0

    for sample in samples:
        conn.execute(
            """INSERT OR REPLACE INTO golden_samples
               (id, module, category, sub_category, eval_type, data_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                sample["id"],
                sample["module"],
                sample["category"],
                sample.get("sub_category", ""),
                sample.get("eval_type", "l3"),
                json.dumps(sample, ensure_ascii=False),
            ),
        )
        count += 1

    conn.commit()
    return count


def main():
    parser = argparse.ArgumentParser(description="ChemAI Golden 数据集种子脚本")
    parser.add_argument("--validate", action="store_true", help="仅校验 JSON 文件格式")
    parser.add_argument("--module", type=str, help="仅导入指定模块")
    args = parser.parse_args()

    # 校验模式
    if args.validate:
        print("校验 Golden 数据集 JSON 文件...\n")
        all_errors = []
        modules = [args.module] if args.module else MODULES
        for mod in modules:
            json_path = GOLDEN_DIR / f"{mod}.json"
            if not json_path.exists():
                print(f"  ✗ {mod}.json — 文件不存在")
                continue
            errors = validate_json(json_path)
            if errors:
                all_errors.extend(errors)
                for e in errors:
                    print(f"  ✗ {e}")
            else:
                print(f"  ✓ {mod}.json — 通过")
        if all_errors:
            print(f"\n✗ {len(all_errors)} 个错误")
            sys.exit(1)
        else:
            print("\n✓ 全部通过")
            sys.exit(0)

    # 导入模式
    print(f"Golden 数据集种子脚本 v0.5.0\n")
    conn = create_db()

    modules = [args.module] if args.module else MODULES
    total = 0
    for mod in modules:
        count = seed_module(conn, mod)
        print(f"  ✓ {mod}: {count} 条样本导入")
        total += count

    conn.close()
    print(f"\n✓ 总计 {total} 条样本导入到 {DB_PATH}")
    print(f"  数据库: {DB_PATH}")


if __name__ == "__main__":
    main()

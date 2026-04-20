#!/usr/bin/env python3
"""
Generate detailed Exp3 quality-speed balance artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper.experiments.exp3_parameter_sensitivity.exp3_balance_common import (
    DEFAULT_EXP3_RESULTS,
    EXP3_RESULTS_DIR,
    EXP3_TARGET_BUDGETS,
    OURS_NAME,
    REFERENCE_NAME,
    add_tradeoff_metrics,
    build_algorithm_summary,
    build_budget_summary,
    build_head_to_head_detail,
    build_query_level_frame,
    df_markdown,
    load_task_frame,
    present_algorithm_summary,
    present_budget_summary,
    summarize_tradeoff_by_budget,
    summarize_tradeoff_counts,
)


STATS_OUT_DEFAULT = EXP3_RESULTS_DIR / "exp3_analysis_stats.json"
MD_OUT_DEFAULT = EXP3_RESULTS_DIR / "exp3_full_text_analysis.md"


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    return json.loads(df.to_json(orient="records"))


def build_payload(metadata: dict[str, Any], task_df: pd.DataFrame) -> dict[str, Any]:
    task_df = add_tradeoff_metrics(task_df, group_cols=["origin_name", "depart_time", "budget_minutes", "score_seed"])
    query_df = build_query_level_frame(task_df)

    task_summary = build_algorithm_summary(task_df, count_label="task_count")
    query_summary = build_algorithm_summary(query_df, count_label="query_count")
    budget_summary = build_budget_summary(task_df, count_label="task_count")

    task_detail = build_head_to_head_detail(
        task_df,
        group_cols=["origin_name", "depart_time", "budget_minutes", "score_seed"],
    )
    query_detail = build_head_to_head_detail(
        query_df,
        group_cols=["origin_name", "depart_time", "budget_minutes"],
    )

    return {
        "metadata": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_results_file": metadata.get("source_exp1_results", ""),
            "source_objective_mode": metadata.get("source_objective_mode", ""),
            "selected_scope": metadata.get("selected_scope", {}),
            "target_budgets_minutes": metadata.get("target_budgets_minutes", list(EXP3_TARGET_BUDGETS)),
            "missing_target_budgets_minutes": metadata.get("missing_target_budgets_minutes", []),
            "task_rows": int(len(task_df)),
            "query_rows": int(len(query_df)),
        },
        "task_level": {
            "algorithm_summary": _records(task_summary),
            "budget_summary": _records(budget_summary),
            "ours_vs_nsga_detail": _records(task_detail),
            "ours_vs_nsga_tradeoff_summary": _records(summarize_tradeoff_counts(task_detail)),
            "ours_vs_nsga_tradeoff_by_budget": _records(summarize_tradeoff_by_budget(task_detail)),
        },
        "query_level": {
            "algorithm_summary": _records(query_summary),
            "ours_vs_nsga_detail": _records(query_detail),
            "ours_vs_nsga_tradeoff_summary": _records(summarize_tradeoff_counts(query_detail)),
            "ours_vs_nsga_tradeoff_by_budget": _records(summarize_tradeoff_by_budget(query_detail)),
        },
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Experiment 3 Balance Analysis (Supplement to Experiment 1)")
    lines.append("")
    lines.append(f"Generated at: {payload['metadata']['generated_at']}")
    lines.append("")
    lines.append("## 1. Positioning")
    lines.append("")
    lines.append(
        "Experiment 3 should be positioned as a supplementary balance analysis for Experiment 1. "
        "The goal is not to claim that Ours is best on every query, but to test whether it most often stays "
        "close to the score-time ideal point under the same task."
    )
    lines.append("")
    lines.append("## 2. Data Overview")
    lines.append("")
    lines.append(f"- Source results: `{payload['metadata']['source_results_file']}`")
    lines.append(f"- Objective mode: `{payload['metadata']['source_objective_mode']}`")
    lines.append(f"- Task-level rows: `{payload['metadata']['task_rows']}`")
    lines.append(f"- Query-level rows: `{payload['metadata']['query_rows']}`")
    scope = payload["metadata"].get("selected_scope", {})
    lines.append(f"- Origins: `{scope.get('origins', [])}`")
    lines.append(f"- Budgets (minutes): `{scope.get('budgets', [])}`")
    lines.append(f"- Target budgets (minutes): `{payload['metadata'].get('target_budgets_minutes', [])}`")
    if payload["metadata"].get("missing_target_budgets_minutes"):
        lines.append(f"- Missing target budgets in current Exp1 source: `{payload['metadata'].get('missing_target_budgets_minutes', [])}`")
    lines.append(f"- Score seeds: `{scope.get('score_seeds', [])}`")
    lines.append("")

    task_summary = present_algorithm_summary(pd.DataFrame(payload["task_level"]["algorithm_summary"]), count_label="task_count")
    query_summary = present_algorithm_summary(pd.DataFrame(payload["query_level"]["algorithm_summary"]), count_label="query_count")
    budget_summary = present_budget_summary(pd.DataFrame(payload["task_level"]["budget_summary"]), count_label="task_count")
    task_tradeoff = pd.DataFrame(payload["task_level"]["ours_vs_nsga_tradeoff_summary"])
    task_tradeoff_budget = pd.DataFrame(payload["task_level"]["ours_vs_nsga_tradeoff_by_budget"])
    query_tradeoff = pd.DataFrame(payload["query_level"]["ours_vs_nsga_tradeoff_summary"])

    lines.append("## 3. Overall Quality-Speed Balance")
    lines.append("")
    if not task_summary.empty:
        leader = task_summary.iloc[0]
        lines.append(
            f"- Task-level leader by balance summary: `{leader['algorithm']}` "
            f"(ideal-point distance `{leader['avg_ideal_distance']:.3f}`)."
        )
        best_query = query_summary.sort_values("avg_ideal_distance", ascending=True).iloc[0]
        lines.append(
            f"- Query-level closest to the ideal point: `{best_query['algorithm']}` "
            f"(distance `{best_query['avg_ideal_distance']:.3f}`)."
        )
    lines.append("")
    lines.append("### 3.1 Task-Level Summary")
    lines.append("")
    lines.append(df_markdown(task_summary))
    lines.append("")
    lines.append("### 3.2 Query-Level Summary")
    lines.append("")
    lines.append(df_markdown(query_summary))
    lines.append("")
    lines.append("### 3.3 Task-Level Summary by Budget")
    lines.append("")
    lines.append(df_markdown(budget_summary))
    lines.append("")

    lines.append(f"## 4. {OURS_NAME} vs {REFERENCE_NAME}")
    lines.append("")
    if not task_tradeoff.empty:
        high_fast = int(task_tradeoff.set_index("tradeoff_category").loc["higher score + faster", "count"])
        high_slow = int(task_tradeoff.set_index("tradeoff_category").loc["higher score + slower", "count"])
        low_fast = int(task_tradeoff.set_index("tradeoff_category").loc["lower score + faster", "count"])
        lines.append(
            f"- Task-level: `{OURS_NAME}` achieves `higher score + faster` on `{high_fast}` tasks, "
            f"`higher score + slower` on `{high_slow}` tasks, and `lower score + faster` on `{low_fast}` tasks."
        )
    lines.append("")
    lines.append("### 4.1 Task-Level Tradeoff Counts")
    lines.append("")
    lines.append(df_markdown(task_tradeoff))
    lines.append("")
    lines.append("### 4.2 Task-Level Tradeoff by Budget")
    lines.append("")
    lines.append(df_markdown(task_tradeoff_budget))
    lines.append("")
    lines.append("### 4.3 Query-Level Tradeoff Counts")
    lines.append("")
    lines.append(df_markdown(query_tradeoff))
    lines.append("")

    lines.append("## 5. Interpretation for Paper Writing")
    lines.append("")
    lines.append(
        "- The main claim should be that Ours provides the best overall quality-speed balance, "
        "not that it wins every single task."
    )
    lines.append(
        "- In the teacher-facing and paper-facing version, `ideal-point distance` should be the primary balance metric."
    )
    lines.append(
        "- The Ours-vs-NSGA-II tradeoff table should be used only as supplementary evidence for when Ours is simultaneously better and faster, "
        "and when it trades score for time or vice versa."
    )
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Exp3 quality-speed balance analysis artifacts.")
    parser.add_argument("--results", type=Path, default=DEFAULT_EXP3_RESULTS)
    parser.add_argument("--stats-out", type=Path, default=STATS_OUT_DEFAULT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT_DEFAULT)
    args = parser.parse_args()

    metadata, task_df = load_task_frame(args.results.resolve())
    payload = build_payload(metadata, task_df)
    markdown = build_markdown(payload)

    args.stats_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.stats_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.md_out.write_text(markdown, encoding="utf-8")

    print(f"[OK] stats json -> {args.stats_out}")
    print(f"[OK] markdown -> {args.md_out}")


if __name__ == "__main__":
    main()

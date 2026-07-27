#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper.experiments.exp4_route_visualization.exp4_common import (
    EXP4_ANALYSIS_MD_PATH,
    EXP4_CASES_PATH,
    load_manifest,
)


def _artifact_map(case: dict) -> dict[str, dict]:
    return {str(artifact.get("algorithm_key", "")): artifact for artifact in case.get("artifacts", [])}


def _artifact_metrics(artifact: dict) -> dict[str, float]:
    summary = artifact.get("summary_metrics", {})
    score = float(summary.get("stop_score_total", 0.0))
    stops = float(summary.get("scored_stop_count", 0.0))
    return {
        "score": score,
        "time": float(artifact.get("elapsed_ms", 0.0)),
        "stops": stops,
        "reward_per_stop": score / stops if stops > 0.0 else 0.0,
    }


def _algorithm_name(artifact: dict) -> str:
    return str(artifact.get("algorithm_name", artifact.get("algorithm_key", "comparison method")))


def _stop_difference_phrase(value: float) -> str:
    if value > 0:
        return f"{abs(value):.0f} more"
    if value < 0:
        return f"{abs(value):.0f} fewer"
    return "the same number of"


def build_case_commentary(case: dict) -> str:
    artifacts = _artifact_map(case)
    ours = artifacts.get("ours")
    if ours is None or len(artifacts) < 2:
        return "Selected algorithms were not fully generated for this case."

    ours_metrics = _artifact_metrics(ours)
    comparisons = [artifact for key, artifact in artifacts.items() if key != "ours"]

    if str(case.get("paper_role", "")) == "success_case":
        reference = artifacts.get("nsga2", max(comparisons, key=lambda item: _artifact_metrics(item)["score"]))
        reference_metrics = _artifact_metrics(reference)
        stop_gap = ours_metrics["stops"] - reference_metrics["stops"]
        density_gap = ours_metrics["reward_per_stop"] - reference_metrics["reward_per_stop"]
        return (
            f"Ours wins this regenerated example on both axes: stop score {ours_metrics['score']:.1f} vs "
            f"{reference_metrics['score']:.1f} for {_algorithm_name(reference)}, and generation time "
            f"{ours_metrics['time']:.1f} ms vs {reference_metrics['time']:.1f} ms. The route-level reason is "
            f"mainly coverage: Ours collects {ours_metrics['stops']:.0f} scored stops vs "
            f"{reference_metrics['stops']:.0f} (difference {stop_gap:+.0f}), while reward per scored stop differs "
            f"by only {density_gap:+.1f}. This is consistent with the aggregate coverage association, although one "
            f"case is illustrative rather than causal."
        )
    if str(case.get("paper_role", "")) == "balance_case":
        top_score = max(comparisons, key=lambda item: _artifact_metrics(item)["score"])
        fastest = min(comparisons, key=lambda item: _artifact_metrics(item)["time"])
        top_metrics = _artifact_metrics(top_score)
        fast_metrics = _artifact_metrics(fastest)
        score_retention = 100.0 * ours_metrics["score"] / max(top_metrics["score"], 1e-9)
        speedup_vs_top = top_metrics["time"] / max(ours_metrics["time"], 1e-9)
        score_gain_vs_fast = ours_metrics["score"] - fast_metrics["score"]
        return (
            f"This is the intended balance example. Ours retains {score_retention:.2f}% of the score achieved by "
            f"{_algorithm_name(top_score)} ({ours_metrics['score']:.1f} vs {top_metrics['score']:.1f}) while running "
            f"{speedup_vs_top:.1f} times faster ({ours_metrics['time']:.1f} vs {top_metrics['time']:.1f} ms). "
            f"Relative to the fastest lower-quality comparator, {_algorithm_name(fastest)}, Ours gains "
            f"{score_gain_vs_fast:.1f} points at a higher runtime. Its ideal-point rank follows from occupying the "
            f"middle of these two extremes, not from being best on either raw axis."
        )
    nsga2 = artifacts.get("nsga2", max(comparisons, key=lambda item: _artifact_metrics(item)["score"]))
    nsga_metrics = _artifact_metrics(nsga2)
    stop_gap = nsga_metrics["stops"] - ours_metrics["stops"]
    density_gap = nsga_metrics["reward_per_stop"] - ours_metrics["reward_per_stop"]
    return (
        f"This case is an explicit counterexample. {_algorithm_name(nsga2)} achieves the higher stop score "
        f"({nsga_metrics['score']:.1f} vs {ours_metrics['score']:.1f}) but takes "
        f"{nsga_metrics['time']:.1f} ms vs {ours_metrics['time']:.1f} ms. It collects "
        f"{_stop_difference_phrase(stop_gap)} scored stops than Ours and has a reward-per-stop difference of "
        f"{density_gap:+.1f}; here the higher reward density outweighs the stop-count difference and explains the "
        f"observed score reversal. The result shows "
        f"that width-controlled search can miss a better long-budget itinerary and rules out a universal-win claim."
    )


def build_markdown(manifest: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = []
    lines.append("# Experiment 4 Full Text Analysis")
    lines.append("")
    lines.append(f"Generated at: {now}")
    lines.append("")
    lines.append("## 1. Positioning")
    lines.append("")
    lines.append(
        "Experiment 4 is a qualitative case study for the same main task used in Experiments 1 and 3: "
        "maximize stop score under a fixed time budget, while also discussing generation time."
    )
    lines.append("")
    lines.append(
        "The purpose is not to add another benchmark, but to visually explain three concrete situations: "
        "a clear Ours win, a quality-speed balance case, and an honest counterexample."
    )
    lines.append("")
    lines.append("## 2. Selected Cases")
    lines.append("")
    for case in manifest.get("cases", []):
        depart_time = int(case["depart_time"])
        lines.append(f"### {case['title']}")
        lines.append("")
        lines.append(f"- Role: `{case['paper_role']}` / `{case['paper_group']}`")
        lines.append(f"- Source: `{case['source_exp']}` / `{case['scenario']}`")
        lines.append(
            f"- Query: `{case['origin_name']}`, `{depart_time // 60:02d}:{depart_time % 60:02d}`, "
            f"`{int(case['budget_minutes']) // 60}h`, `score_seed={case['score_seed']}`, `seed={case['seed']}`"
        )
        lines.append(f"- Selection rule: {case['selection_reason']}")
        lines.append(f"- Intended focus: {case['qualitative_focus']}")
        panel_path = str(case.get("panel_path", "")).strip()
        if panel_path:
            lines.append(f"- Figure panel: `{panel_path}`")
        evidence = case.get("selection_evidence") or {}
        if evidence:
            lines.append(f"- Selection evidence: `{evidence}`")
        lines.append("")
        lines.append(
            "| Algorithm | Stop Score | Gen Time (ms) | Score/h | Effective Time (min) "
            "| Scored Stops | Reward/Stop | Feasible |"
        )
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
        for artifact in case.get("artifacts", []):
            sm = artifact["summary_metrics"]
            score = float(sm["stop_score_total"])
            scored_stops = float(sm["scored_stop_count"])
            reward_per_stop = score / scored_stops if scored_stops > 0.0 else 0.0
            lines.append(
                f"| {artifact['algorithm_name']} | {score:.1f} "
                f"| {float(artifact['elapsed_ms']):.1f} | {float(sm['score_per_hour']):.1f} "
                f"| {float(sm['effective_time_minutes']):.1f} | {scored_stops:.0f} "
                f"| {reward_per_stop:.1f} | {artifact['feasible']} |"
            )
        lines.append("")
        lines.append(build_case_commentary(case))
        lines.append("")
    lines.append("## 3. Usage in the Paper")
    lines.append("")
    lines.append(
        "The main text can use the success case and the balance case together. "
        "The counterexample should be kept as an appendix or limitation figure so the paper explicitly avoids claiming that Ours wins every query."
    )
    lines.append("")
    lines.append(
        "The recommended narrative is: Ours provides the best overall balance between route quality and generation time, "
        "not universal dominance on every instance."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Experiment 4 markdown analysis.")
    parser.add_argument("--manifest", type=Path, default=EXP4_CASES_PATH, help="Path to exp4_cases.json")
    parser.add_argument("--out", type=Path, default=EXP4_ANALYSIS_MD_PATH, help="Output markdown path")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    markdown = build_markdown(manifest)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"Saved Exp4 analysis markdown: {args.out}")


if __name__ == "__main__":
    main()

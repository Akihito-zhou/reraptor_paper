"""Checks for the numerical claims displayed in the manuscript.

Run from the repository root:
    python -m paper.experiments.verify_manuscript_claims

The proprietary timetable snapshot is optional in the public companion. Its
released provenance record is always checked; when an authorized local copy is
present, its checksum and inventory are checked as well.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def close(actual: float, expected: float, *, tol: float = 5e-4) -> None:
    if not math.isclose(float(actual), float(expected), abs_tol=tol, rel_tol=0.0):
        raise AssertionError(f"expected {expected}, found {actual}")


def rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def mean(values: list[float]) -> float:
    if not values:
        raise AssertionError("cannot average an empty collection")
    return sum(values) / len(values)


def check_timetable() -> None:
    provenance_path = ROOT / "paper/results/timetable_provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    expected = "319d443ac097f8964f8774d38fc63c6c8f7ef90e505eb167ffd38bc317727c82"
    inventory = provenance["inventory"]
    if provenance["service_date"] != "20251224":
        raise AssertionError("released timetable service date mismatch")
    if provenance["sha256"] != expected:
        raise AssertionError("released timetable checksum metadata mismatch")
    if (
        inventory["scheduled_segments"],
        inventory["unique_stops"],
        inventory["unique_lines"],
    ) != (304_344, 1032, 302):
        raise AssertionError("released timetable inventory metadata mismatch")

    path = ROOT / "apps/api/data/timetables/segments_fukuoka_20251224.csv"
    if not path.exists():
        print("INFO proprietary timetable absent; verified released provenance metadata")
        return

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise AssertionError(f"timetable checksum mismatch: {digest}")
    with path.open(encoding="utf-8", newline="") as handle:
        timetable = list(csv.DictReader(handle))
    if len(timetable) != 304_344:
        raise AssertionError(f"expected 304344 timetable segments, found {len(timetable)}")
    stops = {row[key] for row in timetable for key in ("from_stop", "to_stop")}
    lines = {row["line_id"] for row in timetable}
    dates = {row["service_date"] for row in timetable}
    if (len(stops), len(lines), dates) != (1032, 302, {"20251224"}):
        raise AssertionError("timetable stop/line/service-date inventory mismatch")


def check_experiment_1() -> None:
    path = ROOT / (
        "paper/results/exp1_algorithm_comparison/"
        "exp1_results_canonical_final_10alg_manuscript_20260723.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    data = payload["results"]
    ours = [row for row in data if row["algorithm"] == "Ours (Full)"]
    nsga = [row for row in data if row["algorithm"] == "NSGA-II"]
    if (len(ours), len(nsga)) != (600, 3000):
        raise AssertionError("Experiment 1 run counts do not match 600 tasks")
    close(mean([row["stop_score_total"] for row in ours]), 872.438333333333)
    close(mean([row["stop_score_total"] for row in nsga]), 802.539333333333)
    close(mean([row["elapsed_ms"] for row in ours]), 5171.180633333333, tol=5e-3)
    close(mean([row["elapsed_ms"] for row in nsga]), 35634.7814, tol=5e-3)
    positive_feasible = sum(
        bool(row["feasible"]) and float(row["stop_score_total"]) > 0 for row in ours
    )
    if positive_feasible != 600:
        raise AssertionError(f"expected 600 positive feasible ReRAPTOR tasks, found {positive_feasible}")

    interpretation = rows(
        "paper/results/exp1_algorithm_comparison/score_interpretability_summary_20260723.csv"
    )
    lookup = {(r["estimand"], r["column"]): r for r in interpretation}
    close(float(lookup[("all_task_failure_zero", "score_gap")]["mean"]), 69.899)
    close(float(lookup[("all_task_failure_zero", "scored_stop_gap")]["mean"]), 1.32)
    close(
        float(lookup[("all_task_failure_zero", "reward_per_scored_stop_gap")]["mean"]),
        -1.913661845486513,
    )


def check_experiment_2() -> None:
    summary = {row["algorithm"]: row for row in rows(
        "paper/results/exp2_ablation_study/exp2_canonical_summary_20260725.csv"
    )}
    close(float(summary["Ours (Full)"]["stop_score"]), 872.438333333333)
    close(float(summary["Ours (NoDom)"]["stop_score"]), 787.458333333333)
    close(float(summary["Ours (NoBeam)"]["cap_hit_rate"]), 0.676666666666667)
    paired = {row["algorithm"]: row for row in rows(
        "paper/results/exp2_ablation_study/exp2_canonical_paired_vs_full_20260725.csv"
    )}
    noneg = paired["Ours (NoNeg)"]
    if (noneg["wins_vs_full"], noneg["ties_vs_full"], noneg["losses_vs_full"]) != (
        "6", "594", "0"
    ):
        raise AssertionError("NoNeg win/tie/loss counts do not match 6/594/0")


def check_experiment_3() -> None:
    paired = {row["config_id"]: row for row in rows(
        "paper/results/exp3_parameter_sensitivity/"
        "sensitivity_canonical_paired_vs_default_20260727.csv"
    )}
    for config_id in ("w25", "w100", "w200"):
        if paired[config_id]["ties_vs_default"] != "600":
            raise AssertionError(f"{config_id} does not tie the default on all tasks")
    w10 = paired["w10"]
    if (w10["wins_vs_default"], w10["ties_vs_default"]) != ("0", "592"):
        raise AssertionError("W=10 should differ on exactly eight tasks")
    close(float(w10["mean_score_delta_vs_default"]), -0.3133333333)


def check_experiment_4() -> None:
    path = ROOT / "paper/results/exp4_route_visualization/exp4_cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    if [case["id"] for case in cases] != [
        "case_a_clear_score_lead",
        "case_b_quality_speed_balance",
        "case_c_contrastive_counterexample",
    ]:
        raise AssertionError("route-case selection differs from the manuscript")
    expected = {
        "case_a_clear_score_lead": {"ours": 1455.0, "nsga2": 684.0},
        "case_b_quality_speed_balance": {"ours": 375.0, "pure_raptor": 376.0},
        "case_c_contrastive_counterexample": {"ours": 1479.0, "nsga2": 1680.0},
    }
    for case in cases:
        found = {a["algorithm_key"]: a["primary_metric_value"] for a in case["artifacts"]}
        for algorithm, score in expected[case["id"]].items():
            close(float(found[algorithm]), score)


def main() -> None:
    checks = [
        check_timetable,
        check_experiment_1,
        check_experiment_2,
        check_experiment_3,
        check_experiment_4,
    ]
    for check in checks:
        check()
        print(f"PASS {check.__name__}")
    print("PASS all manuscript claim checks")


if __name__ == "__main__":
    main()

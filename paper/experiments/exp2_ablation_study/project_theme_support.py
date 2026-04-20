from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Any, Callable


FULLWIDTH_DIGIT_TRANS = str.maketrans("\uff10\uff11\uff12\uff13\uff14\uff15\uff16\uff17\uff18\uff19", "0123456789")


@dataclass(frozen=True)
class ProjectThemeChallenge:
    challenge_id: str
    scoring_type: str
    theme_mode: str
    target: int
    min_minutes: int
    min_legs: int
    valid_stop_ids: frozenset[str]
    valid_route_ids: frozenset[str]


PROJECT_THEME_DEFS: tuple[dict[str, Any], ...] = (
    {"challenge_id": "odd-bus-tour", "scoring_type": "theme_route_id_odd", "theme_mode": "route", "target": 8, "min_minutes": 60, "min_legs": 5},
    {"challenge_id": "single-digit", "scoring_type": "theme_route_single_digit", "theme_mode": "route", "target": 6, "min_minutes": 60, "min_legs": 4},
    {"challenge_id": "century-ride", "scoring_type": "theme_route_triple_digit", "theme_mode": "route", "target": 10, "min_minutes": 90, "min_legs": 6},
    {"challenge_id": "random-subset", "scoring_type": "theme_random_subset", "theme_mode": "route", "target": 8, "min_minutes": 60, "min_legs": 5},
    {"challenge_id": "rapid-transit", "scoring_type": "theme_route_rapid", "theme_mode": "route", "target": 5, "min_minutes": 45, "min_legs": 3},
    {"challenge_id": "seaside-cruise", "scoring_type": "theme_stop_seaside", "theme_mode": "stop", "target": 5, "min_minutes": 45, "min_legs": 3},
    {"challenge_id": "mountain-climber", "scoring_type": "theme_stop_mountain", "theme_mode": "stop", "target": 5, "min_minutes": 45, "min_legs": 3},
    {"challenge_id": "university-link", "scoring_type": "theme_stop_university", "theme_mode": "stop", "target": 4, "min_minutes": 45, "min_legs": 3},
    {"challenge_id": "transfer-hub-hopper", "scoring_type": "theme_stop_station", "theme_mode": "stop", "target": 10, "min_minutes": 90, "min_legs": 6},
    {"challenge_id": "hospital-loop", "scoring_type": "theme_stop_hospital", "theme_mode": "stop", "target": 4, "min_minutes": 45, "min_legs": 3},
)


STOP_THEME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "theme_stop_seaside": ("\u6d77", "\u6d5c", "\u6e2f", "\u6e7e", "\u30de\u30ea\u30f3", "\u30d9\u30a4"),
    "theme_stop_mountain": ("\u5c71", "\u4e18", "\u53f0", "\u5cb3", "\u5ddd", "\u5742"),
    "theme_stop_university": ("\u5927\u5b66", "\u5b66\u5712", "\u30ad\u30e3\u30f3\u30d1\u30b9", "\u4e5d\u5927", "\u798f\u5927"),
    "theme_stop_station": ("\u99c5", "Station", "\u30b9\u30c6\u30fc\u30b7\u30e7\u30f3"),
    "theme_stop_hospital": ("\u75c5\u9662", "\u533b\u7642", "\u30af\u30ea\u30cb\u30c3\u30af"),
}


def _normalized_route_name(name: str) -> str:
    return str(name or "").translate(FULLWIDTH_DIGIT_TRANS)


def parse_route_number(name: str) -> int | None:
    normalized = _normalized_route_name(name)
    for part in normalized.split("\u30fb"):
        token = str(part).strip()
        if not token:
            continue
        main = token.split("-")[0]
        if main.isdigit():
            return int(main)
    match = re.search(r"\b(\d{1,3})(?:-\d+)?\b", normalized)
    if not match:
        return None
    return int(match.group(1))


def _valid_route_ids_for_scoring_type(planner: Any, scoring_type: str) -> frozenset[str]:
    valid: set[str] = set()
    for route_id, line_name in getattr(planner, "line_names", {}).items():
        safe_id = str(route_id)
        safe_name = str(line_name or "")
        number = parse_route_number(safe_name)
        if scoring_type == "theme_route_id_odd":
            if number is not None and number % 2 == 1:
                valid.add(safe_id)
        elif scoring_type == "theme_route_single_digit":
            if number is not None and 1 <= number <= 9:
                valid.add(safe_id)
        elif scoring_type == "theme_route_triple_digit":
            if number is not None and number >= 100:
                valid.add(safe_id)
        elif scoring_type == "theme_route_rapid":
            if any(token in safe_name for token in ("\u5feb\u901f", "\u6025\u884c", "\u7279\u6025", "Rapid", "K", "L")):
                valid.add(safe_id)
    if scoring_type == "theme_random_subset":
        route_ids = sorted(str(route_id) for route_id in getattr(planner, "line_names", {}))
        if route_ids:
            rng = random.Random(20260411)
            subset_size = min(50, len(route_ids))
            valid = set(rng.sample(route_ids, subset_size))
    return frozenset(valid)


def _valid_stop_ids_for_scoring_type(planner: Any, scoring_type: str) -> frozenset[str]:
    keywords = STOP_THEME_KEYWORDS.get(str(scoring_type), ())
    valid: set[str] = set()
    for stop_id, station in getattr(planner, "stations", {}).items():
        name = str(getattr(station, "name", "") or "")
        if any(token in name for token in keywords):
            if scoring_type == "theme_stop_station" and "\u524d" in name:
                continue
            valid.add(str(stop_id))
    return frozenset(valid)


def build_project_theme_challenges(planner: Any, *, quick: bool) -> list[ProjectThemeChallenge]:
    defs = PROJECT_THEME_DEFS[:4] if quick else PROJECT_THEME_DEFS
    challenges: list[ProjectThemeChallenge] = []
    for item in defs:
        scoring_type = str(item["scoring_type"])
        theme_mode = str(item["theme_mode"])
        valid_route_ids = _valid_route_ids_for_scoring_type(planner, scoring_type) if theme_mode == "route" else frozenset()
        valid_stop_ids = _valid_stop_ids_for_scoring_type(planner, scoring_type) if theme_mode == "stop" else frozenset()
        if theme_mode == "route" and not valid_route_ids:
            continue
        if theme_mode == "stop" and not valid_stop_ids:
            continue
        challenges.append(
            ProjectThemeChallenge(
                challenge_id=str(item["challenge_id"]),
                scoring_type=scoring_type,
                theme_mode=theme_mode,
                target=int(item["target"]),
                min_minutes=int(item["min_minutes"]),
                min_legs=int(item["min_legs"]),
                valid_stop_ids=valid_stop_ids,
                valid_route_ids=valid_route_ids,
            )
        )
    return challenges


def sample_project_theme_starts(
    planner: Any,
    challenge: ProjectThemeChallenge,
    *,
    seed: int,
    max_starts: int,
) -> list[tuple[str, str]]:
    rng = random.Random(int(seed))
    if challenge.theme_mode == "stop":
        candidates = sorted(challenge.valid_stop_ids)
        rng.shuffle(candidates)
        return [(code, "theme_stop_start") for code in candidates[: max(1, min(max_starts, len(candidates)))]]

    pure: list[tuple[str, int]] = []
    mixed: list[tuple[str, int]] = []
    valid_routes = set(challenge.valid_route_ids)
    for stop_id, route_ids in getattr(planner, "routes_by_stop", {}).items():
        base_route_ids = {str(route_id).split(":")[0] for route_id in route_ids}
        valid_count = len(base_route_ids & valid_routes)
        if valid_count <= 0:
            continue
        if base_route_ids.issubset(valid_routes):
            pure.append((str(stop_id), valid_count))
        else:
            mixed.append((str(stop_id), valid_count))

    source = mixed if mixed else pure
    start_mode = "mixed_route_start" if mixed else "pure_route_start"
    source.sort(key=lambda item: (-int(item[1]), item[0]))
    candidates = [code for code, _count in source]
    rng.shuffle(candidates)
    trimmed = candidates[: max(1, min(max_starts, len(candidates)))]
    if trimmed:
        return [(code, start_mode) for code in trimmed]

    fallback = [str(code) for code in getattr(planner, "hakata_stops", []) if str(code) in getattr(planner, "routes_by_stop", {})]
    return [(code, "fallback_hakata_start") for code in fallback[: max(1, min(max_starts, len(fallback)))]]


def project_theme_effective_requirements(challenge: ProjectThemeChallenge) -> tuple[int, int]:
    if challenge.theme_mode == "route":
        return max(30, int(challenge.min_minutes) // 2), max(2, int(challenge.min_legs) // 2)
    return int(challenge.min_minutes), int(challenge.min_legs)


def make_project_theme_score_fn(
    planner: Any,
    challenge: ProjectThemeChallenge,
    *,
    include_negative: bool,
) -> Callable[[Any, dict[str, Any]], float]:
    def scoring_fn(label: Any, _metrics: dict[str, Any]) -> float:
        base = float(getattr(label, "ride_minutes", 0.0) or 0.0) * 1000.0
        if challenge.theme_mode == "stop":
            theme_hits = sum(1 for stop_id in getattr(label, "visited", ()) if str(stop_id) in challenge.valid_stop_ids)
            return base + float(theme_hits) * 50000.0

        penalty = 0.0
        unique_main: set[str] = set()
        for leg in getattr(label, "legs", ()):
            line_id = str(getattr(leg, "line_id", "") or "")
            base_id = line_id.split(":")[0]
            if base_id.lower() in {"walk", "transfer", "walking"}:
                continue
            if include_negative and base_id not in challenge.valid_route_ids:
                penalty -= 10000000.0
            line_name = str(getattr(planner, "line_names", {}).get(line_id, getattr(planner, "line_names", {}).get(base_id, "")) or "")
            number = parse_route_number(line_name)
            unique_main.add(str(number) if number is not None else base_id)

        diversity_bonus = float(len(unique_main)) * 50000.0
        return base + diversity_bonus + penalty

    return scoring_fn


def make_project_theme_accept_fn(
    challenge: ProjectThemeChallenge,
    *,
    include_negative: bool,
) -> Callable[[Any, dict[str, Any]], bool]:
    def accept_fn(label: Any, _metrics: dict[str, Any]) -> bool:
        ride_minutes = int(getattr(label, "ride_minutes", 0) or 0)
        leg_count = len(getattr(label, "legs", ()) or ())
        effective_min_minutes, effective_min_legs = project_theme_effective_requirements(challenge)
        if ride_minutes < effective_min_minutes or leg_count < effective_min_legs:
            return False

        if challenge.theme_mode == "stop":
            return True

        total_legs = 0
        valid_legs = 0
        for leg in getattr(label, "legs", ()):
            base_id = str(getattr(leg, "line_id", "") or "").split(":")[0]
            if base_id.lower() in {"walk", "transfer", "walking"}:
                continue
            total_legs += 1
            if base_id in challenge.valid_route_ids:
                valid_legs += 1
        if total_legs <= 0:
            return False
        valid_ratio = float(valid_legs) / float(total_legs)
        return valid_ratio >= 0.9

    return accept_fn


def make_project_theme_dominance_fn() -> Callable[[Any, dict[str, Any], Any, dict[str, Any]], bool]:
    def dominance_fn(a: Any, _ma: dict[str, Any], b: Any, _mb: dict[str, Any]) -> bool:
        return float(getattr(a, "score", 0.0) or 0.0) >= float(getattr(b, "score", 0.0) or 0.0) and float(
            getattr(a, "ride_minutes", 0.0) or 0.0
        ) >= float(getattr(b, "ride_minutes", 0.0) or 0.0) * 0.9

    return dominance_fn


def evaluate_project_theme_route(
    *,
    path_edges: list[Any],
    challenge: ProjectThemeChallenge,
    planner: Any,
    start_mode: str,
) -> dict[str, Any]:
    unique_stops: list[str] = []
    seen_stops: set[str] = set()
    valid_leg_count = 0
    total_legs = 0
    for edge in path_edges:
        to_code = str(getattr(edge, "to_code", "") or "")
        if to_code and to_code not in seen_stops:
            seen_stops.add(to_code)
            unique_stops.append(to_code)
        line_id = str(getattr(edge, "line_id", "") or "")
        base_id = line_id.split(":")[0]
        if base_id.lower() in {"walk", "transfer", "walking"}:
            continue
        total_legs += 1
        if challenge.theme_mode == "route" and base_id in challenge.valid_route_ids:
            valid_leg_count += 1

    ride_minutes = float(max(0, int(path_edges[-1].arrive) - int(path_edges[0].depart))) if path_edges else 0.0
    unique_stop_count = len(unique_stops)
    effective_min_minutes, effective_min_legs = project_theme_effective_requirements(challenge)
    if challenge.theme_mode == "stop":
        theme_hits = sum(1 for code in unique_stops if code in challenge.valid_stop_ids)
        theme_ratio = float(theme_hits) / float(unique_stop_count) if unique_stop_count > 0 else 0.0
        theme_satisfied = bool(
            ride_minutes >= float(effective_min_minutes)
            and total_legs >= int(effective_min_legs)
            and theme_hits > 0
        )
        return {
            "theme_kind": "stop",
            "project_scoring_type": challenge.scoring_type,
            "project_target": int(challenge.target),
            "start_mode": str(start_mode),
            "theme_target_size": int(len(challenge.valid_stop_ids)),
            "theme_stop_count": int(theme_hits),
            "theme_leg_count": 0,
            "theme_hit_ratio": round(theme_ratio, 6),
            "theme_score_total": float(theme_hits),
            "theme_score_share": round(theme_ratio, 6),
            "off_theme_stop_count": int(max(0, unique_stop_count - theme_hits)),
            "off_theme_leg_count": 0,
            "off_theme_score_share": round(max(0.0, 1.0 - theme_ratio), 6),
            "theme_satisfied": bool(theme_satisfied),
            "primary_objective_total": round(ride_minutes, 6),
            "primary_objective_name": "ride_minutes",
            "score_per_hour": round((float(theme_hits) * 60.0 / ride_minutes) if ride_minutes > 0 else 0.0, 6),
            "target_density": round(float(len(challenge.valid_stop_ids)) / max(1.0, float(len(getattr(planner, "stations", {}) or {}))), 6),
            "effective_min_minutes": int(effective_min_minutes),
            "effective_min_legs": int(effective_min_legs),
        }

    valid_ratio = float(valid_leg_count) / float(total_legs) if total_legs > 0 else 0.0
    theme_satisfied = bool(
        ride_minutes >= float(effective_min_minutes)
        and total_legs >= int(effective_min_legs)
        and valid_ratio >= 0.9
    )
    return {
        "theme_kind": "route",
        "project_scoring_type": challenge.scoring_type,
        "project_target": int(challenge.target),
        "start_mode": str(start_mode),
        "theme_target_size": int(len(challenge.valid_route_ids)),
        "theme_stop_count": 0,
        "theme_leg_count": int(valid_leg_count),
        "theme_hit_ratio": round(valid_ratio, 6),
        "theme_score_total": float(valid_leg_count),
        "theme_score_share": round(valid_ratio, 6),
        "off_theme_stop_count": 0,
        "off_theme_leg_count": int(max(0, total_legs - valid_leg_count)),
        "off_theme_score_share": round(max(0.0, 1.0 - valid_ratio), 6),
        "theme_satisfied": bool(theme_satisfied),
        "primary_objective_total": round(ride_minutes, 6),
        "primary_objective_name": "ride_minutes",
        "score_per_hour": round((float(valid_leg_count) * 60.0 / ride_minutes) if ride_minutes > 0 else 0.0, 6),
        "target_density": round(float(len(challenge.valid_route_ids)) / max(1.0, float(len(getattr(planner, "line_names", {}) or {}))), 6),
        "effective_min_minutes": int(effective_min_minutes),
        "effective_min_legs": int(effective_min_legs),
    }

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import requests
from dotenv import load_dotenv  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
APP_API_DIR = PROJECT_ROOT / "apps" / "api"
if str(APP_API_DIR) not in sys.path:
    sys.path.insert(0, str(APP_API_DIR))

from paper.experiments.exp4_route_visualization.exp4_common import (
    EXP4_APPENDIX_PANEL_PATH,
    EXP4_CASES_PATH,
    EXP4_FIGURES_DIR,
    EXP4_MAIN_PANEL_PATH,
    EXP4_SUMMARY_MD_PATH,
    load_manifest,
    save_json,
)
GEOJSON_PATH = PROJECT_ROOT / "apps" / "api" / "data" / "base" / "fukuoka_city.geojson"
ROUTE_COLORS = ["#0b6e4f", "#ea7317", "#2b59c3", "#c3423f", "#8f2d56", "#3c6e71"]


def _get_ekispert_api_base_url() -> str:
    return os.getenv("PAPER_EKISPERT_API_BASE_URL", "https://api.ekispert.jp")


class PaperEkispertShapeFetcher:
    def __init__(self, api_key: str, *, base_url: str, timeout: float = 20.0) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._cache: dict[tuple[str, str, str], list[dict[str, float]]] = {}

    def fetch_leg_shape(
        self,
        from_code: str,
        to_code: str,
        departure: str | None = None,
    ) -> list[dict[str, float]]:
        cache_key = (from_code, to_code, departure or "")
        if cache_key in self._cache:
            return self._cache[cache_key]

        params: dict[str, str] = {
            "key": self._api_key,
            "viaList": f"{from_code}:{to_code}",
            "searchType": "departure",
            "addStop": "true",
        }
        if departure:
            params["time"] = departure.replace(":", "")

        try:
            resp = self._session.get(
                f"{self._base_url}/v1/json/search/course/extreme",
                params=params,
                timeout=self._timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, ValueError):
            self._cache[cache_key] = []
            return []

        course = payload.get("ResultSet", {}).get("Course")
        if isinstance(course, list):
            course = course[0]
        serialize_data = (course or {}).get("SerializeData") or (course or {}).get("serializeData")
        if not serialize_data:
            self._cache[cache_key] = []
            return []

        try:
            shape_resp = self._session.get(
                f"{self._base_url}/v1/json/course/shape",
                params={
                    "key": self._api_key,
                    "serializeData": serialize_data,
                    "type": "all",
                },
                timeout=self._timeout,
            )
            shape_resp.raise_for_status()
            shape_payload = shape_resp.json()
        except (requests.RequestException, ValueError):
            self._cache[cache_key] = []
            return []

        coords = self._extract_shape_coords(shape_payload)
        self._cache[cache_key] = coords
        return coords

    @staticmethod
    def _extract_shape_coords(payload: dict[str, Any]) -> list[dict[str, float]]:
        result = payload.get("ResultSet", {}) if isinstance(payload, dict) else {}
        course = result.get("Course", {}) if isinstance(result, dict) else {}
        patterns = course.get("OperationLinePattern") or []
        if isinstance(patterns, dict):
            patterns = [patterns]

        coords: list[dict[str, float]] = []
        for pattern in patterns:
            lines = pattern.get("Line") or []
            if isinstance(lines, dict):
                lines = [lines]
            for line in lines:
                shapes = line.get("Shape") or []
                if isinstance(shapes, dict):
                    shapes = [shapes]
                for shape in shapes:
                    geo = shape.get("GeoPoint") or {}
                    lat = geo.get("lati_d")
                    lon = geo.get("longi_d")
                    if lat is None or lon is None:
                        continue
                    try:
                        point = {"lat": float(lat), "lon": float(lon)}
                    except (TypeError, ValueError):
                        continue
                    if not coords or coords[-1] != point:
                        coords.append(point)
        return coords


def parse_csv_tokens(raw: str) -> list[str]:
    return [x.strip() for x in str(raw).split(",") if x.strip()]


def _load_geojson_segments() -> list[list[tuple[float, float]]]:
    if not GEOJSON_PATH.exists():
        return []
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    segments: list[list[tuple[float, float]]] = []
    for feature in payload.get("features", []):
        geometry = feature.get("geometry") or {}
        gtype = geometry.get("type")
        coords = geometry.get("coordinates") or []
        if gtype == "Polygon":
            for ring in coords:
                segments.append([(float(lon), float(lat)) for lon, lat in ring])
        elif gtype == "MultiPolygon":
            for polygon in coords:
                for ring in polygon:
                    segments.append([(float(lon), float(lat)) for lon, lat in ring])
    return segments


CITY_SEGMENTS = _load_geojson_segments()


def load_route_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_project_path(raw: str) -> Path:
    path = Path(str(raw).strip())
    if path.exists():
        return path
    parts = path.parts
    if "paper" in parts:
        idx = parts.index("paper")
        candidate = PROJECT_ROOT.joinpath(*parts[idx:])
        if candidate.exists():
            return candidate
    if "apps" in parts:
        idx = parts.index("apps")
        candidate = PROJECT_ROOT.joinpath(*parts[idx:])
        if candidate.exists():
            return candidate
    return path


def _resolve_leg_coords(
    leg: dict,
    fetcher: PaperEkispertShapeFetcher | None,
) -> tuple[list[tuple[float, float]], bool]:
    if fetcher is not None and leg.get("from_code") and leg.get("to_code"):
        fetched = fetcher.fetch_leg_shape(
            str(leg.get("from_code")),
            str(leg.get("to_code")),
            str(leg.get("departure", "")) or None,
        )
        if fetched:
            coords = [(float(pt["lon"]), float(pt["lat"])) for pt in fetched]
            if coords:
                return coords, True

    path_points = leg.get("path") or []
    if path_points:
        return [(float(pt["lon"]), float(pt["lat"])) for pt in path_points], False

    geometry = leg.get("geometry") or {}
    return [(float(lon), float(lat)) for lon, lat in geometry.get("coordinates", [])], False


def _can_group_legs(legs: list[dict], start: int, end: int) -> bool:
    if end <= start:
        return False
    codes = [str(legs[start].get("from_code") or "")]
    if not codes[0]:
        return False
    for idx in range(start, end + 1):
        to_code = str(legs[idx].get("to_code") or "")
        if not to_code:
            return False
        codes.append(to_code)
    return len(codes) == len(set(codes))


def _resolve_group_coords(
    legs: list[dict],
    start: int,
    end: int,
    fetcher: PaperEkispertShapeFetcher | None,
) -> tuple[list[tuple[float, float]], bool]:
    if fetcher is None or not _can_group_legs(legs, start, end):
        return [], False
    first = legs[start]
    last = legs[end]
    fetched = fetcher.fetch_leg_shape(
        str(first.get("from_code")),
        str(last.get("to_code")),
        str(first.get("departure", "")) or None,
    )
    if not fetched:
        return [], False
    coords = [(float(pt["lon"]), float(pt["lat"])) for pt in fetched]
    return coords, bool(coords)


def render_route_png(
    route_json_path: Path,
    output_png_path: Path,
    *,
    fetcher: PaperEkispertShapeFetcher | None = None,
) -> dict[str, int]:
    payload = load_route_json(route_json_path)
    fig, ax = plt.subplots(figsize=(7.0, 7.0))

    for segment in CITY_SEGMENTS:
        xs = [pt[0] for pt in segment]
        ys = [pt[1] for pt in segment]
        ax.plot(xs, ys, color="#d8d8d8", linewidth=0.7, zorder=1)

    all_lons: list[float] = []
    all_lats: list[float] = []
    fetched_legs = 0
    fallback_legs = 0
    legs = payload.get("legs", [])
    draw_items: list[tuple[list[tuple[float, float]], bool, int]] = []
    idx = 0
    while idx < len(legs):
        group_end = idx
        while group_end + 1 < len(legs):
            current = legs[group_end]
            nxt = legs[group_end + 1]
            if (
                current.get("line_name") == nxt.get("line_name")
                and current.get("to_code") == nxt.get("from_code")
            ):
                group_end += 1
                continue
            break

        coords: list[tuple[float, float]] = []
        used_fetch = False
        covered_legs = 1
        if group_end > idx:
            coords, used_fetch = _resolve_group_coords(legs, idx, group_end, fetcher)
            if coords:
                covered_legs = group_end - idx + 1
                draw_items.append((coords, used_fetch, covered_legs))
                if used_fetch:
                    fetched_legs += covered_legs
                else:
                    fallback_legs += covered_legs
                idx = group_end + 1
                continue

        leg = legs[idx]
        coords, used_fetch = _resolve_leg_coords(leg, fetcher)
        if not coords:
            idx += 1
            continue
        draw_items.append((coords, used_fetch, covered_legs))
        if used_fetch:
            fetched_legs += covered_legs
        else:
            fallback_legs += covered_legs
        idx += 1

    for draw_idx, (coords, _used_fetch, _covered_legs) in enumerate(draw_items):
        lons = [pt[0] for pt in coords]
        lats = [pt[1] for pt in coords]
        all_lons.extend(lons)
        all_lats.extend(lats)
        color = ROUTE_COLORS[draw_idx % len(ROUTE_COLORS)]
        ax.plot(lons, lats, color=color, linewidth=3.0, alpha=0.88, zorder=3)
        ax.scatter(lons[0], lats[0], color=color, s=18, zorder=4)

    if all_lons and all_lats:
        ax.scatter(all_lons[0], all_lats[0], color="green", marker="D", s=80, zorder=5)
        ax.scatter(all_lons[-1], all_lats[-1], color="red", marker="X", s=80, zorder=5)
        margin_x = max(0.01, (max(all_lons) - min(all_lons)) * 0.15)
        margin_y = max(0.01, (max(all_lats) - min(all_lats)) * 0.15)
        ax.set_xlim(min(all_lons) - margin_x, max(all_lons) + margin_x)
        ax.set_ylim(min(all_lats) - margin_y, max(all_lats) + margin_y)

    stats = payload.get("statistics", {})
    ax.set_title(
        f"{payload.get('title', 'Exp4 Route')}\n"
        f"Stop Score {float(stats.get('stop_score_total', 0.0)):.1f} | "
        f"Gen {float(stats.get('elapsed_ms', 0.0)):.1f} ms | "
        f"Score/h {float(stats.get('score_per_hour', 0.0)):.1f}",
        fontsize=11,
    )
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return {"fetched_legs": fetched_legs, "fallback_legs": fallback_legs}


def build_case_panel(
    case: dict,
    case_dir: Path,
    *,
    fetcher: PaperEkispertShapeFetcher | None = None,
) -> str:
    route_png_paths: list[tuple[dict, Path]] = []
    total_fetched_legs = 0
    total_fallback_legs = 0
    for artifact in case.get("artifacts", []):
        route_json_raw = str(artifact.get("route_json_path", "")).strip()
        if not route_json_raw:
            continue
        route_json_path = _resolve_project_path(route_json_raw)
        route_png_path = case_dir / f"{case['id']}__{artifact['algorithm_key']}.png"
        stats = render_route_png(route_json_path, route_png_path, fetcher=fetcher)
        total_fetched_legs += stats["fetched_legs"]
        total_fallback_legs += stats["fallback_legs"]
        route_png_paths.append((artifact, route_png_path))

    if not route_png_paths:
        return ""

    fig, axes = plt.subplots(1, len(route_png_paths), figsize=(6.5 * len(route_png_paths), 7.5))
    if len(route_png_paths) == 1:
        axes = [axes]

    for ax, (artifact, png_path) in zip(axes, route_png_paths, strict=False):
        img = plt.imread(png_path)
        sm = artifact["summary_metrics"]
        ax.imshow(img)
        ax.set_title(
            f"{artifact['algorithm_name']}\n"
            f"Score {float(sm['stop_score_total']):.1f} | Gen {float(artifact['elapsed_ms']):.1f} ms\n"
            f"Score/h {float(sm['score_per_hour']):.1f} | Scored Stops {float(sm['scored_stop_count']):.0f}",
            fontsize=10,
        )
        ax.axis("off")

    depart_time = int(case["depart_time"])
    fig.suptitle(
        f"{case['title']}\n"
        f"{case['origin_name']} | {depart_time // 60:02d}:{depart_time % 60:02d} | "
        f"{int(case['budget_minutes']) // 60}h | score_seed={case['score_seed']} | seed={case['seed']}",
        fontsize=14,
    )
    fig.text(0.5, 0.02, case["selection_reason"], ha="center", fontsize=10)
    panel_path = EXP4_FIGURES_DIR / f"exp4_{case['id']}_panel.png"
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(panel_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    if fetcher is not None:
        print(
            f"Case {case['id']}: fetched {total_fetched_legs} legs from Ekispert shape API, "
            f"fell back on {total_fallback_legs} legs."
        )
    return str(panel_path)


def build_collection_panel(cases: list[dict], *, title: str, output_path: Path) -> str:
    panel_cases = [case for case in cases if str(case.get("panel_path", "")).strip()]
    if not panel_cases:
        return ""

    fig, axes = plt.subplots(len(panel_cases), 1, figsize=(16, 8 * len(panel_cases)))
    if len(panel_cases) == 1:
        axes = [axes]

    for ax, case in zip(axes, panel_cases, strict=False):
        img = plt.imread(case["panel_path"])
        ax.imshow(img)
        ax.set_title(case["title"], fontsize=13)
        ax.axis("off")

    fig.suptitle(title, fontsize=16)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return str(output_path)


def write_summary_md(cases: list[dict], *, main_panel_path: str = "", appendix_panel_path: str = "") -> None:
    EXP4_SUMMARY_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EXP4_SUMMARY_MD_PATH, "w", encoding="utf-8") as f:
        f.write("# Exp4 Case Summary\n\n")
        if main_panel_path:
            rel = Path(main_panel_path).relative_to(PROJECT_ROOT)
            f.write(f"- Main cases panel: `{rel.as_posix()}`\n")
        if appendix_panel_path:
            rel = Path(appendix_panel_path).relative_to(PROJECT_ROOT)
            f.write(f"- Appendix panel: `{rel.as_posix()}`\n")
        f.write("\n")
        for case in cases:
            f.write(f"## {case['title']}\n\n")
            f.write(f"- Case id: `{case['id']}`\n")
            f.write(f"- Role: `{case['paper_role']}` / `{case['paper_group']}`\n")
            f.write(f"- Query: `{case['origin_name']}`, `{int(case['depart_time']) // 60:02d}:{int(case['depart_time']) % 60:02d}`, `{int(case['budget_minutes']) // 60}h`, `score_seed={case['score_seed']}`, `seed={case['seed']}`\n")
            f.write(f"- Focus: {case['qualitative_focus']}\n")
            f.write(f"- Selection: {case['selection_reason']}\n")
            panel_path = str(case.get("panel_path", "")).strip()
            if panel_path:
                rel = Path(panel_path).relative_to(PROJECT_ROOT)
                f.write(f"- Panel: `{rel.as_posix()}`\n")
            f.write("\n")
            f.write("| Algorithm | Stop Score | Gen ms | Score/h | Effective Time | Scored Stops | Feasible |\n")
            f.write("| --- | ---: | ---: | ---: | ---: | ---: | --- |\n")
            for artifact in case.get("artifacts", []):
                sm = artifact["summary_metrics"]
                f.write(
                    f"| {artifact['algorithm_name']} | {float(sm['stop_score_total']):.1f} | {float(artifact['elapsed_ms']):.1f} | "
                    f"{float(sm['score_per_hour']):.1f} | {float(sm['effective_time_minutes']):.1f} | {float(sm['scored_stop_count']):.0f} | {artifact['feasible']} |\n"
                )
            f.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot Experiment 4 route-comparison figures.")
    parser.add_argument("--manifest", type=Path, default=EXP4_CASES_PATH, help="Path to exp4_cases.json")
    parser.add_argument("--case-ids", type=str, default="", help="Optional comma-separated subset of case ids.")
    parser.add_argument(
        "--use-ekispert-shapes",
        action="store_true",
        help="Try to fetch actual leg shapes from api.ekispert.jp before falling back to the JSON geometry.",
    )
    args = parser.parse_args()

    fetcher = None
    if args.use_ekispert_shapes:
        load_dotenv(PROJECT_ROOT / ".env")
        api_key = os.getenv("MIXWAY_API_KEY")
        if api_key:
            fetcher = PaperEkispertShapeFetcher(
                api_key,
                base_url=_get_ekispert_api_base_url(),
            )
            print(f"Using Ekispert API endpoint: {_get_ekispert_api_base_url()}")
        else:
            print("MIXWAY_API_KEY not found; route rendering will use JSON geometry only.")

    manifest = load_manifest(args.manifest)
    selected_case_ids = set(parse_csv_tokens(args.case_ids)) if args.case_ids else set()
    all_cases = manifest.get("cases", [])
    target_cases = all_cases
    if selected_case_ids:
        target_cases = [case for case in all_cases if case["id"] in selected_case_ids]

    updates_by_id: dict[str, dict] = {}
    for case in target_cases:
        case_dir = EXP4_FIGURES_DIR / case["id"]
        panel_path = build_case_panel(case, case_dir, fetcher=fetcher)
        case["panel_path"] = panel_path
        updates_by_id[case["id"]] = case
        if panel_path:
            print(f"Saved Exp4 panel: {panel_path}")

    manifest["cases"] = [updates_by_id.get(case["id"], case) for case in all_cases]
    main_cases = [case for case in manifest["cases"] if str(case.get("paper_group", "")) == "main"]
    appendix_cases = [case for case in manifest["cases"] if str(case.get("paper_group", "")) == "appendix"]
    main_panel = build_collection_panel(main_cases, title="Exp4 Main Cases", output_path=EXP4_MAIN_PANEL_PATH)
    appendix_panel = build_collection_panel(appendix_cases, title="Exp4 Appendix Cases", output_path=EXP4_APPENDIX_PANEL_PATH)
    manifest["main_panel_path"] = main_panel
    manifest["appendix_panel_path"] = appendix_panel
    save_json(args.manifest, manifest)
    write_summary_md(manifest["cases"], main_panel_path=main_panel, appendix_panel_path=appendix_panel)
    print(f"Saved Exp4 summary markdown: {EXP4_SUMMARY_MD_PATH}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt  # type: ignore
from matplotlib import font_manager  # type: ignore
from dotenv import load_dotenv  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
APP_API_DIR = PROJECT_ROOT / "apps" / "api"
if str(APP_API_DIR) not in sys.path:
    sys.path.insert(0, str(APP_API_DIR))

from paper.experiments.common.config import FIGURES_BASE_DIR, RESULTS_BASE_DIR  # type: ignore
from services.shape_fetcher import MixwayShapeFetcher  # type: ignore


MANIFEST_PATH = RESULTS_BASE_DIR / "exp2_ablation_study" / "exp2_supporting_route_cases.json"
FIGURES_DIR = FIGURES_BASE_DIR / "exp2"
GEOJSON_PATH = PROJECT_ROOT / "apps" / "api" / "data" / "base" / "fukuoka_city.geojson"
ROUTE_COLORS = ["#0b6e4f", "#ea7317", "#2b59c3", "#c3423f", "#8f2d56", "#3c6e71"]
EKISPERT_API_BASE_URL = os.getenv("PAPER_EKISPERT_API_BASE_URL", "https://api.ekispert.jp")


def _configure_matplotlib_fonts() -> None:
    preferred = [
        "Yu Gothic",
        "Yu Gothic UI",
        "Meiryo",
        "MS Gothic",
        "Noto Sans CJK JP",
        "IPAexGothic",
    ]
    available = {font.name for font in font_manager.fontManager.ttflist}
    chosen = [name for name in preferred if name in available]
    if chosen:
        plt.rcParams["font.family"] = chosen + ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def _query_label(case: dict[str, Any]) -> str:
    depart_time = int(case["depart_time"])
    budget_hours = float(case["budget_minutes"]) / 60.0
    return (
        f"{case['theme_name']} | origin {case['origin_code']} | "
        f"{depart_time // 60:02d}:{depart_time % 60:02d} | {budget_hours:.0f}h | seed={case['seed']}"
    )


def _load_geojson_segments() -> list[list[tuple[float, float]]]:
    if not GEOJSON_PATH.exists():
        return []
    with open(GEOJSON_PATH, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
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


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _render_route(ax: Any, payload: dict[str, Any], fetcher: MixwayShapeFetcher | None) -> None:
    for segment in CITY_SEGMENTS:
        xs = [pt[0] for pt in segment]
        ys = [pt[1] for pt in segment]
        ax.plot(xs, ys, color="#d9dde3", linewidth=0.7, zorder=1)

    all_lons: list[float] = []
    all_lats: list[float] = []
    for idx, leg in enumerate(payload.get("legs", [])):
        coords: list[tuple[float, float]] = []
        if fetcher is not None and leg.get("from_code") and leg.get("to_code"):
            fetched = fetcher.fetch_leg_shape(
                str(leg.get("from_code")),
                str(leg.get("to_code")),
                str(leg.get("departure", "")) or None,
            )
            if fetched:
                coords = [(float(pt["lon"]), float(pt["lat"])) for pt in fetched]
        if not coords:
            path_data = leg.get("path") or []
            if path_data:
                coords = [(float(pt["lon"]), float(pt["lat"])) for pt in path_data]
            else:
                geometry = leg.get("geometry") or {}
                coords = [(float(lon), float(lat)) for lon, lat in geometry.get("coordinates", [])]
        if not coords:
            continue

        color = ROUTE_COLORS[idx % len(ROUTE_COLORS)]
        xs = [pt[0] for pt in coords]
        ys = [pt[1] for pt in coords]
        ax.plot(xs, ys, color=color, linewidth=2.8, alpha=0.9, zorder=3)
        ax.scatter(xs[0], ys[0], color=color, s=12, zorder=4)
        all_lons.extend(xs)
        all_lats.extend(ys)

    if all_lons and all_lats:
        ax.scatter(all_lons[0], all_lats[0], color="#1b9e77", marker="D", s=52, zorder=5)
        ax.scatter(all_lons[-1], all_lats[-1], color="#d95f02", marker="X", s=52, zorder=5)
        margin_x = max(0.01, (max(all_lons) - min(all_lons)) * 0.18)
        margin_y = max(0.01, (max(all_lats) - min(all_lats)) * 0.18)
        ax.set_xlim(min(all_lons) - margin_x, max(all_lons) + margin_x)
        ax.set_ylim(min(all_lats) - margin_y, max(all_lats) + margin_y)

    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")


def _build_panel(case: dict[str, Any], fetcher: MixwayShapeFetcher | None) -> Path:
    artifacts = list(case.get("artifacts", []))
    fig, axes = plt.subplots(1, len(artifacts), figsize=(7.0 * len(artifacts), 7.4))
    if len(artifacts) == 1:
        axes = [axes]

    for ax, artifact in zip(axes, artifacts, strict=False):
        route_path = Path(str(artifact["route_json_path"]))
        payload = _load_json(route_path)
        _render_route(ax, payload, fetcher)
        ax.set_title(
            f"{artifact['algorithm_name']}\n"
            f"ThemeHit {float(artifact['theme_hit_ratio']):.3f} | "
            f"ThemeSat {int(bool(artifact['theme_satisfied']))}\n"
            f"Ride {float(artifact['ride_minutes']):.0f} min | "
            f"Time {float(artifact['elapsed_ms']) / 1000.0:.1f}s",
            fontsize=11,
        )

    depart_time = int(case["depart_time"])
    budget_hours = float(case["budget_minutes"]) / 60.0
    fig.suptitle(
        f"{case['title']}\n"
        f"{case['theme_name']} | origin {case['origin_code']} | "
        f"{depart_time // 60:02d}:{depart_time % 60:02d} | {budget_hours:.0f}h | seed={case['seed']}",
        fontsize=14,
    )
    fig.text(0.5, 0.02, case["selection_reason"], ha="center", fontsize=10)
    fig.subplots_adjust(top=0.85)
    output_path = FIGURES_DIR / f"exp2_supporting_{case['id']}_panel.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot representative Exp2 supporting route cases.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH, help="Path to exp2_supporting_route_cases.json")
    parser.add_argument(
        "--use-ekispert",
        "--use-mixway",
        dest="use_ekispert",
        action="store_true",
        help="Fetch detailed leg shapes from the Ekispert API at api.ekispert.jp. --use-mixway is kept as a backward-compatible alias.",
    )
    args = parser.parse_args()

    _configure_matplotlib_fonts()

    fetcher = None
    if args.use_ekispert:
        load_dotenv(PROJECT_ROOT / ".env")
        api_key = os.getenv("MIXWAY_API_KEY")
        if api_key:
            fetcher = MixwayShapeFetcher(
                api_key,
                base_url=EKISPERT_API_BASE_URL,
                use_cache=True,
            )
            print(f"Using Ekispert API endpoint: {EKISPERT_API_BASE_URL}")
        else:
            print("MIXWAY_API_KEY not found; falling back to route geometry stored in JSON.")
    else:
        print("Ekispert fetching disabled; using route geometry stored in JSON.")

    manifest = _load_json(args.manifest)
    panels: list[dict[str, str]] = []
    for case in manifest.get("cases", []):
        panel_path = _build_panel(case, fetcher)
        case["panel_path"] = str(panel_path)
        panels.append({"case_id": str(case["id"]), "panel_path": str(panel_path)})
        print(f"Saved panel: {panel_path}")

    summary_lines = ["# Exp2 Supporting Route Panels", ""]
    for case in manifest.get("cases", []):
        summary_lines.extend(
            [
                f"## {case['title']}",
                "",
                f"- Theme: `{case['theme_name']}`",
                f"- Query: `{_query_label(case)}`",
                f"- Selection reason: {case['selection_reason']}",
                f"- Panel: `{Path(str(case['panel_path'])).relative_to(PROJECT_ROOT).as_posix()}`",
                "",
            ]
        )
    summary_path = RESULTS_BASE_DIR / "exp2_ablation_study" / "exp2_supporting_route_cases.md"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"Saved summary: {summary_path}")
    with open(args.manifest, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

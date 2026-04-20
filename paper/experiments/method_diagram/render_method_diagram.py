from __future__ import annotations

from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
OUT_BASE = ROOT / "figures" / "method" / "ours_framework_flow"


def save_figure(fig: plt.Figure, out_base: Path) -> None:
    fig.savefig(out_base.with_suffix(".png"), dpi=240, bbox_inches="tight")
    fig.savefig(out_base.with_suffix(".pdf"), bbox_inches="tight")


def rounded(ax, x, y, w, h, *, fc: str, ec: str = "#0f172a", lw: float = 1.4) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.028",
            linewidth=lw,
            edgecolor=ec,
            facecolor=fc,
        )
    )


def stage_box(ax, x, y, w, h, *, idx: str, title: str, body: str, accent: str, fill_color: str) -> None:
    rounded(ax, x, y, w, h, fc=fill_color)
    rounded(ax, x + 0.02, y + h - 0.07, 0.09, 0.045, fc=accent, ec=accent, lw=0.0)
    ax.text(x + 0.065, y + h - 0.048, idx, ha="center", va="center", fontsize=9.5, fontweight="bold", color="#ffffff")
    ax.text(x + 0.02, y + h - 0.10, title, ha="left", va="top", fontsize=11, fontweight="bold", color="#0f172a")
    ax.text(
        x + 0.02,
        y + h - 0.16,
        body,
        ha="left",
        va="top",
        fontsize=8.9,
        color="#334155",
        linespacing=1.45,
    )


def side_panel(ax, x, y, w, h, *, title: str, bullets: list[tuple[str, str]], accent: str, fill_color: str) -> None:
    rounded(ax, x, y, w, h, fc=fill_color)
    ax.text(x + 0.025, y + h - 0.05, title, ha="left", va="top", fontsize=11, fontweight="bold", color="#0f172a")
    cursor_y = y + h - 0.10
    for label, desc in bullets:
        rounded(ax, x + 0.025, cursor_y - 0.012, 0.055, 0.028, fc=accent, ec=accent, lw=0.0)
        ax.text(x + 0.0525, cursor_y + 0.002, label, ha="center", va="center", fontsize=8.2, fontweight="bold", color="#ffffff")
        ax.text(
            x + 0.095,
            cursor_y + 0.004,
            desc,
            ha="left",
            va="top",
            fontsize=8.3,
            color="#334155",
            linespacing=1.35,
        )
        cursor_y -= 0.085


def connect(ax, start: tuple[float, float], end: tuple[float, float], *, color: str = "#475569", lw: float = 2.0) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=16,
            linewidth=lw,
            color=color,
            shrinkA=4,
            shrinkB=4,
        )
    )


def main() -> None:
    OUT_BASE.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(14.4, 8.8), facecolor="#f8fafc")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    rounded(ax, 0.035, 0.90, 0.93, 0.07, fc="#e2e8f0", ec="#e2e8f0", lw=0.0)
    ax.text(
        0.05,
        0.945,
        "ReRAPTOR Search Framework",
        ha="left",
        va="center",
        fontsize=19,
        fontweight="bold",
        color="#0f172a",
    )
    ax.text(
        0.05,
        0.912,
        "Shared timetable-feasible search backbone with task-specific scoring and three-layer pruning",
        ha="left",
        va="center",
        fontsize=10.0,
        color="#334155",
    )

    stage_box(
        ax,
        0.05,
        0.64,
        0.18,
        0.17,
        idx="Step 1",
        title="Load Query",
        body="GTFS stop schedules,\norigin, departure time,\ntime budget, and score profile.",
        accent="#2563eb",
        fill_color="#eff6ff",
    )
    stage_box(
        ax,
        0.29,
        0.64,
        0.18,
        0.17,
        idx="Step 2",
        title="Initialize Label",
        body="Create the base label:\narrival time, visited-stop state,\ncounters, and leg history.",
        accent="#0284c7",
        fill_color="#ecfeff",
    )
    stage_box(
        ax,
        0.53,
        0.64,
        0.18,
        0.17,
        idx="Step 3",
        title="Expand Timetable Edges",
        body="Enumerate feasible outgoing\nservices under transfer\nand budget constraints.",
        accent="#16a34a",
        fill_color="#f0fdf4",
    )
    stage_box(
        ax,
        0.77,
        0.64,
        0.18,
        0.17,
        idx="Step 4",
        title="Update Route State",
        body="Refresh ride time,\nunique stops, geometry features,\nand task-specific accumulators.",
        accent="#ca8a04",
        fill_color="#fefce8",
    )

    stage_box(
        ax,
        0.11,
        0.34,
        0.24,
        0.18,
        idx="Step 5",
        title="Compute Search Score",
        body="Rank each partial route\nwith a task-aware surrogate score\nbefore acceptance.",
        accent="#7c3aed",
        fill_color="#f5f3ff",
    )
    side_panel(
        ax,
        0.41,
        0.27,
        0.28,
        0.30,
        title="Three-Layer Pruning",
        bullets=[
            ("NEG", "Reject loops and clearly weak\npartial routes."),
            ("DOM", "Discard labels dominated\nat the same stop and round."),
            ("BEAM", "Keep only the top-W labels\nper stop-round bucket."),
        ],
        accent="#dc2626",
        fill_color="#fef2f2",
    )
    stage_box(
        ax,
        0.75,
        0.34,
        0.20,
        0.18,
        idx="Step 6",
        title="Keep Accepted Labels",
        body="Store feasible survivors\nfor final ranking\nand route reconstruction.",
        accent="#059669",
        fill_color="#ecfdf5",
    )

    stage_box(
        ax,
        0.29,
        0.08,
        0.42,
        0.12,
        idx="Step 7",
        title="Return Final Itinerary",
        body="Iterate until the frontier is exhausted\nor a resource cap is reached,\nthen output the highest-scored accepted route.",
        accent="#0f172a",
        fill_color="#f8fafc",
    )

    connect(ax, (0.23, 0.725), (0.29, 0.725))
    connect(ax, (0.47, 0.725), (0.53, 0.725))
    connect(ax, (0.71, 0.725), (0.77, 0.725))
    connect(ax, (0.86, 0.64), (0.23, 0.52))
    connect(ax, (0.35, 0.43), (0.41, 0.43))
    connect(ax, (0.69, 0.43), (0.75, 0.43))
    connect(ax, (0.85, 0.34), (0.65, 0.20))

    rounded(ax, 0.05, 0.08, 0.18, 0.12, fc="#ffffff", ec="#cbd5e1", lw=1.2)
    ax.text(0.07, 0.165, "Shared search backbone", ha="left", va="center", fontsize=10.2, fontweight="bold", color="#0f172a")
    ax.text(
        0.07,
        0.118,
        "Steps 1 to 4 are unchanged\nacross the experiments.",
        ha="left",
        va="center",
        fontsize=8.9,
        color="#475569",
        linespacing=1.3,
    )

    rounded(ax, 0.77, 0.08, 0.18, 0.12, fc="#ffffff", ec="#cbd5e1", lw=1.2)
    ax.text(0.79, 0.165, "Task-specific modules", ha="left", va="center", fontsize=10.2, fontweight="bold", color="#0f172a")
    ax.text(
        0.79,
        0.118,
        "Scoring, pruning predicates,\nand acceptance rules change\nby experiment.",
        ha="left",
        va="center",
        fontsize=8.9,
        color="#475569",
        linespacing=1.3,
    )

    save_figure(fig, OUT_BASE)


if __name__ == "__main__":
    main()

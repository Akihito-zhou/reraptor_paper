from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
OUT_BASE = ROOT / "figures" / "method" / "intro_problem_overview"


def save_figure(fig: plt.Figure, out_base: Path) -> None:
    fig.savefig(out_base.with_suffix(".png"), dpi=240, bbox_inches="tight")
    fig.savefig(out_base.with_suffix(".pdf"), bbox_inches="tight")


def rounded_panel(ax, x, y, w, h, *, fc: str, ec: str = "#0f172a", lw: float = 1.5) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.03",
        linewidth=lw,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(patch)


def add_card(ax, x, y, w, h, *, title: str, accent: str, body_lines: list[str], footer: str) -> None:
    rounded_panel(ax, x, y, w, h, fc="#ffffff")
    rounded_panel(ax, x + 0.018, y + h - 0.078, 0.12, 0.05, fc=accent, ec=accent, lw=0.0)
    ax.text(
        x + 0.078,
        y + h - 0.053,
        title,
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="#ffffff",
    )

    cursor_y = y + h - 0.12
    for line in body_lines:
        ax.text(
            x + 0.03,
            cursor_y,
            "\u2022 " + line,
            ha="left",
            va="top",
            fontsize=9.2,
            color="#334155",
            linespacing=1.38,
        )
        cursor_y -= 0.07

    rounded_panel(ax, x + 0.03, y + 0.03, w - 0.06, 0.08, fc="#f8fafc", ec="#cbd5e1", lw=1.1)
    ax.text(
        x + w / 2,
        y + 0.07,
        footer,
        ha="center",
        va="center",
        fontsize=8.6,
        fontweight="bold",
        color="#0f172a",
    )


def add_network(ax, *, title: str, subtitle: str, route_color: str, route: list[tuple[str, str]]) -> None:
    nodes = {
        "O": (0.12, 0.50),
        "A": (0.28, 0.76),
        "B": (0.30, 0.24),
        "C": (0.50, 0.50),
        "D": (0.72, 0.77),
        "E": (0.70, 0.24),
        "F": (0.88, 0.50),
    }
    edges = [
        ("O", "A"),
        ("O", "B"),
        ("A", "C"),
        ("B", "C"),
        ("C", "D"),
        ("C", "E"),
        ("D", "F"),
        ("E", "F"),
    ]

    rounded_panel(ax, 0.0, 0.0, 1.0, 1.0, fc="#ffffff", ec="#cbd5e1", lw=1.2)
    ax.text(0.05, 0.92, title, ha="left", va="center", fontsize=10.0, fontweight="bold", color="#0f172a")
    ax.text(0.05, 0.84, subtitle, ha="left", va="center", fontsize=8.2, color="#475569")

    for a, b in edges:
        xa, ya = nodes[a]
        xb, yb = nodes[b]
        ax.plot([xa, xb], [ya, yb], color="#d7dee8", lw=3.0, zorder=1, solid_capstyle="round")

    for a, b in route:
        xa, ya = nodes[a]
        xb, yb = nodes[b]
        ax.plot([xa, xb], [ya, yb], color=route_color, lw=5.2, zorder=3, solid_capstyle="round")

    for name, (x, y) in nodes.items():
        radius = 0.032 if name == "O" else 0.026
        face = "#0f172a" if name == "O" else "#ffffff"
        edge = "#0f172a"
        ax.add_patch(Circle((x, y), radius, facecolor=face, edgecolor=edge, lw=1.6, zorder=4))
        ax.text(
            x,
            y - 0.07,
            "Origin" if name == "O" else name,
            ha="center",
            va="top",
            fontsize=8.2,
            color="#334155",
        )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def main() -> None:
    OUT_BASE.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(14.2, 8.6), facecolor="#f8fafc")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    rounded_panel(ax, 0.035, 0.88, 0.93, 0.09, fc="#e2e8f0", ec="#e2e8f0", lw=0.0)
    ax.text(
        0.05,
        0.942,
        "From Earliest Arrival to Budgeted Itinerary Value",
        ha="left",
        va="center",
        fontsize=19,
        fontweight="bold",
        color="#0f172a",
    )
    ax.text(
        0.05,
        0.904,
        "The timetable constraints stay unchanged; the optimization target moves from shortest journey to higher-value city exploration.",
        ha="left",
        va="center",
        fontsize=10.0,
        color="#334155",
    )

    add_card(
        ax,
        0.05,
        0.52,
        0.26,
        0.28,
        title="Conventional Query",
        accent="#2563eb",
        body_lines=[
            "Origin, departure time,\nand GTFS feasibility.",
            "Optimize arrival time,\nnot itinerary value.",
        ],
        footer="Earliest feasible arrival",
    )
    add_card(
        ax,
        0.37,
        0.52,
        0.26,
        0.28,
        title="Budgeted Goal",
        accent="#059669",
        body_lines=[
            "Same timetable and\ntransfer constraints.",
            "Maximize ride value,\nstop diversity, and spread.",
        ],
        footer="Highest feasible itinerary value",
    )
    add_card(
        ax,
        0.69,
        0.52,
        0.26,
        0.28,
        title="Why It Is Hard",
        accent="#7c3aed",
        body_lines=[
            "Partial routes need richer\nstate than shortest paths.",
            "Too many labels cause\nsearch-space explosion.",
        ],
        footer="Need: richer state with bounded search",
    )

    ax.add_patch(
        FancyArrowPatch((0.31, 0.66), (0.37, 0.66), arrowstyle="-|>", mutation_scale=16, linewidth=2.2, color="#64748b")
    )
    ax.add_patch(
        FancyArrowPatch((0.63, 0.66), (0.69, 0.66), arrowstyle="-|>", mutation_scale=16, linewidth=2.2, color="#64748b")
    )

    ax.text(0.5, 0.46, "Same timetable network, different optimization target", ha="center", va="center", fontsize=10.6, fontweight="bold", color="#334155")

    left = fig.add_axes([0.07, 0.11, 0.39, 0.28])
    right = fig.add_axes([0.54, 0.11, 0.39, 0.28])

    add_network(
        left,
        title="Shortest-journey style",
        subtitle="Feasible but narrow route with fewer stops",
        route_color="#f97316",
        route=[("O", "A"), ("A", "C"), ("C", "F")],
    )
    add_network(
        right,
        title="Value-maximizing itinerary",
        subtitle="Still feasible, but collects broader route value",
        route_color="#059669",
        route=[("O", "B"), ("B", "C"), ("C", "D"), ("D", "F")],
    )

    ax.add_patch(
        FancyArrowPatch((0.47, 0.25), (0.53, 0.25), arrowstyle="-|>", mutation_scale=18, linewidth=2.4, color="#0f172a")
    )
    ax.text(0.50, 0.29, "Optimization target changes", ha="center", va="bottom", fontsize=9.6, color="#475569")

    save_figure(fig, OUT_BASE)


if __name__ == "__main__":
    main()

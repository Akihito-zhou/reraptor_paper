"""
Algorithm registry.

Import all algorithm classes and expose them via `ALL_ALGORITHMS` list
for the experiment runner.
"""
from __future__ import annotations

from .ours_full import OursFull
from .pure_raptor import PureRaptor
from .greedy import GreedyLookahead
from .mcraptor import McRaptorBaseline
from .ils_2opt import ILS2Opt
from .vns import VNS
from .nsga2 import NSGA2
from .sa import SimulatedAnnealing
from .zhang2025_dynamic_pref_adapted import Zhang2025DynamicPrefAdapted
from .zhou_wang_2025_alns_adapted import ZhouWang2025ALNSAdapted

def _norm_algo_name(value: str) -> str:
    return "".join(ch.lower() for ch in str(value) if ch.isalnum())


def _keep_algorithm(algo_name: str, requested_norm: set[str]) -> bool:
    if not requested_norm:
        return True
    name_norm = _norm_algo_name(algo_name)
    for token in requested_norm:
        if token == name_norm or token in name_norm:
            return True
    return False


def build_all_algorithms(
    *,
    objective=None,
    include_recent_adapted: bool = False,
    algorithm_filter: list[str] | None = None,
) -> list:
    """
    Build a fresh algorithm set for one experiment session.

    Using new instances avoids accidental cross-run state carry-over from
    mutable algorithm objects such as cached metrics or diagnostic counters.
    """
    algorithms = [
        OursFull(),
        ILS2Opt(),
        VNS(),
        NSGA2(),
        SimulatedAnnealing(),
        McRaptorBaseline(),
        PureRaptor(),
        GreedyLookahead(),
    ]
    if include_recent_adapted:
        algorithms.extend(
            [
                Zhang2025DynamicPrefAdapted(),
                ZhouWang2025ALNSAdapted(),
            ]
        )

    requested_norm = {_norm_algo_name(x) for x in (algorithm_filter or []) if str(x).strip()}
    if requested_norm:
        algorithms = [algo for algo in algorithms if _keep_algorithm(algo.name, requested_norm)]

    if objective is not None:
        for algo in algorithms:
            algo.objective = objective
    return algorithms


ALL_ALGORITHMS = build_all_algorithms()

__all__ = ["ALL_ALGORITHMS", "build_all_algorithms"]

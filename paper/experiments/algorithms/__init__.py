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

def build_all_algorithms(*, objective=None) -> list:
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
    if objective is not None:
        for algo in algorithms:
            algo.objective = objective
    return algorithms


ALL_ALGORITHMS = build_all_algorithms()

__all__ = ["ALL_ALGORITHMS", "build_all_algorithms"]

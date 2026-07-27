"""Frozen configuration grid for canonical Stop Score sensitivity analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Iterable

from paper.experiments.algorithms.ours_full import OursFull
from paper.experiments.common.stop_scoring import StopScoringProfile


@dataclass(frozen=True)
class SensitivitySpec:
    """One deterministic ReRAPTOR sensitivity configuration."""

    config_id: str
    panel: str
    factor: str
    factor_value: str
    beam_width: int = 50
    candidate_cap_short: int | None = 30
    candidate_cap_long: int | None = 20
    reward_coefficient: float = 10000.0
    score_per_hour_coefficient: float = 5.0
    effective_time_coefficient: float = 0.1
    overrun_penalty: float = 50000.0
    negative_penalty_scale: float = 1.0

    @property
    def algorithm_name(self) -> str:
        return f"ReRAPTOR sensitivity [{self.config_id}]"

    def objective(
        self,
        *,
        stop_scores: dict[str, int],
        dwell_minutes: int,
        search_mode: str,
    ) -> StopScoringProfile:
        return StopScoringProfile(
            stop_scores=stop_scores,
            dwell_minutes=dwell_minutes,
            search_mode=search_mode,
            reward_coefficient=self.reward_coefficient,
            score_per_hour_coefficient=self.score_per_hour_coefficient,
            effective_time_coefficient=self.effective_time_coefficient,
            overrun_penalty=self.overrun_penalty,
        )

    def algorithm(
        self,
        *,
        objective: StopScoringProfile,
        timeout_seconds: float,
    ) -> OursFull:
        algorithm = OursFull(
            use_beam=True,
            use_dominance=True,
            use_negative_score=True,
            beam_width=self.beam_width,
            timeout_seconds=timeout_seconds,
            objective_candidate_cap_short=self.candidate_cap_short,
            objective_candidate_cap_long=self.candidate_cap_long,
            negative_repeat_penalty=50000.0 * self.negative_penalty_scale,
            negative_short_hop_penalty=20000.0 * self.negative_penalty_scale,
        )
        algorithm.name = self.algorithm_name
        algorithm.objective = objective
        return algorithm

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_SPEC = SensitivitySpec(
    config_id="default",
    panel="oat",
    factor="default",
    factor_value="W50; cap(30,20); reward10000; SPH5; time0.1; neg1",
)


def _variants(
    factor: str,
    values: Iterable[tuple[str, str, dict[str, Any]]],
) -> list[SensitivitySpec]:
    return [
        replace(
            DEFAULT_SPEC,
            config_id=config_id,
            factor=factor,
            factor_value=factor_value,
            **updates,
        )
        for config_id, factor_value, updates in values
    ]


OAT_SPECS: tuple[SensitivitySpec, ...] = tuple(
    [
        DEFAULT_SPEC,
        *_variants(
            "beam_width",
            (
                ("w10", "10", {"beam_width": 10}),
                ("w25", "25", {"beam_width": 25}),
                ("w100", "100", {"beam_width": 100}),
                ("w200", "200", {"beam_width": 200}),
            ),
        ),
        *_variants(
            "candidate_cap",
            (
                (
                    "cap15_10",
                    "(15,10)",
                    {"candidate_cap_short": 15, "candidate_cap_long": 10},
                ),
                (
                    "cap60_40",
                    "(60,40)",
                    {"candidate_cap_short": 60, "candidate_cap_long": 40},
                ),
                (
                    "cap_uncapped",
                    "uncapped",
                    {"candidate_cap_short": None, "candidate_cap_long": None},
                ),
            ),
        ),
        *_variants(
            "reward_coefficient",
            (
                ("reward5000", "5000", {"reward_coefficient": 5000.0}),
                ("reward20000", "20000", {"reward_coefficient": 20000.0}),
            ),
        ),
        *_variants(
            "score_per_hour_coefficient",
            (
                ("sph0", "0", {"score_per_hour_coefficient": 0.0}),
                ("sph2p5", "2.5", {"score_per_hour_coefficient": 2.5}),
                ("sph10", "10", {"score_per_hour_coefficient": 10.0}),
            ),
        ),
        *_variants(
            "effective_time_coefficient",
            (
                ("time0", "0", {"effective_time_coefficient": 0.0}),
                ("time0p05", "0.05", {"effective_time_coefficient": 0.05}),
                ("time0p2", "0.2", {"effective_time_coefficient": 0.2}),
            ),
        ),
        *_variants(
            "negative_penalty_scale",
            (
                ("neg0p5", "0.5", {"negative_penalty_scale": 0.5}),
                ("neg2", "2", {"negative_penalty_scale": 2.0}),
            ),
        ),
    ]
)


# The five center-line interaction cells are already supplied by the OAT panel:
# w25, default, w100, cap15_10, and cap60_40. Only the four corners require
# additional runs on the preregistered smaller interaction subset.
INTERACTION_CORNER_SPECS: tuple[SensitivitySpec, ...] = tuple(
    replace(
        DEFAULT_SPEC,
        config_id=f"int_w{width}_cap{short}_{long}",
        panel="interaction",
        factor="beam_width_x_candidate_cap",
        factor_value=f"W={width}; cap=({short},{long})",
        beam_width=width,
        candidate_cap_short=short,
        candidate_cap_long=long,
    )
    for width in (25, 100)
    for short, long in ((15, 10), (60, 40))
)


def all_specs() -> tuple[SensitivitySpec, ...]:
    return (*OAT_SPECS, *INTERACTION_CORNER_SPECS)


def select_specs(
    *,
    panel: str,
    requested_ids: Iterable[str] | None = None,
    include_default: bool = False,
) -> list[SensitivitySpec]:
    if panel == "oat":
        candidates = list(OAT_SPECS)
    elif panel == "interaction":
        candidates = list(INTERACTION_CORNER_SPECS)
    elif panel == "all":
        candidates = list(all_specs())
    else:
        raise ValueError(f"Unknown sensitivity panel: {panel}")

    if not include_default:
        candidates = [spec for spec in candidates if spec.config_id != "default"]

    requested = {str(value).strip().lower() for value in (requested_ids or []) if str(value).strip()}
    if not requested:
        return candidates
    selected = [spec for spec in candidates if spec.config_id.lower() in requested]
    missing = sorted(requested - {spec.config_id.lower() for spec in selected})
    if missing:
        raise ValueError(f"Unknown sensitivity config id(s): {missing}")
    return selected

# Adaptation Notes for Recent (2024+) Baselines

This note documents how recent methods were adapted to the paper's benchmark setting:

- timetable-feasible stop-schedule expansion
- fixed departure time and fixed time budget
- open itinerary (no fixed destination)
- stop-reward objective evaluation (`stop_score_total`)

## 1) Zhang et al. (2025, TRE) - Dynamic preference-based multimodal trip planning

- Original scope: dynamic preference-based multimodal planning for PT + shared mobility.
- Adapted baseline: `Zhang2025-DynPref (adapted)`.
- Adaptation idea:
  - keep rolling-horizon preference adaptation spirit;
  - use timetable-feasible edge expansion only (no external mobility mode simulation);
  - dynamically shift search preference from diversity (early budget stage) to efficiency (late stage).

## 2) Li & Kim (2024, CMC) - Real-time demand-responsive transit route planning

- Original scope: queue-based real-time heuristic A* for demand-responsive transit.
- Adapted baseline: `LiKim2024-RTA* (adapted)`.
- Adaptation idea:
  - use queue-based best-first expansion over timetable-feasible candidates;
  - define A*-like score from current collected reward + discounted optimistic upper bound;
  - keep hard feasibility checks through shared route-validation/evaluation pipeline.

## 3) Zhou & Wang (2025, FEM) - routing + request selection in demand-adaptive systems

- Original scope: demand-adaptive multi-route planning with ALNS-style search.
- Adapted baseline: `ZhouWang2025-ALNS (adapted)`.
- Adaptation idea:
  - use ALNS destroy/repair operator loop under timetable-feasible regrowth;
  - adaptive operator weights updated by accepted improvements;
  - simulated-annealing acceptance for diversification.

## Fair Comparison Policy

- All adapted baselines are evaluated by the same objective metrics as other methods:
  - `stop_score_total`
  - `elapsed_ms`
  - `score_per_hour`
  - `effective_budget_feasible`
- All methods share identical query sets, budgets, stop-score seeds, and planner data.

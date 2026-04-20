from __future__ import annotations

import heapq
import logging
import os
import threading
import time
from bisect import bisect_left
from collections import defaultdict
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

from . import planner_loader
from .planner_constants import (
    DATA_DIR,
    DEFAULT_REALTIME_CACHE_SECONDS,
    MAX_LOOKAHEAD_MINUTES,
    MAX_BRANCH_PER_EXPANSION,
    MAX_EXPANSIONS,
    MAX_QUEUE_SIZE,
    MAX_ROUTES_FOR_RAPTOR,
    MAX_TRIPS_PER_ROUTE,
    START_TIME_MINUTES,
    TRANSFER_BUFFER_MINUTES,
)
from .planner_models import (
    ChallengePlan,
    JourneyLeg,
    RouteData,
    RouteTrip,
    SearchState,
    Station,
    StopSchedule,
    TripEdge,
)
from .planner_utils import collapse_edges, derive_quadrant_labels
from .planners import (
    city_loop,
    longest_duration,
    most_stops,
    ultimate_challenge,
)


try:  # pragma: no cover - allow running as either package or module
    from ..clients.ekispert_bus import EkispertBusClient
except ImportError:  # pragma: no cover
    from clients.ekispert_bus import EkispertBusClient  # type: ignore

try:  # pragma: no cover - allow running as either package or module
    from .realtime_timetable import RealtimeTimetableManager
except ImportError:  # pragma: no cover
    from realtime_timetable import RealtimeTimetableManager  # type: ignore


logger = logging.getLogger(__name__)


class PlannerError(RuntimeError):
    """Raised when the planner cannot compute challenges."""


class PlannerService:
    """Generates challenge plans based on stored timetable + geo data."""

    def __init__(
        self,
        data_dir: Path | None = None,
        *,
        enable_realtime: bool | None = None,
        api_key: str | None = None,
        realtime_cache_seconds: int = DEFAULT_REALTIME_CACHE_SECONDS,
    ):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.stations: dict[str, Station] = {}
        self.line_names: dict[str, str] = {}
        self.eligible_lines: set[str] = set()
        self.stop_schedules: dict[str, StopSchedule] = {}
        self.hakata_stops: list[str] = []
        self.quadrant_map: dict[str, int] = {}
        self.line_stop_edges: dict[str, list[str]] = {}

        self._cache: dict[str, ChallengePlan] | None = None
        self._cache_mtime: float = 0.0
        self._lock = threading.Lock()
        self._latest_data_file: Path | None = None
        self.static_edges: list[TripEdge] = []
        self.routes: dict[str, RouteData] = {}
        self.routes_by_stop: dict[str, set[str]] = defaultdict(set)
        self.hakata_coord: tuple[float, float] = (33.589, 130.420)
        self.inner_radius_km: float = 2.0
        self.city_boundary: list[list[tuple[float, float]]] = []
        self._distance_cache: dict[tuple[str, str], float] = {}
        self.boundary_sequence: list[str] = []
        self.boundary_index: dict[str, int] = {}
        self.trip_id_to_metadata: dict[str, dict] = {}
        self._beam_cache: dict[tuple, SearchState | None] = {}

        env_flag = os.getenv("PLANNER_ENABLE_REALTIME", "").strip().lower()
        env_enabled = env_flag in {"1", "true", "yes", "on"}
        self._realtime_cache_seconds = max(30, realtime_cache_seconds)
        desired_realtime = (
            enable_realtime if enable_realtime is not None else env_enabled
        )
        api_key_value = api_key or os.getenv("EKISPERT_API_KEY")
        client = (
            EkispertBusClient(api_key_value)
            if desired_realtime and api_key_value
            else None
        )
        if desired_realtime and not api_key_value:
            logger.warning(
                "Planner realtime mode requested but EKISPERT_API_KEY is missing; "
                "falling back to static data."
            )
        self._timetable_manager = RealtimeTimetableManager(
            client,
            enable_realtime=client is not None,
            cache_seconds=self._realtime_cache_seconds,
        )
        self._realtime_active = self._timetable_manager.realtime_enabled
        self._cache_generated_at = 0.0

    # ---------- public API ----------

    @staticmethod
    def _normalize_challenge_id(challenge_id: str) -> str:
        """Normalize challenge IDs to the kebab-case form used by the API."""
        return challenge_id.strip().lower().replace("_", "-")

    def list_challenges(self) -> list[dict]:
        plans = self._ensure_plans()
        return [plan.to_dict() for plan in plans.values() if plan]

    def get_challenge(self, challenge_id: str) -> dict:
        normalized_id = self._normalize_challenge_id(challenge_id)
        plans = self._ensure_plans()
        if normalized_id not in plans or not plans[normalized_id]:
            raise PlannerError(f"challenge '{challenge_id}' not available")
        return plans[normalized_id].to_dict()

    def ensure_data_loaded(self) -> None:
        """Ensures that basic static data (stations, edges) is loaded."""
        with self._lock:
            # If stations are already loaded, we assume data is ready enough for ad-hoc queries
            if self.stations:
                return

            try:
                latest = self._call_loader(planner_loader.find_latest_data_file, self)
                if not latest:
                    logger.warning("No data file found during ensure_data_loaded")
                    return
                
                self._load_static_assets()
                self._load_edges(latest)
                self._latest_data_file = latest
                # Note: We don't set self._cache here because we haven't computed challenges.
                # _ensure_plans will still trigger a reload/recompute if called later, 
                # effectively refreshing everything, which is fine.
                logger.info(f"Data loaded successfully: {len(self.stations)} stations")
                
            except Exception as e:
                logger.error(f"Failed to load data: {e}")
                # We don't raise here to avoid crashing if data is temporarily bad,
                # but caller might fail later


    # ---------- bootstrap ----------

    def _ensure_plans(self) -> dict[str, ChallengePlan | None]:
        with self._lock:
            latest = self._call_loader(planner_loader.find_latest_data_file, self)
            latest_mtime = latest.stat().st_mtime if latest else 0.0
            now_ts = time.time()
            static_stale = (
                not self._cache
                or self._latest_data_file != latest
                or self._cache_mtime < latest_mtime
            )
            realtime_stale = self._realtime_active and (
                now_ts - self._cache_generated_at >= self._realtime_cache_seconds
            )
            if self._cache and not static_stale and not realtime_stale:
                return self._cache

            if static_stale:
                self._load_static_assets()
                self._load_edges(latest)
            elif realtime_stale:
                self._refresh_stop_schedules(force_refresh=True)

            plans = self._compute_challenges()
            self._cache = plans
            self._cache_mtime = latest_mtime
            self._latest_data_file = latest
            # track for realtime invalidation
            self._cache_generated_at = now_ts
            return plans

    def _call_loader(self, func: Callable, *args, **kwargs):
        """Invokes a loader function, wrapping exceptions in PlannerError."""
        try:
            return func(*args, **kwargs)
        except RuntimeError as exc:
            raise PlannerError(str(exc)) from exc

    def _load_static_assets(self) -> None:
        """Loads static assets like station and line data."""
        self._call_loader(planner_loader.load_static_assets, self)
        
        # The loader now only loads stations within Fukuoka city.
        # The fukuoka_station_codes set is still used by build_boundary_sequence.
        self.fukuoka_station_codes = set(self.stations.keys())
        
        # Keep the city boundary polygons for other potential uses.
        import json
        self.fukuoka_polygons = []
        geojson_path = self.data_dir / "base" / "fukuoka_city.geojson"
        if geojson_path.exists():
            with geojson_path.open("r", encoding="utf-8") as f:
                geojson_data = json.load(f)
                for feature in geojson_data.get("features", []):
                    geom = feature.get("geometry", {})
                    if geom.get("type") == "Polygon":
                        self.fukuoka_polygons.append(geom["coordinates"][0])
                    elif geom.get("type") == "MultiPolygon":
                        for polygon in geom["coordinates"]:
                            self.fukuoka_polygons.append(polygon[0])


    def _load_edges(self, data_path: Path | None) -> None:
        """Loads trip edge data and initializes schedules."""
        self._call_loader(planner_loader.load_edges, self, data_path)
        if not self.stop_schedules:
            raise PlannerError("Failed to find a route for the longest ride.")
        
        # Build a lookup table to get metadata from trip_id
        for edge in self.static_edges:
            if edge.trip_id not in self.trip_id_to_metadata:
                self.trip_id_to_metadata[edge.trip_id] = {
                    "direction": edge.direction,
                    "service_date": edge.service_date,
                }

    def _refresh_stop_schedules(self, *, force_refresh: bool = False) -> None:
        """Refreshes stop schedules from either realtime or static data."""
        horizon_start = START_TIME_MINUTES
        horizon_end = START_TIME_MINUTES + 24 * 60
        edges: list[TripEdge] = []
        if self._timetable_manager:
            edges = self._timetable_manager.get_edges_for_window(
                horizon_start,
                horizon_end,
                line_filter=self.eligible_lines,
                force_refresh=force_refresh,
            )
        if not edges:
            edges = [
                edge
                for edge in self.static_edges
                if edge.arrive >= horizon_start and edge.depart <= horizon_end
            ]
        if not edges:
            logger.warning(
                "No timetable edges available between %s and %s minutes.",
                horizon_start,
                horizon_end,
            )
            self.stop_schedules = {}
            return
        schedules: dict[str, StopSchedule] = defaultdict(StopSchedule)
        for edge in edges:
            schedules[edge.from_code].add_edge(edge)
        if not schedules and edges:
            logger.warning(
                "Edges available but no schedules were constructed; check data integrity."
            )
        for sched in schedules.values():
            sched.finalize()
        self.stop_schedules = schedules
        # reset cached beam searches when schedules change
        self._beam_cache.clear()
        self._build_route_timetables()

    def _build_route_timetables(self) -> None:
        """Constructs route-based timetables dynamically based on exact trip stop sequences."""
        routes: dict[str, RouteData] = {}
        routes_by_stop: dict[str, set[str]] = defaultdict(set)

        # 1. Group edges by trip_id, maintaining sorted order
        raw_trips: dict[str, list[TripEdge]] = defaultdict(list)
        for edge in self.static_edges:
            if edge.line_id not in self.eligible_lines:
                continue
            raw_trips[edge.trip_id].append(edge)

        # 2. Extract sequences and group trips by exact sequence signature
        signature_groups: dict[tuple[str, ...], list[list[TripEdge]]] = defaultdict(list)
        for trip_id, edges in raw_trips.items():
            edges.sort(key=lambda e: e.depart)
            
            # Trace the continuous sequence. If there are gaps, the sequence is broken.
            seq = [edges[0].from_code]
            valid = True
            for e in edges:
                if e.from_code == seq[-1]:
                    if e.to_code not in seq:
                        seq.append(e.to_code)
                else:
                    valid = False
                    break
            
            if valid and len(seq) >= 2:
                signature_groups[tuple(seq)].append(edges)

        # 3. Build RAPTOR Routes
        for sig_idx, (stops_seq, trip_list) in enumerate(signature_groups.items()):
            if len(routes) >= MAX_ROUTES_FOR_RAPTOR:
                break
                
            sample_edge = trip_list[0][0]
            route_key = f"{sample_edge.line_id}:{sample_edge.direction}_T{sig_idx}"
            
            stop_to_index = {code: idx for idx, code in enumerate(stops_seq)}
            
            route_trips = []
            for edges in trip_list:
                departures: list[int | None] = [None] * len(stops_seq)
                arrivals: list[int | None] = [None] * len(stops_seq)
                segment_distances: list[float] = [0.0] * (len(stops_seq) - 1)
                
                for edge in edges:
                    from_idx = stop_to_index[edge.from_code]
                    to_idx = stop_to_index[edge.to_code]
                    departures[from_idx] = edge.depart
                    arrivals[to_idx] = edge.arrive
                    if from_idx < len(segment_distances):
                        segment_distances[from_idx] = edge.distance_km

                departures[-1] = arrivals[-1]
                arrivals[0] = departures[0]
                
                # Verify fully populated (since signature matched perfectly, this should always pass)
                if all(d is not None for d in departures) and all(a is not None for a in arrivals):
                    route_trips.append(
                        RouteTrip(
                            trip_id=edges[0].trip_id,
                            departures=departures,
                            arrivals=arrivals,
                            segment_distances=segment_distances,
                        )
                    )

            if not route_trips:
                continue

            # Limit trips per route just to keep memory sane
            if len(route_trips) > MAX_TRIPS_PER_ROUTE:
                route_trips.sort(key=lambda t: t.departures[0])
                route_trips = route_trips[:MAX_TRIPS_PER_ROUTE]

            line_name = self.line_names.get(sample_edge.line_id, sample_edge.line_id)
            routes[route_key] = RouteData(
                line_id=sample_edge.line_id,
                direction=sample_edge.direction,
                line_name=line_name,
                stops=list(stops_seq),
                stop_to_index=stop_to_index,
                trips=route_trips,
            )
            for stop in stops_seq:
                routes_by_stop[stop].add(route_key)

        self.routes = routes
        self.routes_by_stop = {stop: set(ids) for stop, ids in routes_by_stop.items()}
        planner_loader.build_boundary_sequence(self)

    # ---------- challenge planners ----------

    def _compute_challenges(self) -> dict[str, ChallengePlan | None]:
        """Computes all challenges in parallel by delegating to the specific planner modules."""

        challenge_definitions = [
            {
                "id": "longest-duration",
                "score_key": "duration",
                "title": "24時間ロングライド",
                "tagline": "博多から出発し24時間ひたすら乗り継ぎ続ける耐久チャレンジ。",
                "theme_tags": ["時間最大化", "耐久"],
                "badge": "最長乗車",
                "fallback": longest_duration.plan,
                "constraints": {"max_zone_visits": 8},
            },
            {
                "id": "most-stops",
                "score_key": "stops",
                "title": "ユニーク停留所コンプリート",
                "tagline": "24時間以内にできるだけ多くの停留所を踏破して博多へ戻るトレース。",
                "theme_tags": ["停留所制覇", "博多起終点"],
                "badge": "停留所ハンター",
                "fallback": most_stops.plan,
                "constraints": {"max_zone_visits": 12},
            },
            {
                "id": "city-loop",
                "score_key": "loop",
                "title": "福岡市一周トレース",
                "tagline": "市内の北東・南東・南西・北西ゾーンをすべて踏んで一筆書きで戻る。",
                "theme_tags": ["シティループ", "周回"],
                "badge": "周回達人",
                "fallback": city_loop.plan,
                "constraints": {
                    "max_zone_visits": 12,
                    "min_boundary_zones": 2,
                },
            },

            {
                "id": "ultimate-challenge",
                "score_key": "ultimate",
                "title": "究極の福岡バス制覇",
                "tagline": "福岡市の全境界を巡り、12時間以上乗り続ける究極のチャレンジ。",
                "theme_tags": ["究極", "境界制覇", "最長乗車"],
                "badge": "究極制覇者",
                "fallback": ultimate_challenge.plan,
                "constraints": {"max_zone_visits": 6, "require_quadrants": True},
            },
        ]

        # Directly use the specific planner for each challenge
        planners = {
            cfg["id"]: cfg["fallback"]
            for cfg in challenge_definitions
        }
        
        plans: dict[str, ChallengePlan | None] = {}
        with ThreadPoolExecutor(max_workers=len(planners)) as executor:
            future_to_challenge = {
                executor.submit(planner_func, self): challenge_id
                for challenge_id, planner_func in planners.items()
            }
            for future in future_to_challenge:
                challenge_id = future_to_challenge[future]
                normalized_id = self._normalize_challenge_id(challenge_id)
                try:
                    plan = future.result()
                    if plan:
                        plan.challenge_id = self._normalize_challenge_id(
                            plan.challenge_id
                        )
                    plans[normalized_id] = plan
                except Exception:
                    logger.exception(f"Error computing challenge '{challenge_id}'")
                    plans[normalized_id] = None
        return plans



    def run_beam_search(
        self,
        *,
        score_key: str,
        require_unique: bool,
        require_quadrants: bool,
        max_queue: int | None = None,
        max_expansions: int | None = None,
        max_branch: int | None = None,
        max_stop_visits: int | None = None,
        max_line_visits: int | None = None,
        min_transfer_minutes: int = TRANSFER_BUFFER_MINUTES,
        transfer_penalty_minutes: int = 0,
        stop_repeat_penalty_weight: int = 0,
        hakata_max_visits: int | None = None,
    ) -> SearchState | None:
        if not self.stop_schedules:
            raise PlannerError("Timetables are not loaded.")
        time_limit = START_TIME_MINUTES + 24 * 60
        pq: list[tuple[float, int, SearchState]] = []
        counter = 0
        queue_limit = max_queue or MAX_QUEUE_SIZE
        expansion_limit = max_expansions or MAX_EXPANSIONS
        branch_limit = max_branch or MAX_BRANCH_PER_EXPANSION
        stop_limit = max_stop_visits if max_stop_visits and max_stop_visits > 0 else None
        line_limit = max_line_visits if max_line_visits and max_line_visits > 0 else None

        cache_key = (
            score_key,
            require_unique,
            require_quadrants,
            max_queue,
            max_expansions,
            max_branch,
            stop_limit,
            line_limit,
            min_transfer_minutes,
            transfer_penalty_minutes,
            stop_repeat_penalty_weight,
            hakata_max_visits,
        )
        if cache_key in self._beam_cache:
            return self._beam_cache[cache_key]

        def push(state: SearchState, priority: float) -> None:
            nonlocal counter
            counter += 1
            if len(pq) >= queue_limit:
                heapq.heappushpop(pq, (priority, counter, state))
            else:
                heapq.heappush(pq, (priority, counter, state))

        best_key_score: dict[tuple[str, int], float] = {}
        results: list[SearchState] = []

        for stop_code in self.hakata_stops:
            mask = self.quadrant_map.get(stop_code, 0)
            initial_unique = 1 if require_unique else 0
            state = SearchState(
                priority=0.0,
                ride_minutes=0,
                current_time=START_TIME_MINUTES,
                stop_code=stop_code,
                path=(),
                unique_count=initial_unique,
                quadrant_mask=mask,
                stop_visit_counts={stop_code: 1},
                line_visit_counts={},
                transfers=0,
            )
            push(state, 0.0)

        expansions = 0
        while pq and expansions < expansion_limit:
            _priority, _, state = heapq.heappop(pq)
            expansions += 1
            
            if (
                state.path
                and state.stop_code in self.hakata_stops
                and state.current_time >= START_TIME_MINUTES + 120
            ):
                if not require_quadrants or state.quadrant_mask == 15:
                    results.append(state)
                    if score_key == "loop" and state.quadrant_mask == 15:
                        break

            next_edges = self._next_edges(
                state.stop_code,
                state.current_time + min_transfer_minutes,
                lookahead_minutes=MAX_LOOKAHEAD_MINUTES,
            )
            if not next_edges:
                continue

            for i, edge in enumerate(next_edges):
                if i >= branch_limit: break
                if edge.arrive > time_limit: continue

                if require_unique and edge.to_code in state.stop_visit_counts and not (edge.to_code in self.hakata_stops and state.path):
                    continue

                if stop_limit:
                    limit = hakata_max_visits if edge.to_code in self.hakata_stops and hakata_max_visits else stop_limit
                    if state.stop_visit_counts.get(edge.to_code, 0) >= limit:
                        continue
                
                new_stop_counts = dict(state.stop_visit_counts)
                new_stop_counts[edge.to_code] = new_stop_counts.get(edge.to_code, 0) + 1

                prev_edge = state.path[-1] if state.path else None
                is_new_trip = prev_edge is None or edge.trip_id != prev_edge.trip_id
                
                if line_limit and is_new_trip and state.line_visit_counts.get(edge.line_id, 0) >= line_limit:
                    continue

                new_line_counts = dict(state.line_visit_counts)
                if is_new_trip:
                    new_line_counts[edge.line_id] = new_line_counts.get(edge.line_id, 0) + 1

                next_state = SearchState(
                    priority=0.0,
                    ride_minutes=state.ride_minutes + edge.ride_minutes,
                    current_time=edge.arrive,
                    stop_code=edge.to_code,
                    path=state.path + (edge,),
                    unique_count=state.unique_count + (1 if require_unique and edge.to_code not in state.stop_visit_counts else 0),
                    quadrant_mask=state.quadrant_mask | self.quadrant_map.get(edge.to_code, 0),
                    stop_visit_counts=new_stop_counts,
                    line_visit_counts=new_line_counts,
                    transfers=state.transfers + (1 if is_new_trip and prev_edge is not None else 0),
                )
                score = self._score_state(
                    next_state,
                    score_key,
                    transfer_penalty_minutes,
                    stop_repeat_penalty_weight,
                )
                key = (edge.to_code, next_state.current_time // 30)
                if score > best_key_score.get(key, -1):
                    best_key_score[key] = score
                    push(next_state, -score)

        if not results:
            self._beam_cache[cache_key] = None
            return None
        
        scores = [
            (self._score_state(s, score_key, transfer_penalty_minutes, stop_repeat_penalty_weight), s)
            for s in results
        ]
        scores.sort(key=lambda t: t[0], reverse=True)
        best_state = scores[0][1]
        self._beam_cache[cache_key] = best_state
        return best_state

    def _next_edges(
        self, stop_code: str, earliest_depart: int, *, lookahead_minutes: int | None = None
    ) -> list[TripEdge]:
        schedule = self.stop_schedules.get(stop_code)
        if not schedule or not schedule.departures:
            return []
        idx = bisect_left(schedule.departures, earliest_depart)
        if lookahead_minutes is None:
            return schedule.edges[idx:]
        horizon = earliest_depart + lookahead_minutes
        edges = schedule.edges[idx:]
        clipped: list[TripEdge] = []
        for edge in edges:
            if edge.depart > horizon:
                break
            clipped.append(edge)
        return clipped

    def run_simple_raptor(
        self,
        origin: str,
        destination: str,
        depart_after: int,
        allowed_lines: set[str] | None = None,
        avoid_lines: set[str] | None = None,
    ) -> tuple[int, list[JourneyLeg]] | None:
        if not self.stop_schedules:
            return None
        if origin not in self.stop_schedules or destination not in self.stop_schedules:
            return None
        time_limit = START_TIME_MINUTES + 24 * 60
        earliest: dict[str, int] = {origin: depart_after}
        queue: list[tuple[int, str, tuple[JourneyLeg, ...]]] = []
        heapq.heappush(queue, (depart_after, origin, tuple()))

        visited_states = set()

        while queue:
            current_time, stop_code, path = heapq.heappop(queue)
            
            # Pruning: don't revisit same stop with same/worse time if path length is similar
            # simplified: just tracking best time at stop is in `earliest`
            known = earliest.get(stop_code, float("inf"))
            if current_time > known:
                continue
            
            if stop_code == destination and path:
                return current_time, list(path)
            if current_time >= time_limit:
                continue
            
            # Limit path depth to prevent infinite loops in restricted graphs
            if len(path) > 15:
                continue

            ready_time = current_time if not path else current_time + TRANSFER_BUFFER_MINUTES
            edges = self._next_edges(stop_code, ready_time)
            if not edges:
                continue
            
            for i, edge in enumerate(edges):
                if i >= 50: break # Increased lookahead slightly
                if edge.depart < ready_time: continue
                if edge.arrive > time_limit: break

                # --- Constraint Check ---
                # Extract route number from line_name (format: 西鉄バス・７・普通・...or 西鉄バス・66・普通・...)
                # The route number is the second segment after splitting by ・
                # Note: route numbers may be fullwidth (１２３) or halfwidth (123)
                route_number = None
                if edge.line_name:
                    parts = edge.line_name.split("・")
                    if len(parts) >= 2:
                        raw_num = parts[1]
                        # Normalize fullwidth digits to halfwidth
                        route_number = raw_num.translate(str.maketrans(
                            "０１２３４５６７８９",
                            "0123456789"
                        ))
                
                if allowed_lines is not None:
                    if route_number is None or route_number not in allowed_lines:
                        continue
                if avoid_lines is not None:
                    if route_number is not None and route_number in avoid_lines:
                        continue
                # ------------------------
                
                leg = JourneyLeg(
                    line_id=edge.line_id,
                    line_name=edge.line_name,
                    trip_id=edge.trip_id,
                    from_code=edge.from_code,
                    to_code=edge.to_code,
                    depart=edge.depart,
                    arrive=edge.arrive,
                    distance_km=edge.distance_km,
                    stop_hops=1,
                )
                new_time = edge.arrive
                prev_best = earliest.get(edge.to_code)
                
                # Allow slightly later arrival if it helps escape a trap, but generally strict
                if prev_best is None or new_time < prev_best:
                    earliest[edge.to_code] = new_time
                    heapq.heappush(queue, (new_time, edge.to_code, path + (leg,)))
        return None

    def _convert_journey_legs_to_trip_edges(self, journey_legs: list[JourneyLeg]) -> list[TripEdge]:
        """Converts a list of JourneyLegs to a list of TripEdges."""
        trip_edges = []
        for leg in journey_legs:
            metadata = self.trip_id_to_metadata.get(leg.trip_id)
            if not metadata:
                # This should not happen if the data is consistent
                logger.warning(f"Could not find metadata for trip_id {leg.trip_id}")
                continue

            from_station = self.stations.get(leg.from_code)
            to_station = self.stations.get(leg.to_code)
            if not from_station or not to_station:
                continue

            trip_edges.append(TripEdge(
                line_id=leg.line_id,
                line_name=leg.line_name,
                trip_id=leg.trip_id,
                direction=metadata["direction"],
                service_date=metadata["service_date"],
                from_code=leg.from_code,
                from_name=from_station.name,
                to_code=leg.to_code,
                to_name=to_station.name,
                depart=leg.depart,
                arrive=leg.arrive,
                distance_km=leg.distance_km,
                from_lat=from_station.lat,
                from_lon=from_station.lon,
                to_lat=to_station.lat,
                to_lon=to_station.lon,
            ))
        return trip_edges

    def get_station_distance(self, code_a: str, code_b: str) -> float:
        """Get cached distance between two stations."""
        if code_a == code_b:
            return 0.0
        
        # Use sorted tuple as key for symmetry
        key = tuple(sorted([code_a, code_b]))
        
        if key in self._distance_cache:
            return self._distance_cache[key]
        
        # Calculate and cache
        station_a = self.stations.get(code_a)
        station_b = self.stations.get(code_b)
        
        if not station_a or not station_b:
            return float('inf')
        
        from .planner_utils import distance_km as calc_distance_km
        dist = calc_distance_km(station_a.lat, station_a.lon, station_b.lat, station_b.lon)
        self._distance_cache[key] = dist
        return dist

    def _score_state(
        self,
        state: SearchState,
        key: str,
        transfer_penalty_minutes: int = 0,
        stop_repeat_penalty_weight: int = 0,
    ) -> float:
        line_ids = [edge.line_id for edge in state.path]
        unique_lines = len(set(line_ids))
        repeat_penalty = max(0, len(line_ids) - unique_lines)
        transfer_penalty_total = state.transfers * transfer_penalty_minutes
        stop_repeat = sum(max(0, count - 1) for count in state.stop_visit_counts.values())
        stop_repeat_penalty = stop_repeat * stop_repeat_penalty_weight

        base_score = 0.0
        if key == "loop":
            quadrants = bin(state.quadrant_mask).count("1")
            base_score = quadrants * 2000 + float(state.ride_minutes) + unique_lines * 15
        elif key == "unique":
            base_score = state.unique_count * 1200 + float(state.ride_minutes) + unique_lines * 12
        elif key == "distance":
            base_score = state.path[-1].distance_km * 1000 + float(state.ride_minutes) + unique_lines * 10
        elif key == "fastest":
            # Used by the fill stage to connect zones as quickly as possible.
            # No penalties, just pure speed.
            return -state.current_time
        else: # ride
            base_score = float(state.ride_minutes) + unique_lines * 10

        return base_score - repeat_penalty * (8 if key != "loop" else 4) - transfer_penalty_total - stop_repeat_penalty


        """
        Runs a challenge-aware beam search from a single origin to any stop in a destination zone.
        """
        if not self.stop_schedules:
            raise PlannerError("Timetables are not loaded.")
        
        dest_zone = self.hub_zones_by_id.get(destination_zone_id)
        if not dest_zone:
            raise PlannerError(f"Destination zone {destination_zone_id} not found.")
        
        destination_station_codes = {member['code'] for member in dest_zone['members']}
        
        time_limit = START_TIME_MINUTES + 24 * 60
        pq: list[tuple[float, int, SearchState]] = []
        counter = 0
        
        # Start from the provided base state
        initial_state = replace(
            base_state,
            current_time=depart_after,
            stop_code=origin_station_code,
        )
        
        # Push the initial state onto the priority queue
        initial_score = self._score_state(initial_state, score_key)
        heapq.heappush(pq, (-initial_score, counter, initial_state))

        best_key_score: dict[tuple[str, int], float] = {}
        results: list[SearchState] = []
        
        expansions = 0
        while pq and expansions < max_expansions:
            _priority, _, state = heapq.heappop(pq)
            expansions += 1

            # Termination condition: check if the current stop is in the destination zone
            if state.stop_code in destination_station_codes:
                results.append(state)
                # We can't stop here, a shorter path might lead to a better score later.
                # Let's continue searching until the queue is smaller or expansions run out.
                if len(results) > 10: # Keep a list of potential results
                    break
                continue

            # Only add a transfer buffer if we are actually transferring from another trip.
            ready_time = (
                state.current_time
                if not state.path
                else state.current_time + TRANSFER_BUFFER_MINUTES
            )
            next_edges = self._next_edges(state.stop_code, ready_time)
            if not next_edges:
                continue

            for i, edge in enumerate(next_edges):
                if i >= 30: break # Limit branching factor in this focused search
                if edge.arrive > time_limit: continue
                
                # Add budget constraint for the segment search
                if time_budget_minutes is not None and edge.arrive > depart_after + time_budget_minutes:
                    continue

                # Re-use logic from run_beam_search for expansion
                new_stop_counts = dict(state.stop_visit_counts)
                new_stop_counts[edge.to_code] = new_stop_counts.get(edge.to_code, 0) + 1

                prev_edge = state.path[-1] if state.path else None
                is_new_trip = prev_edge is None or edge.trip_id != prev_edge.trip_id
                
                new_line_counts = dict(state.line_visit_counts)
                if is_new_trip:
                    new_line_counts[edge.line_id] = new_line_counts.get(edge.line_id, 0) + 1

                next_state = SearchState(
                    priority=0.0,
                    ride_minutes=state.ride_minutes + edge.ride_minutes,
                    current_time=edge.arrive,
                    stop_code=edge.to_code,
                    path=state.path + (edge,),
                    unique_count=state.unique_count + (1 if edge.to_code not in state.stop_visit_counts else 0),
                    quadrant_mask=state.quadrant_mask | self.quadrant_map.get(edge.to_code, 0),
                    stop_visit_counts=new_stop_counts,
                    line_visit_counts=new_line_counts,
                    transfers=state.transfers + (1 if is_new_trip and prev_edge is not None else 0),
                )
                
                score = self._score_state(next_state, score_key)
                key = (edge.to_code, next_state.current_time // 15)
                if score > best_key_score.get(key, -1):
                    best_key_score[key] = score
                    counter += 1
                    heapq.heappush(pq, (-score, counter, next_state))

        if not results:
            return None
        
        # Return the best result found
        results.sort(key=lambda s: self._score_state(s, score_key), reverse=True)
        return results[0]

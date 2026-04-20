"""
Gemini API integration for intelligent route planning.
Uses Gemini to suggest station visit order, then validates with RAPTOR.

Gemini APIを使用したインテリジェントなルート計画。
Geminiが訪問順序を提案し、RAPTORで検証します。
"""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

if TYPE_CHECKING:
    from .planner import PlannerService
    from services.planner_models import ChallengePlan

logger = logging.getLogger(__name__)


# System prompt for Gemini
SYSTEM_PROMPT = """
あなたは福岡市の公共交通「西鉄バス」のルートプランナーです。
ユーザーの自然言語リクエストを**正確に解析**し、制約条件を構造化して出力してください。

【重要：制約条件の抽出と構造化】
ユーザーのリクエストから以下の制約を抽出し、constraintsオブジェクトに反映してください：

1. **路線制約 (allowed_lines / avoid_lines)**
   - 「1番から9番のバスだけ」→ allowed_lines: ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
   - 「一桁路線で」→ allowed_lines: ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
   - 「偶数番号の路線」→ allowed_lines: ["2", "4", "6", "8", ...]
   - 「高速バスは使わない」→ avoid_lines: ["高速", "急行", "特急"]
   - 「100番台の路線」→ allowed_lines: ["100", "101", "102", ...]

2. **エリア制約 (preferred_areas)**
   - 「海沿いを走りたい」→ preferred_areas: ["志賀島", "糸島", "海の中道", "百道"]
   - 「山の方に行きたい」→ preferred_areas: ["脊振", "曲渕", "早良区南部"]
   - 「天神周辺」→ preferred_areas: ["天神", "渡辺通", "薬院"]

3. **徒歩オプション (allow_walking / max_walking_km)**
   - デフォルト: allow_walking: true, max_walking_km: 2.0
   - 「歩きたくない」→ allow_walking: false
   - 「5kmくらいなら歩ける」→ max_walking_km: 5.0

4. **ルート特性 (route_preference)**
   - 「できるだけ長く乗りたい」→ route_preference: "long_distance"
   - 「乗り換えを減らして」→ route_preference: "minimal_transfer"
   - 「挑戦的なルート」→ route_preference: "challenging"

【停留所選択ルール】
- 停留所名は提供リストから「完全一致」で選んでください
- 路線情報（[路線: 1, 7]など）を参考に、制約を満たす停留所を優先選択
- ルートは出発地に戻る循環ルート（Start == End）

【福岡市の地理参考】
- 都心：博多駅・天神・薬院・渡辺通
- 海沿い：志賀島・糸島・海の中道・百道
- 山間部：早良区南部・脊振・曲渕
- 郊外：西区・東区・城南区南部
"""

USER_PROMPT_TEMPLATE = """
ユーザーのリクエスト: {goal}

【ステップ1: リクエストから制約を抽出】
上記リクエストを分析し、以下を特定してください：
- 路線の制限（allowed_lines / avoid_lines）
- エリアの指定（preferred_areas）
- 徒歩の可否（allow_walking / max_walking_km）
- ルート特性（route_preference）

【ステップ2: 利用可能な停留所リスト】
以下のリストから、制約を満たす停留所を選んでください：
{available_stops}

【ステップ3: JSON形式で出力】
{{
  "route_name": "ルート名（ユーザーのテーマを反映）",
  "description": "ルートの特徴（50文字以内）",
  "stops": ["出発地", "経由地1", "経由地2", ..., "出発地"],
  "estimated_hours": 所要時間,
  "constraints": {{
    "allowed_lines": [],      // 使用可能な路線番号（空=制限なし）
    "avoid_lines": [],        // 禁止する路線（空=制限なし）
    "preferred_areas": [],    // 優先エリア名（空=制限なし）
    "allow_walking": true,    // 徒歩を許可するか
    "max_walking_km": 2.0,    // 最大徒歩距離(km)
    "route_preference": null  // "long_distance" / "minimal_transfer" / "challenging"
  }}
}}

【制約抽出の例】
- 「一桁番号のバスで」→ allowed_lines: ["1","2","3","4","5","6","7","8","9"]
- 「高速は使わない」→ avoid_lines: ["高速","急行","特急"]
- 「海沿いルート」→ preferred_areas: ["志賀島","糸島","百道"]
- 「歩きたくない」→ allow_walking: false
- 「長距離で」→ route_preference: "long_distance"

【重要】stopsには上記リストの停留所名を「完全一致」で使用してください。
"""


def is_gemini_available() -> bool:
    """Check if Gemini API is available."""
    if not GEMINI_AVAILABLE:
        return False
    api_key = os.environ.get("GEMINI_API_KEY")
    return bool(api_key)


def generate_route_suggestion(
    service: "PlannerService",
    user_goal: str,
) -> dict | None:
    """
    Use Gemini to generate a station visit sequence based on user's goal.
    ユーザーの目標に基づいて、Geminiで訪問順序を生成します。
    
    Args:
        service: The PlannerService instance with station data
        user_goal: Natural language description of what the user wants
        
    Returns:
        Dictionary with route_name, description, stops, or None if failed
    """
    if not GEMINI_AVAILABLE:
        logger.warning("Gemini not available: google-generativeai package not installed")
        return None
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("Gemini API key not found in environment")
        return None
    
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to configure Gemini: {e}")
        return None
    
    # Build station list with route information
    # For each station, include which route numbers serve it
    station_routes: dict[str, set[str]] = {}
    
    for code, sched in service.stop_schedules.items():
        station = service.stations.get(code)
        if not station:
            continue
        station_name = station.name
        if station_name not in station_routes:
            station_routes[station_name] = set()
        
        for edge in sched.edges:
            if edge.line_name:
                parts = edge.line_name.split("・")
                if len(parts) >= 2:
                    raw_num = parts[1]
                    # Normalize fullwidth to halfwidth
                    route_num = raw_num.translate(str.maketrans(
                        "０１２３４５６７８９",
                        "0123456789"
                    ))
                    station_routes[station_name].add(route_num)
    
    # Format: "Station Name (routes: 1, 7, 9)" or "Station Name" if too many routes
    major_stops = []
    for name, routes in sorted(station_routes.items()):
        single_digit = [r for r in routes if r.isdigit() and len(r) == 1]
        if single_digit:
            # Highlight stations with single-digit routes
            major_stops.append(f"{name} [路線: {', '.join(sorted(single_digit))}]")
        elif len(routes) <= 5:
            major_stops.append(f"{name} [路線: {', '.join(sorted(routes)[:5])}]")
        else:
            # Too many routes, just show the station name
            major_stops.append(name)
    
    # Build the prompt
    stops_list = "\n".join(f"- {entry}" for entry in major_stops)
    user_message = USER_PROMPT_TEMPLATE.format(
        goal=user_goal,
        available_stops=stops_list,
    )
    
    try:
        model = genai.GenerativeModel("gemini-3-flash-preview")
        response = model.generate_content([SYSTEM_PROMPT, user_message])
        
        # Parse JSON from response
        text = response.text
        start = text.find("{")
        end = text.rfind("}") + 1
        
        if start >= 0 and end > start:
            result = json.loads(text[start:end])
            logger.info(f"Gemini suggested route: {result.get('route_name')}")
            return result
        else:
            logger.warning("Gemini response did not contain valid JSON")
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None


def resolve_fuzzy_station_names(
    fuzzy_names: list[str],
    all_station_names: list[str],
) -> list[str]:
    """
    Use smart matching to map fuzzy station names to exact station names.
    スマートマッチングで曖昧な駅名を正確な駅名にマッピングします。
    """
    from difflib import get_close_matches
    
    if len(all_station_names) == 0:
        logger.warning("resolve_fuzzy_station_names called with empty station list!")
    
    # Pre-process: create lookup without suffix
    names_without_suffix = {n.replace("／西鉄バス", ""): n for n in all_station_names}
    
    def normalize_for_matching(name: str) -> str:
        """Normalize name for better matching."""
        # Remove common suffixes and prefixes
        n = name.replace("／西鉄バス", "")
        # Convert fullwidth to halfwidth
        for fw, hw in [("Ａ", "A"), ("Ｂ", "B"), ("Ｃ", "C"), ("Ｄ", "D"), ("Ｅ", "E"), ("Ｆ", "F"),
                       ("（", "("), ("）", ")"), ("・", "")]:
            n = n.replace(fw, hw)
        return n
    
    def find_best_match(fuzzy_name: str) -> str | None:
        # Normalize the fuzzy name
        fuzzy_norm = normalize_for_matching(fuzzy_name)
        
        # 1. Exact match with suffix
        with_suffix = f"{fuzzy_name}／西鉄バス"
        if with_suffix in all_station_names:
            return with_suffix
        
        # 2. Exact match in names_without_suffix
        if fuzzy_name in names_without_suffix:
            return names_without_suffix[fuzzy_name]
        
        # 3. Try normalized matching
        for name_no_suffix, full_name in names_without_suffix.items():
            name_norm = normalize_for_matching(name_no_suffix)
            if fuzzy_norm == name_norm:
                return full_name
        
        # 4. Substring match - find stations containing the query
        matches = []
        for name_no_suffix, full_name in names_without_suffix.items():
            if fuzzy_norm in name_no_suffix or name_no_suffix.startswith(fuzzy_norm):
                matches.append((len(name_no_suffix), full_name))
        if matches:
            # Return shortest match (most specific)
            matches.sort()
            return matches[0][1]
        
        # 5. Extract core keyword and search
        # e.g., "博多駅前A" -> try to find anything with "博多駅"
        core = fuzzy_norm.rstrip("ABCDEF0123456789前口")
        if len(core) >= 2:
            for name_no_suffix, full_name in names_without_suffix.items():
                if core in name_no_suffix:
                    return full_name
        
        # 6. Use difflib as last resort with very low cutoff
        names_list = list(names_without_suffix.keys())
        matches = get_close_matches(fuzzy_norm, names_list, n=1, cutoff=0.3)
        if matches:
            return names_without_suffix[matches[0]]
        
        return None
    
    resolved = []
    for fuzzy_name in fuzzy_names:
        match = find_best_match(fuzzy_name)
        if match:
            resolved.append(match)
            logger.info(f"Matched: '{fuzzy_name}' -> '{match}'")
        else:
            logger.warning(f"Could not match station: '{fuzzy_name}'")
    
    return resolved


def validate_and_build_route(
    service: "PlannerService",
    suggested_stops: list[str],
    route_name: str = "カスタムルート",
    description: str = "AIが提案したルート",
    constraints: dict | None = None,
    start_station_code: str | None = None,
) -> "ChallengePlan | None":
    """
    Validate the Gemini-suggested stops using RAPTOR and build actual route.
    Geminiが提案した停留所をRAPTORで検証し、実際のルートを構築します。
    
    Args:
        service: The PlannerService instance
        suggested_stops: List of station names suggested by Gemini
        route_name: Name for the generated route
        description: Description for the generated route
        constraints: Optional set of constraints (allowed_lines, avoid_lines)
        start_station_code: Optional station code to use as start/end point (from user location)
        
    Returns:
        ChallengePlan if successful, None otherwise
    """
    from services.planner_models import ChallengePlan, LegPlan
    from services.planner_utils import derive_quadrant_labels
    from services.planner_constants import START_TIME_MINUTES
    
    # Parse constraints
    allowed_lines = None
    avoid_lines = None
    allow_walking = True  # Default: walking allowed
    max_walking_km = 2.0  # Default: 2km max
    route_preference = None
    preferred_areas = None
    
    if constraints:
        # Route line constraints
        if constraints.get("allowed_lines"):
            try:
                allowed_lines = set(str(x) for x in constraints["allowed_lines"])
            except Exception:
                pass
        if constraints.get("avoid_lines"):
            try:
                avoid_lines = set(str(x) for x in constraints["avoid_lines"])
            except Exception:
                pass
        
        # Walking constraints
        if "allow_walking" in constraints:
            allow_walking = bool(constraints["allow_walking"])
        if "max_walking_km" in constraints:
            try:
                max_walking_km = float(constraints["max_walking_km"])
            except (ValueError, TypeError):
                pass
        
        # Route preference
        if constraints.get("route_preference"):
            route_preference = str(constraints["route_preference"])
        
        # Area preference
        if constraints.get("preferred_areas"):
            try:
                preferred_areas = list(constraints["preferred_areas"])
            except Exception:
                pass
            
    # Log applied constraints
    if allowed_lines:
        logger.info(f"Applying allowed_lines constraint: {allowed_lines}")
    if avoid_lines:
        logger.info(f"Applying avoid_lines constraint: {avoid_lines}")
    if not allow_walking:
        logger.info("Walking disabled by constraint")
    if max_walking_km != 2.0:
        logger.info(f"Max walking distance: {max_walking_km}km")
    if route_preference:
        logger.info(f"Route preference: {route_preference}")
    if preferred_areas:
        logger.info(f"Preferred areas: {preferred_areas}")
    
    # First, resolve fuzzy station names to exact names
    all_station_names = [station.name for station in service.stations.values()]
    resolved_stops = resolve_fuzzy_station_names(suggested_stops, all_station_names)
    logger.info(f"Resolved stops: {resolved_stops}")
    
    # Normalize function for full-width/half-width character matching
    def normalize_name(name: str) -> str:
        """Normalize station name: remove suffix, convert fullwidth to halfwidth."""
        # Remove common suffixes
        normalized = name.replace("／西鉄バス", "")
        # Convert fullwidth alphanumerics to halfwidth
        result = []
        for c in normalized:
            code = ord(c)
            # Fullwidth A-Z (Ａ-Ｚ) -> A-Z
            if 0xFF21 <= code <= 0xFF3A:
                result.append(chr(code - 0xFF21 + ord('A')))
            # Fullwidth a-z (ａ-ｚ) -> a-z
            elif 0xFF41 <= code <= 0xFF5A:
                result.append(chr(code - 0xFF41 + ord('a')))
            # Fullwidth 0-9 (０-９) -> 0-9
            elif 0xFF10 <= code <= 0xFF19:
                result.append(chr(code - 0xFF10 + ord('0')))
            else:
                result.append(c)
        return ''.join(result)
    
    # Build name to code mapping with multiple index keys
    name_to_code: dict[str, str] = {}
    for code, station in service.stations.items():
        name = station.name
        name_to_code[name] = code
        # Also index by partial names for fuzzy matching
        if "／" in name:
            short_name = name.split("／")[0]
            if short_name not in name_to_code:
                name_to_code[short_name] = code
        # Remove common suffixes for matching
        for suffix in ["駅", "駅前", "駅北口", "駅南口", "駅東口", "駅西口", "バス停", "前"]:
            if name.endswith(suffix) and len(name) > len(suffix):
                base = name[:-len(suffix)]
                if base not in name_to_code:
                    name_to_code[base] = code
    
    # Build normalized name lookup for better matching
    normalized_to_code: dict[str, str] = {}
    for name, code in name_to_code.items():
        norm = normalize_name(name)
        if norm not in normalized_to_code:
            normalized_to_code[norm] = code
    
    def find_station_code(query: str) -> str | None:
        """Find station code with fuzzy matching."""
        # Exact match
        if query in name_to_code:
            return name_to_code[query]
        
        # Try normalized match (handles fullwidth/halfwidth differences)
        query_norm = normalize_name(query)
        if query_norm in normalized_to_code:
            return normalized_to_code[query_norm]
        
        # Try removing common suffixes from query
        query_normalized = query_norm
        for suffix in ["駅前", "駅北口", "駅南口", "駅東口", "駅西口", "バス停", "駅", "前"]:
            if query_norm.endswith(suffix):
                query_normalized = query_norm[:-len(suffix)]
                if query_normalized in normalized_to_code:
                    return normalized_to_code[query_normalized]
                break
        
        # Try contains match (both directions) using normalized names
        best_match = None
        best_score = 0
        for norm_name, code in normalized_to_code.items():
            # Query contains station name or station name contains query
            if query_norm in norm_name or norm_name in query_norm:
                score = len(norm_name) if query_norm in norm_name else len(query_norm)
                if score > best_score:
                    best_score = score
                    best_match = code
            # Also try startswith
            elif norm_name.startswith(query_normalized) or query_normalized.startswith(norm_name):
                score = min(len(norm_name), len(query_normalized))
                if score > best_score:
                    best_score = score
                    best_match = code
        
        return best_match
    
    # Convert station names to codes (use resolved names)
    stop_codes: list[str] = []
    unmatched: list[str] = []
    
    for name in resolved_stops:
        code = find_station_code(name)
        if code:
            stop_codes.append(code)
        else:
            unmatched.append(name)
    
    if unmatched:
        logger.warning(f"Could not find stations: {unmatched}")
    
    if len(stop_codes) < 2:
        logger.error("Not enough valid stations to build route")
        return None
    
    # Determine start/end station
    # Priority: 1) start_station_code (user location) 2) Hakata 3) Gemini's choice
    route_start_code = start_station_code  # From user location
    if not route_start_code and service.hakata_stops:
        route_start_code = service.hakata_stops[0]  # Default to Hakata
    
    # Ensure route ends at start station (circular route)
    if route_start_code and stop_codes[-1] != route_start_code:
        stop_codes.append(route_start_code)
    
    # Ensure route starts at start station
    if route_start_code and stop_codes[0] != route_start_code:
        stop_codes.insert(0, route_start_code)
    
    logger.info(f"Building route with {len(stop_codes)} waypoints")
    
    # Build route segment by segment using simple RAPTOR
    all_legs: list[LegPlan] = []
    current_time = START_TIME_MINUTES
    
    for i in range(len(stop_codes) - 1):
        origin = stop_codes[i]
        destination = stop_codes[i + 1]
        
        # Try with constraints first
        result = service.run_simple_raptor(
            origin, 
            destination, 
            current_time,
            allowed_lines=allowed_lines,
            avoid_lines=avoid_lines
        )
        
        # If constrained route fails, try to add walking segment instead of fallback
        if not result and (allowed_lines or avoid_lines):
            # Check if walking is allowed
            if not allow_walking:
                logger.warning(f"Skipping segment {origin} -> {destination} - no compliant route and walking disabled")
                continue
            
            # Calculate walking distance between origin and destination
            origin_station = service.stations.get(origin)
            dest_station = service.stations.get(destination)
            
            if origin_station and dest_station:
                from math import radians, cos, sin, sqrt, atan2
                # Haversine formula for distance
                R = 6371  # Earth radius in km
                lat1, lon1 = radians(origin_station.lat), radians(origin_station.lon)
                lat2, lon2 = radians(dest_station.lat), radians(dest_station.lon)
                dlat, dlon = lat2 - lat1, lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
                c = 2*atan2(sqrt(a), sqrt(1-a))
                walking_distance_km = R * c
                
                # Use dynamic max_walking_km from constraints
                WALKING_SPEED_KPH = 5.0  # Average walking speed
                
                if walking_distance_km <= max_walking_km:
                    # Create walking leg
                    walking_minutes = int(walking_distance_km / WALKING_SPEED_KPH * 60)
                    walking_leg = LegPlan(
                        line_id="WALK",
                        line_name="徒歩",
                        trip_id="WALK",
                        from_code=origin,
                        from_name=origin_station.name,
                        to_code=destination,
                        to_name=dest_station.name,
                        depart=current_time,
                        arrive=current_time + walking_minutes,
                        ride_minutes=walking_minutes,
                        distance_km=round(walking_distance_km, 2),
                        stop_hops=0,
                        path=[(origin_station.lat, origin_station.lon), (dest_station.lat, dest_station.lon)],
                        from_lat=origin_station.lat,
                        from_lon=origin_station.lon,
                        to_lat=dest_station.lat,
                        to_lon=dest_station.lon,
                    )
                    all_legs.append(walking_leg)
                    current_time += walking_minutes
                    logger.info(f"Added walking segment {origin_station.name} -> {dest_station.name} ({walking_distance_km:.1f}km, {walking_minutes}min)")
                    continue
                else:
                    logger.warning(f"Walking distance too far ({walking_distance_km:.1f}km > {max_walking_km}km) for {origin} -> {destination}")
            
            # If walking not possible, skip this segment entirely (don't use non-compliant bus)
            logger.warning(f"Skipping segment {origin} -> {destination} - no compliant route and walking not possible")
            continue
            
        if not result:
            logger.warning(f"Could not find route from {origin} to {destination}")
            continue
        
        arrival_time, journey_legs = result
        
        # Convert journey legs to leg plans
        from services.planner_utils import label_leg_to_plan
        for leg in journey_legs:
            leg_plan = label_leg_to_plan(leg, service.stations)
            all_legs.append(leg_plan)
        
        current_time = arrival_time
    
    if not all_legs:
        logger.error("Could not build any route segments")
        return None
    
    # === Fetch actual route shapes from Mixway API ===
    try:
        from services.shape_fetcher import MixwayShapeFetcher
        mixway_api_key = os.environ.get("MIXWAY_API_KEY")
        if mixway_api_key:
            shape_fetcher = MixwayShapeFetcher(mixway_api_key, use_cache=True)
            enriched_legs = []
            for leg in all_legs:
                # Fetch shape for this leg
                try:
                    from services.planner_utils import format_minutes
                    departure_str = format_minutes(leg.depart)
                    coords = shape_fetcher.fetch_leg_shape(
                        leg.from_code,
                        leg.to_code,
                        departure_str
                    )
                    if coords and len(coords) >= 2:
                        # Update path with actual geometry
                        new_path = [(c["lat"], c["lon"]) for c in coords]
                        # Create new LegPlan with updated path
                        enriched_leg = LegPlan(
                            line_id=leg.line_id,
                            line_name=leg.line_name,
                            trip_id=leg.trip_id,
                            from_code=leg.from_code,
                            from_name=leg.from_name,
                            to_code=leg.to_code,
                            to_name=leg.to_name,
                            depart=leg.depart,
                            arrive=leg.arrive,
                            ride_minutes=leg.ride_minutes,
                            distance_km=leg.distance_km,
                            stop_hops=leg.stop_hops,
                            path=new_path,
                            from_lat=leg.from_lat,
                            from_lon=leg.from_lon,
                            to_lat=leg.to_lat,
                            to_lon=leg.to_lon,
                        )
                        enriched_legs.append(enriched_leg)
                        logger.info(f"Enriched leg {leg.from_code}->{leg.to_code} with {len(new_path)} coordinates")
                    else:
                        enriched_legs.append(leg)  # Keep original if no shape found
                except Exception as shape_err:
                    logger.warning(f"Shape fetch failed for {leg.from_code}->{leg.to_code}: {shape_err}")
                    enriched_legs.append(leg)
            all_legs = enriched_legs
            logger.info(f"Shape enrichment complete for {len(all_legs)} legs")
        else:
            logger.info("MIXWAY_API_KEY not set, skipping shape enrichment")
    except ImportError:
        logger.warning("MixwayShapeFetcher not available, skipping shape enrichment")
    except Exception as e:
        logger.warning(f"Shape enrichment failed: {e}")
    # === End shape fetching ===
    
    start_name = (
        service.stations[service.hakata_stops[0]].name
        if service.hakata_stops and service.hakata_stops[0] in service.stations
        else "博多駅"
    )
    
    plan = ChallengePlan(
        challenge_id="custom-ai-route",
        title=route_name,
        tagline=description,
        theme_tags=["AI生成", "カスタム"],
        badge="AI Route",
        legs=all_legs,
        start_stop_name=start_name,
        wards=derive_quadrant_labels(all_legs, service.quadrant_map),
        stations=service.stations,
    )
    
    return plan


def generate_one_stroke_route(
    service: "PlannerService",
) -> "ChallengePlan | None":
    """
    Generate a "one-stroke" (一笔画) route that covers as much of Fukuoka as possible
    without repeating stations.
    福岡市内をできるだけ広くカバーする一筆書きルートを生成します。
    """
    goal = """
    福岡市内を一筆書きで巡るルートを提案してください。
    条件：
    - 博多駅から出発して博多駅に戻る
    - できるだけ広い範囲をカバーする
    - 東区、西区、南区、中央区すべてを通る
    - 同じ場所は二度通らない
    - 24時間以内で達成可能な現実的なルート
    """
    
    suggestion = generate_route_suggestion(service, goal)
    if not suggestion:
        return None
    
    return validate_and_build_route(
        service,
        suggestion.get("stops", []),
        route_name=suggestion.get("route_name", "一筆書きチャレンジ"),
        description=suggestion.get("description", "AIが提案した一筆書きルート"),
    )


def generate_custom_challenge(
    service: "PlannerService",
    user_goal: str,
    user_location: tuple[float, float] | None = None,
) -> "ChallengePlan | None":
    """
    Generate a custom challenge route based on user's natural language goal.
    ユーザーの自然言語の目標に基づいてカスタムチャレンジルートを生成します。
    
    Args:
        service: The PlannerService instance
        user_goal: Natural language description (e.g., "東西南北の端をすべてタッチ")
        user_location: Optional (lat, lon) tuple of user's current location
        
    Returns:
        ChallengePlan if successful, None otherwise
    """
    suggestion = generate_route_suggestion(service, user_goal)
    if not suggestion:
        return None
    
    # Find nearest station if user_location provided
    start_station_code = None
    if user_location:
        from math import radians, cos, sin, sqrt, atan2
        user_lat, user_lon = user_location
        
        best_dist = float('inf')
        best_code = None
        
        # Haversine formula to find nearest station
        R = 6371  # Earth radius in km
        for code, station in service.stations.items():
            lat1, lon1 = radians(user_lat), radians(user_lon)
            lat2, lon2 = radians(station.lat), radians(station.lon)
            dlat, dlon = lat2 - lat1, lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
            c = 2*atan2(sqrt(a), sqrt(1-a))
            dist = R * c
            
            if dist < best_dist:
                best_dist = dist
                best_code = code
        
        if best_code and best_dist <= 5.0:  # Within 5km
            start_station_code = best_code
            logger.info(f"Found nearest station: {service.stations[best_code].name} ({best_dist:.2f}km away)")
    
    return validate_and_build_route(
        service,
        suggestion.get("stops", []),
        route_name=suggestion.get("route_name", "カスタムチャレンジ"),
        description=suggestion.get("description", user_goal[:50]),
        constraints=suggestion.get("constraints"),
        start_station_code=start_station_code,
    )


# ===== Route Metadata Generation =====
# ルートメタデータ生成

ROUTE_NAMING_PROMPT = """
あなたはバス旅行のエキスパートです。
以下のルートデータを分析し、ルートの特徴に合った魅力的なタイトルと説明文を日本語で生成してください。

ルートデータ:
- 総乗車時間: {ride_minutes}分 ({hours}時間{mins}分)
- 総距離: {distance_km} km
- 乗り換え回数: {transfers}回
- 訪問した停留所数: {total_stops}箇所
- 開始停留所: {start_stop}
- 終了停留所: {end_stop}
- 主要な経由地: {key_stops}
- カバーエリア: {areas}

重要: タイトルと説明は実際のルート特性を正確に反映してください。
例えば、8時間のルートを「24時間チャレンジ」と呼ばないでください。

JSON形式で返してください:
{{
  "title": "タイトル（日本語、15文字以内）",
  "tagline": "説明文（日本語、50文字以内、ルートの魅力を伝える）",
  "theme_tags": ["タグ1", "タグ2"],
  "badge": "バッジ名（達成感を示す短い言葉）"
}}
"""


def generate_route_metadata(route_data: dict) -> dict | None:
    """
    Use Gemini to analyze route data and generate appropriate title and description.
    Geminiを使用してルートデータを分析し、適切なタイトルと説明を生成します。
    
    Args:
        route_data: Route dictionary with legs, total_ride_minutes, etc.
        
    Returns:
        Dictionary with title, tagline, theme_tags, badge, or None if failed
    """
    if not GEMINI_AVAILABLE:
        logger.warning("Gemini not available for route naming")
        return None
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("Gemini API key not found for route naming")
        return None
    
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to configure Gemini for naming: {e}")
        return None
    
    # Extract route characteristics
    ride_minutes = route_data.get("total_ride_minutes", 0)
    hours = ride_minutes // 60
    mins = ride_minutes % 60
    distance_km = route_data.get("total_distance_km", 0)
    transfers = route_data.get("transfers", 0)
    legs = route_data.get("legs", [])
    total_stops = len(set(leg.get("from_code", "") for leg in legs) | set(leg.get("to_code", "") for leg in legs))
    
    start_stop = legs[0].get("from_stop", "不明") if legs else "不明"
    end_stop = legs[-1].get("to_stop", "不明") if legs else "不明"
    
    # Get key stops (first, middle, last few)
    key_stops_set = set()
    if legs:
        key_stops_set.add(legs[0].get("from_stop", ""))
        key_stops_set.add(legs[-1].get("to_stop", ""))
        mid_idx = len(legs) // 2
        if mid_idx > 0:
            key_stops_set.add(legs[mid_idx].get("from_stop", ""))
        for i in range(min(3, len(legs))):
            key_stops_set.add(legs[i].get("to_stop", ""))
    key_stops = ", ".join(list(key_stops_set)[:5])
    
    areas = route_data.get("wards", ["福岡市内"])
    areas_str = ", ".join(areas) if isinstance(areas, list) else str(areas)
    
    # Build the prompt
    prompt = ROUTE_NAMING_PROMPT.format(
        ride_minutes=ride_minutes,
        hours=hours,
        mins=mins,
        distance_km=distance_km,
        transfers=transfers,
        total_stops=total_stops,
        start_stop=start_stop,
        end_stop=end_stop,
        key_stops=key_stops,
        areas=areas_str,
    )
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(prompt)
        
        # Parse JSON from response
        text = response.text
        start = text.find("{")
        end = text.rfind("}") + 1
        
        if start >= 0 and end > start:
            result = json.loads(text[start:end])
            logger.info(f"Gemini generated route name: {result.get('title')}")
            return result
        else:
            logger.warning("Gemini naming response did not contain valid JSON")
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini naming response: {e}")
        return None
    except Exception as e:
        logger.error(f"Gemini naming API error: {e}")
        return None


def enhance_route_with_metadata(route_data: dict) -> dict:
    """
    Enhance a route with Gemini-generated metadata.
    If Gemini is not available or fails, returns the original route unchanged.
    
    ルートにGemini生成のメタデータを追加します。
    Geminiが利用できない場合や失敗した場合は、元のルートをそのまま返します。
    """
    metadata = generate_route_metadata(route_data)
    if metadata:
        route_data["title"] = metadata.get("title", route_data.get("title"))
        route_data["tagline"] = metadata.get("tagline", route_data.get("tagline"))
        route_data["theme_tags"] = metadata.get("theme_tags", route_data.get("theme_tags", []))
        route_data["badges"] = [metadata.get("badge")] if metadata.get("badge") else route_data.get("badges", [])
    return route_data


def regenerate_all_metadata(routes_dir: str) -> dict:
    """
    Regenerate metadata for all route JSON files in a directory.
    ディレクトリ内のすべてのルートJSONファイルのメタデータを再生成します。
    
    Args:
        routes_dir: Path to directory containing route JSON files
        
    Returns:
        Dictionary with results for each file
    """
    from pathlib import Path
    
    results = {}
    routes_path = Path(routes_dir)
    
    if not routes_path.exists():
        return {"error": f"Directory not found: {routes_dir}"}
    
    for json_file in routes_path.glob("raptor_debug_*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                route_data = json.load(f)
            
            original_title = route_data.get("title", "Unknown")
            enhanced = enhance_route_with_metadata(route_data)
            
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(enhanced, f, ensure_ascii=False, indent=2)
            
            results[json_file.name] = {
                "status": "success",
                "original_title": original_title,
                "new_title": enhanced.get("title"),
                "new_tagline": enhanced.get("tagline"),
            }
        except Exception as e:
            results[json_file.name] = {
                "status": "error",
                "error": str(e),
            }
    
    return results

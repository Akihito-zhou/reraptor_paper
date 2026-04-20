from __future__ import annotations

import math
from collections import Counter
from datetime import datetime
from typing import Sequence

from .planner_constants import REST_SUGGESTIONS, REST_STOP_THRESHOLD
from .planner_models import LegPlan, TripEdge


def is_in_fukuoka(lat: float, lon: float, fukuoka_polygons: list[list[list[float]]]) -> bool:
    """
    Checks if a point is inside any of the Fukuoka city polygons using the Ray Casting algorithm.
    A point is in a polygon if a line from the point to infinity crosses the polygon edge an odd number of times.
    
    IMPORTANT: Coordinate System Note
    - Input parameters: (lat, lon) - Standard Python order
    - GeoJSON format: [lon, lat] - GeoJSON standard (lon first!)
    - This function correctly handles the conversion when unpacking polygon coordinates
    """
    inside = False
    for polygon in fukuoka_polygons:
        # Check each polygon
        is_inside_polygon = False
        for i in range(len(polygon)):
            p1_lon, p1_lat = polygon[i]
            p2_lon, p2_lat = polygon[i - 1] # Wraps around to the last vertex

            # Check if the point is on a horizontal polygon segment
            if p1_lat == p2_lat == lat and min(p1_lon, p2_lon) <= lon <= max(p1_lon, p2_lon):
                return True
            
            # Check if the point is on a vertical polygon segment
            if p1_lon == p2_lon == lon and min(p1_lat, p2_lat) <= lat <= max(p1_lat, p2_lat):
                return True

            # Ray casting algorithm
            if (p1_lat > lat) != (p2_lat > lat):
                # Calculate the x-intersection of the line segment with the ray
                intersect_lon = (p2_lon - p1_lon) * (lat - p1_lat) / (p2_lat - p1_lat) + p1_lon
                if lon < intersect_lon:
                    is_inside_polygon = not is_inside_polygon
        
        if is_inside_polygon:
            inside = True
            break # No need to check other polygons if it's inside one
            
    return inside


def haversine_km(a, b) -> float:
    """计算两个站点间的大圆距离 / 2地点間の大円距離を計算する。"""
    r = 6371.0
    lat1 = math.radians(a.lat)
    lat2 = math.radians(b.lat)
    dlat = lat2 - lat1
    dlon = math.radians(b.lon - a.lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def format_minutes(total_minutes: int) -> str:
    """把分钟数格式化为时刻字符串 / 分単位を時刻文字列に整形する。"""
    if total_minutes < 0:
        total_minutes = 0
    days, minutes = divmod(total_minutes, 1440)
    hours, mins = divmod(minutes, 60)
    base = f"{hours:02d}:{mins:02d}"
    if days == 0:
        return base
    return f"+{days}d {base}"


def generate_rest_stops(
    legs: Sequence[LegPlan],
    stations: dict[str, "Station"] | None = None,
) -> list[dict]:
    """
    根据停留间隔和附近POI生成休息建议（每个时间段最多1个）。
    区間の待ち時間と周辺POIに応じて休憩案を生成する（時間帯ごとに最大1つ）。
    """
    from .planner_constants import DATA_DIR
    import json
    
    # Time periods covering the full day (max 1 rest stop per period)
    TIME_PERIODS = [
        ("early_morning", 6 * 60, 8 * 60, None),     # 6:00-8:00
        ("morning", 8 * 60, 10 * 60, None),          # 8:00-10:00
        ("late_morning", 10 * 60, 11 * 60, None),    # 10:00-11:00
        ("lunch", 11 * 60, 14 * 60, "lunch"),        # 11:00-14:00
        ("afternoon", 14 * 60, 17 * 60, None),       # 14:00-17:00
        ("dinner", 17 * 60, 20 * 60, "dinner"),      # 17:00-20:00
        ("evening", 20 * 60, 24 * 60, None),         # 20:00-24:00
    ]
    
    used_periods: set[str] = set()
    
    # Load OSM POI data
    rest_points_path = DATA_DIR / "generated" / "rest_points.json"
    pois: list[dict] = []
    if rest_points_path.exists():
        try:
            with open(rest_points_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                pois = data.get("rest_points", [])
        except (json.JSONDecodeError, IOError):
            pass
    
    results: list[dict] = []
    for idx, (prev, nxt) in enumerate(zip(legs, legs[1:], strict=False)):
        gap = nxt.depart - prev.arrive
        arrive_time = prev.arrive
        leg_sequence = idx + 1
        
        # Find which time period this belongs to
        current_period = None
        meal_type = None
        for period_name, start, end, period_meal_type in TIME_PERIODS:
            if start <= arrive_time < end:
                current_period = period_name
                meal_type = period_meal_type
                break
        
        # Skip if this period already has a rest stop
        if current_period in used_periods:
            continue
        
        # Determine threshold
        is_meal_time = meal_type is not None
        threshold = 10 if is_meal_time else REST_STOP_THRESHOLD
        
        if gap < threshold:
            continue
        
        at_name = prev.to_name or prev.to_code
        
        # Find nearby POIs
        nearby_pois: list[dict] = []
        restaurants: list[dict] = []
        others: list[dict] = []
        
        if stations and pois and prev.to_code:
            station = stations.get(prev.to_code)
            if station:
                search_radius = 0.5  # 500m
                for poi in pois:
                    if not poi.get("lat") or not poi.get("lon"):
                        continue
                    dist = distance_km(station.lat, station.lon, poi["lat"], poi["lon"])
                    if dist <= search_radius:
                        poi_data = {
                            "name": poi.get("name", "Unknown"),
                            "type": poi.get("type", ""),
                            "brand": poi.get("brand", ""),
                            "distance_m": int(dist * 1000),
                        }
                        if poi.get("type") in ("restaurant", "fast_food", "cafe"):
                            restaurants.append(poi_data)
                        else:
                            others.append(poi_data)
                
                restaurants.sort(key=lambda x: x["distance_m"])
                others.sort(key=lambda x: x["distance_m"])
                
                if is_meal_time and restaurants:
                    nearby_pois = restaurants[:3] + others[:1]
                else:
                    nearby_pois = (restaurants + others)[:4]
        
        # Generate suggestion based on period
        if meal_type == "lunch" and nearby_pois:
            poi = next((p for p in nearby_pois if p["type"] in ("restaurant", "fast_food", "cafe")), nearby_pois[0])
            display_name = poi.get("brand") or poi.get("name", "")
            suggestion = f"🍱 ランチタイム！{display_name}で昼食（徒歩{poi['distance_m']}m、{gap}分の休憩）"
        elif meal_type == "dinner" and nearby_pois:
            poi = next((p for p in nearby_pois if p["type"] in ("restaurant", "fast_food", "cafe")), nearby_pois[0])
            display_name = poi.get("brand") or poi.get("name", "")
            suggestion = f"🍽️ ディナータイム！{display_name}で夕食（徒歩{poi['distance_m']}m、{gap}分の休憩）"
        elif current_period == "early_morning" and nearby_pois:
            poi = nearby_pois[0]
            suggestion = f"🌅 早朝の休憩！{poi.get('brand') or poi.get('name', '')}（徒歩{poi['distance_m']}m）"
        elif current_period == "morning" and nearby_pois:
            poi = nearby_pois[0]
            suggestion = f"☕ 朝の休憩！{poi.get('brand') or poi.get('name', '')}（徒歩{poi['distance_m']}m）"
        elif current_period == "late_morning" and nearby_pois:
            poi = nearby_pois[0]
            suggestion = f"🥐 午前の休憩！{poi.get('brand') or poi.get('name', '')}（徒歩{poi['distance_m']}m）"
        elif current_period == "afternoon" and nearby_pois:
            poi = nearby_pois[0]
            suggestion = f"🍵 午後のティータイム！{poi.get('brand') or poi.get('name', '')}（徒歩{poi['distance_m']}m）"
        elif current_period == "evening" and nearby_pois:
            poi = nearby_pois[0]
            suggestion = f"🌙 夜の休憩！{poi.get('brand') or poi.get('name', '')}（徒歩{poi['distance_m']}m）"
        elif nearby_pois:
            poi = nearby_pois[0]
            poi_type = poi.get("type", "")
            poi_name = poi.get("name", "")
            poi_brand = poi.get("brand", "")
            
            if poi_type == "convenience":
                suggestion = f"🏪 {poi_brand or poi_name}で飲み物を補給（徒歩{poi['distance_m']}m）"
            elif poi_type == "cafe":
                suggestion = f"☕ {poi_name}でコーヒータイム（徒歩{poi['distance_m']}m）"
            elif poi_type == "fast_food":
                suggestion = f"🍔 {poi_brand or poi_name}で軽食（徒歩{poi['distance_m']}m）"
            elif poi_type == "restaurant":
                suggestion = f"🍽️ {poi_name}で食事（徒歩{poi['distance_m']}m）"
            elif poi_type == "toilets":
                suggestion = f"🚻 公共トイレあり（徒歩{poi['distance_m']}m）"
            else:
                suggestion = f"近くに {poi_name} があります（徒歩{poi['distance_m']}m）"
        else:
            suggestion = REST_SUGGESTIONS[len(results) % len(REST_SUGGESTIONS)]
        
        results.append({
            "at": at_name,
            "minutes": gap,
            "suggestion": suggestion,
            "nearby_pois": nearby_pois[:3] if nearby_pois else None,
            "meal_break": meal_type,
            "time_period": current_period,
            "time": f"{arrive_time // 60:02d}:{arrive_time % 60:02d}",
            "end_time": f"{(arrive_time + gap) // 60:02d}:{(arrive_time + gap) % 60:02d}",
            "after_leg": leg_sequence,
        })
        
        # Mark this period as used
        if current_period:
            used_periods.add(current_period)
    
    return results


def collapse_edges(
    edges: Sequence[TripEdge], stations: dict[str, "Station"]
) -> list[LegPlan]:
    """把连续同线路的边压缩成LegPlan / 同一路線の連続エッジをまとめてLegPlan化する。"""
    if not edges:
        return []
    legs: list[LegPlan] = []
    buffer = [edges[0]]
    for edge in edges[1:]:
        last = buffer[-1]
        if edge.trip_id == last.trip_id and edge.line_id == last.line_id:
            buffer.append(edge)
        else:
            legs.append(_compress_buffer(buffer, stations))
            buffer = [edge]
    if buffer:
        legs.append(_compress_buffer(buffer, stations))
    return legs


def _compress_buffer(
    buffer: Sequence[TripEdge], stations: dict[str, "Station"]
) -> LegPlan:
    """辅助函数：将缓冲区内的边合并 / 補助関数：バッファ内のエッジをマージする。"""
    first = buffer[0]
    last = buffer[-1]

    from_station = stations.get(first.from_code)
    to_station = stations.get(last.to_code)

    from_name = from_station.name if from_station else first.from_name
    to_name = to_station.name if to_station else last.to_name
    from_lat = from_station.lat if from_station else first.from_lat
    from_lon = from_station.lon if from_station else first.from_lon
    to_lat = to_station.lat if to_station else last.to_lat
    to_lon = to_station.lon if to_station else last.to_lon

    distance = sum(edge.distance_km for edge in buffer)
    ride_minutes = last.arrive - first.depart
    path: list[tuple[float, float]] = []
    for idx, edge in enumerate(buffer):
        edge_from_station = stations.get(edge.from_code)
        edge_to_station = stations.get(edge.to_code)
        if idx == 0:
            path.append(
                (
                    edge_from_station.lat if edge_from_station else 0.0,
                    edge_from_station.lon if edge_from_station else 0.0,
                )
            )
        path.append(
            (
                edge_to_station.lat if edge_to_station else 0.0,
                edge_to_station.lon if edge_to_station else 0.0,
            )
        )

    return LegPlan(
        line_id=first.line_id,
        line_name=first.line_name,
        trip_id=first.trip_id,
        from_code=first.from_code,
        from_name=from_name,
        to_code=last.to_code,
        to_name=to_name,
        depart=first.depart,
        arrive=last.arrive,
        ride_minutes=ride_minutes,
        distance_km=distance,
        stop_hops=len(buffer),
        path=path,
        from_lat=from_lat,
        from_lon=from_lon,
        to_lat=to_lat,
        to_lon=to_lon,
    )


def derive_quadrant_labels(legs: Sequence[LegPlan], quadrant_map: dict[str, int]) -> list[str]:
    """根据行程覆盖返回象限标签 / 走行軌跡のカバレッジから象限ラベルを返す。"""
    labels = {
        1: "福岡市北東エリア",
        2: "福岡市南東エリア",
        4: "福岡市南西エリア",
        8: "福岡市北西エリア",
    }
    visited = Counter()
    for leg in legs:
        visited.update([quadrant_map.get(leg.from_code, 0)])
        visited.update([quadrant_map.get(leg.to_code, 0)])
    out = []
    for bit, label in labels.items():
        if visited.get(bit):
            out.append(label)
    return out or ["福岡市内"]


def parse_datetime(raw: str, base_dt: datetime) -> datetime | None:
    """解析多种日期时间格式 / 複数フォーマットの日時文字列を解析する。"""
    text = raw.strip()
    fmts = [
        "%Y%m%d%H%M%S",
        "%Y%m%d%H%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    ]
    if len(text) == 4 and text.isdigit():
        hours = int(text[:2])
        mins = int(text[2:])
        return base_dt.replace(hour=hours, minute=mins, second=0)
    if len(text) == 5 and text[2] == ":":
        hours = int(text[:2])
        mins = int(text[3:])
        return base_dt.replace(hour=hours, minute=mins, second=0)
    if text.endswith("Z"):
        text = text[:-1]
    if "+" in text and text.count(":") >= 2 and "T" in text:
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            pass
    for fmt in fmts:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the Haversine distance between two points in kilometers."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def project_to_plane(
    lat: float, lon: float, base_lat: float, base_lon: float
) -> tuple[float, float]:
    """Projects lat/lon coordinates to a 2D plane relative to a base coordinate."""
    lat_diff = lat - base_lat
    lon_diff = lon - base_lon
    cos_lat = math.cos(math.radians(base_lat))
    x = lon_diff * cos_lat * 111.320  # km
    y = lat_diff * 110.574  # km
    return x, y


def label_leg_to_plan(leg: "JourneyLeg", stations: dict[str, "Station"]) -> LegPlan:
    from_station = stations.get(leg.from_code)
    to_station = stations.get(leg.to_code)
    from_name = from_station.name if from_station else leg.from_code
    to_name = to_station.name if to_station else leg.to_code
    from_lat = from_station.lat if from_station else 0.0
    from_lon = from_station.lon if from_station else 0.0
    to_lat = to_station.lat if to_station else 0.0
    to_lon = to_station.lon if to_station else 0.0
    path = [(from_lat, from_lon), (to_lat, to_lon)]
    ride_minutes = max(0, leg.arrive - leg.depart)
    return LegPlan(
        line_id=leg.line_id,
        line_name=leg.line_name,
        trip_id=leg.trip_id,
        from_code=leg.from_code,
        from_name=from_name,
        to_code=leg.to_code,
        to_name=to_name,
        depart=leg.depart,
        arrive=leg.arrive,
        ride_minutes=ride_minutes,
        distance_km=leg.distance_km,
        stop_hops=leg.stop_hops,
        path=path,
        from_lat=from_lat,
        from_lon=from_lon,
        to_lat=to_lat,
        to_lon=to_lon,
    )


def inject_meal_breaks(
    legs: list[LegPlan],
    stations: dict,
    pois: list[dict],
    planner,  # PlannerService - avoid circular import
) -> tuple[list[LegPlan], list[dict]]:
    """
    Inject meal breaks into a route during lunch (11-13) and dinner (17-19) times.
    
    After arriving at a station during meal time with nearby restaurants:
    1. Insert a meal break (30-60 minutes based on distance)
    2. Re-plan the remaining route from that station with delayed departure
    
    Args:
        legs: Original route legs
        stations: Station dictionary
        pois: POI data from OSM
        planner: PlannerService instance for re-planning
        
    Returns:
        Tuple of (new_legs, meal_breaks_info)
    """
    if not legs:
        return legs, []
    
    # Meal time windows (minutes from midnight)
    LUNCH_START, LUNCH_END = 11 * 60, 13 * 60  # 11:00-13:00
    DINNER_START, DINNER_END = 17 * 60, 19 * 60  # 17:00-19:00
    
    # Track which meals have been inserted
    lunch_done = False
    dinner_done = False
    meal_breaks = []
    
    new_legs = []
    i = 0
    
    while i < len(legs):
        leg = legs[i]
        arrive_time = leg.arrive
        
        # Check if arriving during meal time
        is_lunch_time = LUNCH_START <= arrive_time <= LUNCH_END and not lunch_done
        is_dinner_time = DINNER_START <= arrive_time <= DINNER_END and not dinner_done
        
        if not (is_lunch_time or is_dinner_time):
            new_legs.append(leg)
            i += 1
            continue
        
        # Find nearby restaurants (prioritize restaurants over convenience stores)
        nearby = _find_meal_spots(leg.to_code, stations, pois)
        
        if not nearby:
            new_legs.append(leg)
            i += 1
            continue
        
        # Calculate break duration based on distance
        best_spot = nearby[0]
        distance_m = best_spot["distance_m"]
        if distance_m <= 200:
            break_duration = 30
        elif distance_m <= 500:
            break_duration = 45
        else:
            break_duration = 60
        
        # Add current leg
        new_legs.append(leg)
        
        # Record meal break info
        meal_type = "lunch" if is_lunch_time else "dinner"
        meal_break_info = {
            "type": meal_type,
            "at_stop": leg.to_name or leg.to_code,
            "at_code": leg.to_code,
            "arrive_time": f"{arrive_time // 60:02d}:{arrive_time % 60:02d}",
            "break_duration": break_duration,
            "resume_time": f"{(arrive_time + break_duration) // 60:02d}:{(arrive_time + break_duration) % 60:02d}",
            "restaurant": best_spot,
            "nearby_options": nearby[:3],
        }
        meal_breaks.append(meal_break_info)
        
        # Mark meal as done
        if is_lunch_time:
            lunch_done = True
        else:
            dinner_done = True
        
        # Get final destination from original route
        final_destination = legs[-1].to_code
        
        # Re-plan from this station to final destination with delayed departure
        new_departure = arrive_time + break_duration
        
        try:
            # Use simple RAPTOR to re-plan remaining route
            result = planner.run_simple_raptor(leg.to_code, final_destination, new_departure)
            if result:
                arrival, journey_legs = result
                for jl in journey_legs:
                    replanned_leg = label_leg_to_plan(jl, stations)
                    new_legs.append(replanned_leg)
                # Skip remaining original legs since we've re-planned
                break
        except Exception:
            pass  # If re-planning fails, continue with original route
        
        i += 1
    
    # If we didn't re-plan, just copy remaining legs
    while i < len(legs):
        new_legs.append(legs[i])
        i += 1
    
    return new_legs, meal_breaks


def _find_meal_spots(stop_code: str, stations: dict, pois: list[dict]) -> list[dict]:
    """Find nearby restaurants/convenience stores for a meal break."""
    if not stations or not pois or stop_code not in stations:
        return []
    
    station = stations[stop_code]
    
    # Categorize POIs
    restaurants = []
    convenience = []
    
    for poi in pois:
        if not poi.get("lat") or not poi.get("lon"):
            continue
        
        dist = distance_km(station.lat, station.lon, poi["lat"], poi["lon"])
        if dist > 1.0:  # Max 1km
            continue
        
        poi_data = {
            "name": poi.get("name", "Unknown"),
            "type": poi.get("type", ""),
            "brand": poi.get("brand", ""),
            "distance_m": int(dist * 1000),
        }
        
        if poi.get("type") in ("restaurant", "fast_food", "cafe"):
            restaurants.append(poi_data)
        elif poi.get("type") == "convenience":
            convenience.append(poi_data)
    
    # Sort by distance
    restaurants.sort(key=lambda x: x["distance_m"])
    convenience.sort(key=lambda x: x["distance_m"])
    
    # Return restaurants first, then convenience as fallback
    return restaurants[:5] + convenience[:2]


def auto_inject_meal_breaks(
    legs: list[LegPlan],
    stations: dict,
    pois: list[dict],
) -> list[dict]:
    """
    Detect meal times and suggest restaurants (simplified version without route re-planning).
    
    This is used in ChallengePlan.to_dict() for auto-injection.
    Unlike inject_meal_breaks(), this doesn't modify the route - just adds meal break suggestions.
    """
    if not legs:
        return []
    
    # Meal time windows (minutes from midnight)
    LUNCH_START, LUNCH_END = 11 * 60, 13 * 60  # 11:00-13:00
    DINNER_START, DINNER_END = 17 * 60, 19 * 60  # 17:00-19:00
    
    lunch_done = False
    dinner_done = False
    meal_breaks = []
    
    for leg in legs:
        arrive_time = leg.arrive
        
        # Check if arriving during meal time
        is_lunch = LUNCH_START <= arrive_time <= LUNCH_END and not lunch_done
        is_dinner = DINNER_START <= arrive_time <= DINNER_END and not dinner_done
        
        if not (is_lunch or is_dinner):
            continue
        
        # Find nearby restaurants
        nearby = _find_meal_spots(leg.to_code, stations, pois)
        if not nearby:
            continue
        
        best_spot = nearby[0]
        distance_m = best_spot["distance_m"]
        
        # Calculate suggested break duration
        if distance_m <= 200:
            break_duration = 30
        elif distance_m <= 500:
            break_duration = 45
        else:
            break_duration = 60
        
        meal_type = "lunch" if is_lunch else "dinner"
        meal_breaks.append({
            "type": meal_type,
            "at_stop": leg.to_name or leg.to_code,
            "at_code": leg.to_code,
            "arrive_time": f"{arrive_time // 60:02d}:{arrive_time % 60:02d}",
            "suggested_duration": break_duration,
            "restaurant": best_spot,
            "nearby_options": nearby[:3],
        })
        
        if is_lunch:
            lunch_done = True
        else:
            dinner_done = True
    
    return meal_breaks


__all__ = [
    "collapse_edges",
    "derive_quadrant_labels",
    "format_minutes",
    "generate_rest_stops",
    "haversine_km",
    "parse_datetime",
    "distance_km",
    "project_to_plane",
    "label_leg_to_plan",
    "is_in_fukuoka",
    "inject_meal_breaks",
    "auto_inject_meal_breaks",
]



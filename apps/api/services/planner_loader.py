from __future__ import annotations

import csv
import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import math
import yaml

from .planner_constants import (
    BOUNDARY_BIN_COUNT,
    BOUNDARY_MAX_DIST_KM,
    BOUNDARY_MIN_DIST_KM,
    SEGMENTS_PREFIX,
    TIMETABLE_PREFIX,
)
from .planner_models import Station, TripEdge
from .planner_utils import (
    distance_km,
    haversine_km,
    is_in_fukuoka,
    parse_datetime,
    project_to_plane,
)

if TYPE_CHECKING:
    from .planner import PlannerService

logger = logging.getLogger(__name__)


def _extract_code(entry: str | dict) -> str | None:
    """Helper to normalize a station entry to its code string."""
    if isinstance(entry, str):
        return entry.strip() or None
    if isinstance(entry, dict):
        code = entry.get("code") or entry.get("id")
        return str(code).strip() if code else None
    return None


def load_boundary_include_codes(service: "PlannerService") -> set[str]:
    """Return codes explicitly listed in boundary_overrides.json include."""
    path = service.data_dir / "generated" / "boundary_overrides.json"
    codes: set[str] = set()
    if not path.exists():
        return codes
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data.get("include", []) or []:
            code = _extract_code(entry)
            if code:
                codes.add(code)
    except json.JSONDecodeError:
        logger.warning("boundary_overrides.json is invalid; ignoring includes for edge filtering.")
    return codes


def load_yaml(path: Path) -> dict:
    """读取YAML文件并返回字典 / YAMLファイルを読み込み辞書を返す。"""
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a YAML mapping")
    return data


def load_static_assets(service: "PlannerService") -> None:
    """加载站点、线路、边界等静态资产 / 駅・路線・境界などの静的資産を読み込む。"""
    service.stations = load_stations(service)
    service.line_names, service.eligible_lines = load_line_meta(service)
    service.hakata_stops = detect_hakata_stops(service)
    if not service.hakata_stops:
        raise RuntimeError("博多駅周辺の停留所が stations_fukuoka.csv から検出できません")
    origin_station = service.stations.get(service.hakata_stops[0])
    if origin_station:
        service.hakata_coord = (origin_station.lat, origin_station.lon)
    service.quadrant_map = assign_quadrants(service)
    service.city_boundary = load_city_boundary(service)
    service.line_stop_edges = load_line_stop_edges(service)


def load_stations(service: "PlannerService") -> dict[str, Station]:
    """读取 stations_fukuoka.csv 并返回站点映射 / stations_fukuoka.csv を読み駅マップを返す。"""
    path = service.data_dir / "base" / "stations_fukuoka.csv"
    if not path.exists():
        raise RuntimeError("stations_fukuoka.csv が見つかりません")
    stations: dict[str, Station] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("ekispert_station_code") or row.get("station_code")
            if not code:
                continue
            try:
                lat = float(row.get("lat") or 0)
                lon = float(row.get("lon") or 0)
            except ValueError:
                continue
            if lat == 0 and lon == 0:
                continue
            stations[str(code)] = Station(
                code=str(code),
                name=row.get("name") or str(code),
                lat=lat,
                lon=lon,
            )
    if not stations:
        raise RuntimeError("stations_fukuoka.csv に有効なデータがありません")
    return stations


def load_line_meta(service: "PlannerService") -> tuple[dict[str, str], set[str]]:
    """读取 freepass 配置，返回线路名称与可用集合 / freepass設定を読み路線名と対象集合を返す。"""
    path = service.data_dir / "base" / "freepass_lines.yml"
    data = load_yaml(path)
    line_names: dict[str, str] = {}
    eligible: set[str] = set()
    for row in data.get("freepass_lines", []):
        line_id = str(row.get("line_id"))
        if not line_id:
            continue
        name = row.get("name") or row.get("line_name") or line_id
        line_names[line_id] = name
        if row.get("eligible"):
            eligible.add(line_id)
    if not eligible:
        raise RuntimeError("freepass_lines.yml に eligible な路線がありません")
    return line_names, eligible


def detect_hakata_stops(service: "PlannerService") -> list[str]:
    """
    博多駅とその周辺1km以内の停留所を検出する。
    Detect Hakata Station and nearby stops within 1km radius.
    """
    import math
    
    # 博多駅(A・E・F)の座標を基準点とする
    # Use Hakata Station (A・E・F) coordinates as reference point
    HAKATA_LAT = 33.587089
    HAKATA_LON = 130.421197
    MAX_DISTANCE_KM = 1.0
    
    def calc_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """2点間の距離を計算(km) / Calculate distance between two points in km"""
        lat_diff = (lat2 - lat1) * 111.32
        lon_diff = (lon2 - lon1) * 111.32 * math.cos(math.radians(lat1))
        return math.sqrt(lat_diff**2 + lon_diff**2)
    
    # "博多駅"を含む駅のみを対象とする (博多工業高校などを除外)
    # Only target stations with "博多駅" (exclude stations like 博多工業高校)
    hakata_station_keywords = ["博多駅", "博多バスターミナル"]
    
    candidates = []
    for code, st in service.stations.items():
        if any(keyword in st.name for keyword in hakata_station_keywords):
            distance = calc_distance(HAKATA_LAT, HAKATA_LON, st.lat, st.lon)
            if distance <= MAX_DISTANCE_KM:
                candidates.append((code, st, distance))
    
    # 距離でソート（近い順）
    # Sort by distance (closest first)
    candidates.sort(key=lambda x: x[2])
    
    if candidates:
        return [code for code, _, _ in candidates]
    
    # フォールバック: 博多駅座標に最も近い3駅
    # Fallback: pick 3 nearest stations to Hakata Station coordinates
    fallback = sorted(
        service.stations.values(),
        key=lambda st: calc_distance(HAKATA_LAT, HAKATA_LON, st.lat, st.lon),
    )
    return [station.code for station in fallback[:3]]


def assign_quadrants(service: "PlannerService") -> dict[str, int]:
    """根据相对于博多的位置给站点打上象限标签 / 博多基準で象限ビットを付与する。"""
    mask: dict[str, int] = {}
    base_lat, base_lon = service.hakata_coord
    for code, station in service.stations.items():
        lat = station.lat
        lon = station.lon
        quadrant = 0
        if lat >= base_lat:
            quadrant |= 1  # north
        else:
            quadrant |= 4  # south
        if lon >= base_lon:
            quadrant |= 2  # east
        else:
            quadrant |= 8  # west
        mask[code] = quadrant
    return mask


def load_city_boundary(service: "PlannerService") -> list[list[tuple[float, float]]]:
    """加载福冈市GeoJSON边界 / 福岡市のGeoJSON境界を読み込む。"""
    path = service.data_dir / "base" / "fukuoka_city.geojson"
    if not path.exists():
        logger.warning("fukuoka_city.geojson not found; city loop may degrade.")
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("City boundary geojson is not valid JSON.")
        return []

    features = data.get("features")
    if not isinstance(features, list):
        logger.warning("City boundary geojson must be a FeatureCollection.")
        return []

    rings: list[list[tuple[float, float]]] = []

    def append_ring(raw_ring: list[list[float]]) -> None:
        cleaned: list[tuple[float, float]] = []
        for pair in raw_ring:
            if (
                isinstance(pair, (list, tuple))
                and len(pair) >= 2
                and isinstance(pair[0], (int, float))
                and isinstance(pair[1], (int, float))
            ):
                lon, lat = pair[0], pair[1]
                cleaned.append((lat, lon))
        if len(cleaned) >= 2:
            rings.append(cleaned)

    for feature in features:
        geometry = feature.get("geometry") if isinstance(feature, dict) else None
        if not isinstance(geometry, dict):
            continue
        gtype = geometry.get("type")
        coords = geometry.get("coordinates")
        if not coords:
            continue
        if gtype == "Polygon" and isinstance(coords, list):
            append_ring(coords[0] if coords else [])
        elif gtype == "MultiPolygon" and isinstance(coords, list):
            for poly in coords:
                if poly:
                    append_ring(poly[0])

    if not rings:
        logger.warning("City boundary geojson has no polygon data.")
        return []
    return rings



def load_line_stop_edges(service: "PlannerService") -> dict[str, list[str]]:
    """读取 line_stop_edges.csv，构建线路停靠顺序 / line_stop_edges.csv から路線停留順を構築する。"""
    path = service.data_dir / "base" / "line_stop_edges.csv"
    mapping: dict[str, list[str]] = defaultdict(list)
    if not path.exists():
        logger.warning("line_stop_edges.csv missing; RAPTOR coverage may be limited.")
        return mapping
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            line_id = str(row.get("line_id") or "")
            stop_id = str(row.get("station_code") or "")
            if not line_id or not stop_id:
                continue
            mapping[line_id].append(stop_id)
    logger.info(f"Loaded {len(mapping)} line-stop mappings.")
    return mapping


def distance_point_to_polyline(service: "PlannerService", lat: float, lon: float) -> float:
    """计算点到城市边界的距离 / 点から都市境界までの距離を計算する。"""
    if not service.city_boundary:
        return float("inf")
    px, py = project_to_plane(lat, lon, *service.hakata_coord)
    min_dist = float("inf")
    for ring in service.city_boundary:
        if len(ring) < 2:
            continue
        for idx in range(len(ring) - 1):
            lat_a, lon_a = ring[idx]
            lat_b, lon_b = ring[idx + 1]
            ax, ay = project_to_plane(lat_a, lon_a, *service.hakata_coord)
            bx, by = project_to_plane(lat_b, lon_b, *service.hakata_coord)
            dist = point_segment_distance(px, py, ax, ay, bx, by)
            if dist < min_dist:
                min_dist = dist
    return min_dist



def point_segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    """计算点到线段的距离 / 点と線分の距離を算出する。"""
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    nx = ax + t * dx
    ny = ay + t * dy
    return math.hypot(px - nx, py - ny)


def build_boundary_sequence(service: "PlannerService") -> None:
    """根据福冈市边界挑选代表性站点（含手工例外）用于 city-loop TSP。"""
    if not service.city_boundary:
        service.boundary_sequence = []
        service.boundary_index = {}
        return

    overrides_path = service.data_dir / "generated" / "boundary_overrides.json"
    include_overrides: set[str] = set()
    exclude_overrides: set[str] = set()
    substitutes: dict[str, dict] = {}
    if overrides_path.exists():
        try:
            override_data = json.loads(overrides_path.read_text(encoding="utf-8"))
            include_overrides = {
                _extract_code(code) for code in override_data.get("include", []) if _extract_code(code)
            }
            exclude_overrides = {
                _extract_code(code) for code in override_data.get("exclude", []) if _extract_code(code)
            }
            for item in override_data.get("substitute", []) or []:
                target = _extract_code(item.get("target") or item)
                via = [_extract_code(v) for v in item.get("via", []) if _extract_code(v)]
                auto = bool(item.get("auto")) or not via
                radius_km = float(item.get("radius_km", 2.0))
                min_degree = int(item.get("min_degree", 2))
                if target:
                    substitutes[target] = {
                        "via": via,
                        "auto": auto,
                        "radius_km": radius_km,
                        "min_degree": min_degree,
                    }
        except json.JSONDecodeError:
            logger.warning("boundary_overrides.json is invalid; ignoring overrides.")

    # Prepare boundary segments projected to plane for distance checks.
    boundary_segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for ring in service.city_boundary:
        for a, b in zip(ring, ring[1:], strict=False):
            ax, ay = project_to_plane(a[0], a[1], *service.hakata_coord)
            bx, by = project_to_plane(b[0], b[1], *service.hakata_coord)
            boundary_segments.append(((ax, ay), (bx, by)))

    def boundary_distance_km(lat: float, lon: float) -> float:
        px, py = project_to_plane(lat, lon, *service.hakata_coord)
        if not boundary_segments:
            return float("inf")
        return min(
            point_segment_distance(px, py, ax, ay, bx, by)
            for (ax, ay), (bx, by) in boundary_segments
        )

    def auto_substitutes(target_code: str, radius_km: float, min_degree: int) -> list[str]:
        target = service.stations.get(target_code)
        if not target:
            return []
        results: list[tuple[int, float, str]] = []
        for code, st in service.stations.items():
            if code == target_code or code in exclude_overrides:
                continue
            deg = route_degree.get(code, 0)
            if deg < min_degree:
                continue
            d = distance_km(target.lat, target.lon, st.lat, st.lon)
            if d > radius_km:
                continue
            results.append((deg, d, code))
        results.sort(key=lambda t: (-t[0], t[1]))
        return [code for _deg, _d, code in results[:2]]

    bins: list[tuple[float, str]] = []
    bin_size = 360.0 / BOUNDARY_BIN_COUNT
    best_per_bin: dict[int, tuple[float, float, str]] = {}

    route_degree: dict[str, int] = {}
    if getattr(service, "routes_by_stop", None):
        route_degree = {stop: len(routes) for stop, routes in service.routes_by_stop.items()}

    for code, station in service.stations.items():
        if code in exclude_overrides:
            continue
        angle = (math.degrees(math.atan2(station.lon - service.hakata_coord[1], station.lat - service.hakata_coord[0])) + 360.0) % 360.0
        dist = boundary_distance_km(station.lat, station.lon)
        in_band = BOUNDARY_MIN_DIST_KM <= dist <= BOUNDARY_MAX_DIST_KM
        forced = code in include_overrides
        degree = route_degree.get(code, 0)
        # Skip dead-end or single-line outliers unless explicitly forced.
        if not forced and (not in_band or degree < 2):
            continue
        bin_idx = int(angle // bin_size)
        current = best_per_bin.get(bin_idx)
        if current is None or dist < current[0]:
            best_per_bin[bin_idx] = (dist, angle, code)

    bins.extend((angle, code) for _dist, angle, code in best_per_bin.values())

    # Ensure overrides are always included
    for code in include_overrides:
        if code not in service.stations:
            continue
        st = service.stations[code]
        angle = (math.degrees(math.atan2(st.lon - service.hakata_coord[1], st.lat - service.hakata_coord[0])) + 360.0) % 360.0
        bins.append((angle, code))

    if not bins:
        service.boundary_sequence = []
        service.boundary_index = {}
        return

    bins.sort()
    sequence = [code for _, code in bins]
    if service.hakata_stops:
        sequence = [service.hakata_stops[0]] + sequence + [service.hakata_stops[0]]

    seen: set[str] = set()
    deduped: list[str] = []
    for code in sequence:
        if code in substitutes:
            info = substitutes[code]
            via_list: list[str] = info.get("via") or []
            if info.get("auto"):
                via_list = via_list or auto_substitutes(
                    code, info.get("radius_km", 2.0), info.get("min_degree", 2)
                )
            for via in via_list:
                if via in exclude_overrides:
                    continue
                if via not in service.stations:
                    logger.debug("Substitute station %s not found in stations; skipping.", via)
                    continue
                if via in seen:
                    continue
                deduped.append(via)
                seen.add(via)
            continue
        if code in seen:
            continue
        deduped.append(code)
        seen.add(code)

    service.boundary_sequence = deduped
    service.boundary_index = {code: idx for idx, code in enumerate(deduped)}


def find_latest_data_file(service: "PlannerService") -> Path | None:
    """寻找最新的福冈市内 segments 文件 / 最新の福岡市内segmentsファイルを探す。"""
    timetables_dir = service.data_dir / "timetables"
    candidates = sorted(
        timetables_dir.glob("segments_fukuoka_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0]
    
    # Fallback for older timetable format for compatibility, though less likely now
    candidates = sorted(
        timetables_dir.glob("timetable_fukuoka_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0]
        
    return None


def load_edges(service: "PlannerService", data_path: Path | None) -> None:
    """加载CSV并生成 TripEdge 列表 / CSVを読みTripEdge一覧を生成する。"""
    if data_path is None:
        raise RuntimeError("segments_fukuoka_YYYYMMDD.csv が見つかりません")
    
    # Simplified logic as we now have dedicated fukuoka segment files
    if "segment" in data_path.name:
        edges = load_segment_edges(service, data_path)
    elif "timetable" in data_path.name:
        edges = load_timetable_edges(service, data_path)
    else:
        raise RuntimeError(f"Unknown timetable format for file: {data_path.name}")

    if not edges:
        raise RuntimeError("エッジデータの読み込みに失敗しました")
    service.static_edges = edges
    service._timetable_manager.load_static_edges(edges)
    service._refresh_stop_schedules(force_refresh=True)


def load_segment_edges(service: "PlannerService", segment_path: Path) -> list[TripEdge]:
    """读取 segments CSV 并转换为边 / segments CSV を読みエッジへ変換する。"""
    edges: list[TripEdge] = []
    polygons = service.fukuoka_polygons if hasattr(service, "fukuoka_polygons") else []
    boundary_includes = load_boundary_include_codes(service)
    # Pre-calculate valid stations to avoid expensive ray casting in the loop
    valid_stations = set()
    if polygons:
        for code, station in service.stations.items():
            if is_in_fukuoka(station.lat, station.lon, polygons):
                valid_stations.add(code)
    
    with segment_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Note: trip_id and segment_id are optional - fallback logic exists below
        required = {
            "line_id",
            "direction",
            "service_date",
            "from_stop",
            "to_stop",
            "depart",
            "arrive",
        }
        if not required.issubset(set(reader.fieldnames or [])):
            raise RuntimeError("segments CSV の列構成が想定外です")
        for row in reader:
            line_id = str(row.get("line_id") or "")
            if line_id not in service.eligible_lines:
                continue
            from_code = str(row.get("from_stop") or "")
            to_code = str(row.get("to_stop") or "")
            
            depart = parse_segment_minutes(row.get("depart"))
            arrive = parse_segment_minutes(row.get("arrive"))

            if depart is None or arrive is None:
                continue
            if arrive <= depart:
                arrive += 1440
            
            try:
                st_a = service.stations[from_code]
                st_b = service.stations[to_code]
            except KeyError:
                continue
            
            # 2. 福岡市内判定 (または特例) / Check if inside Fukuoka (or override)
            #    Both must be inside OR explicitly included in boundary_includes
            is_valid = False
            if polygons:
                is_from_in = from_code in valid_stations
                is_to_in = to_code in valid_stations
                if is_from_in and is_to_in:
                    is_valid = True
            
            if not is_valid and not (
                from_code in boundary_includes or to_code in boundary_includes
            ):
                continue
            
            trip_identifier = str(
                row.get("trip_id")
                or row.get("segment_id")
                or f"{line_id}-{row.get('direction', '')}-{depart}"  # Group by line+direction+departure time
            )
            edges.append(
                TripEdge(
                    line_id=line_id,
                    line_name=service.line_names.get(line_id, line_id),
                    trip_id=trip_identifier,
                    direction=str(row.get("direction") or ""),
                    service_date=str(row.get("service_date") or ""),
                    from_code=from_code,
                    from_name=row.get("from_name") or st_a.name,
                    to_code=to_code,
                    to_name=row.get("to_name") or st_b.name,
                    depart=depart,
                    arrive=arrive,
                    distance_km=haversine_km(st_a, st_b),
                    from_lat=st_a.lat,
                    from_lon=st_a.lon,
                    to_lat=st_b.lat,
                    to_lon=st_b.lon,
                )
            )
    return edges


def load_timetable_edges(service: "PlannerService", timetable_path: Path) -> list[TripEdge]:
    """解析 timetable CSV 为 TripEdge 列表 / timetable CSV を解析しTripEdge一覧を得る。"""
    polygons = service.fukuoka_polygons if hasattr(service, "fukuoka_polygons") else []
    boundary_includes = load_boundary_include_codes(service)
    rows_by_trip: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    with timetable_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            line_code = str(row.get("operationLineCode") or "")
            if line_code not in service.eligible_lines:
                continue
            station_code = str(row.get("station_code") or "")
            if station_code not in service.stations:
                continue
            try:
                seq = int(row.get("stop_seq") or 0)
            except ValueError:
                seq = 0
            row["_seq"] = seq
            key = (
                line_code,
                str(row.get("direction") or ""),
                str(row.get("service_date") or ""),
                str(row.get("trip_id") or ""),
            )
            rows_by_trip[key].append(row)
    if not rows_by_trip:
        raise RuntimeError("時刻表から有効な trip データを読み込めませんでした")
    edges: list[TripEdge] = []
    for (line_id, direction, service_date, trip_id), rows in rows_by_trip.items():
        rows.sort(key=lambda r: r["_seq"])
        edges.extend(
            rows_to_edges(
                service=service,
                line_id=line_id,
                direction=direction,
                service_date=service_date,
                trip_id=trip_id,
                rows=rows,
            )
        )
    return edges


def rows_to_edges(
    service: "PlannerService",
    line_id: str,
    direction: str,
    service_date: str,
    trip_id: str,
    rows: Sequence[dict],
) -> list[TripEdge]:
    """把单趟行程的原始行转换为 TripEdge 序列 / 1便分の行データをTripEdge列へ変換する。"""
    edges: list[TripEdge] = []
    try:
        base_dt = datetime.strptime(service_date or "19700101", "%Y%m%d")
    except ValueError:
        base_dt = datetime.strptime("19700101", "%Y%m%d")
    prev_minutes: int | None = None
    rollover = 0

    def normalize_time(raw: str | None) -> int | None:
        nonlocal prev_minutes, rollover
        if not raw:
            return None
        raw = raw.strip()
        dt_val = parse_datetime(raw, base_dt)
        if dt_val is None:
            return None
        minutes = int((dt_val - base_dt).total_seconds() // 60)
        if prev_minutes is not None and minutes + rollover + 600 < prev_minutes:
            rollover += 1440
        minutes += rollover
        prev_minutes = minutes
        return minutes

    enriched = []
    for row in rows:
        dep = normalize_time(row.get("dep") or row.get("Departure"))
        arr = normalize_time(row.get("arr") or row.get("Arrival"))
        enriched.append(
            {
                "station_code": str(row.get("station_code")),
                "dep": dep,
                "arr": arr,
            }
        )

    for from_row, to_row in zip(enriched, enriched[1:], strict=False):
        from_code = str(from_row["station_code"])
        to_code = str(to_row["station_code"])
        if from_code not in service.stations or to_code not in service.stations:
            continue
        depart = from_row["dep"]
        arrive = to_row["arr"]
        if depart is None or arrive is None or arrive <= depart:
            continue
        st_a = service.stations[from_code]
        st_b = service.stations[to_code]
        if polygons and not (
            is_in_fukuoka(st_a.lat, st_a.lon, polygons)
            and is_in_fukuoka(st_b.lat, st_b.lon, polygons)
        ) and not (
            from_code in boundary_includes or to_code in boundary_includes
        ):
            continue
        edges.append(
            TripEdge(
                line_id=line_id,
                line_name=service.line_names.get(line_id, line_id),
                trip_id=trip_id,
                direction=direction,
                service_date=service_date,
                from_code=from_code,
                from_name=st_a.name,
                to_code=to_code,
                to_name=st_b.name,
                depart=depart,
                arrive=arrive,
                distance_km=haversine_km(st_a, st_b),
                from_lat=st_a.lat,
                from_lon=st_a.lon,
                to_lat=st_b.lat,
                to_lon=st_b.lon,
            )
        )
    return edges


def parse_segment_minutes(raw: str | None) -> int | None:
    """解析 segments CSV 的时间字段 / segments CSV の時間文字列を解析する。"""
    if not raw:
        return None
    text = raw.strip()
    if len(text) < 5 or text[2] != ":":
        return None
    try:
        hours = int(text[0:2])
        minutes = int(text[3:5])
    except ValueError:
        return None
    return hours * 60 + minutes

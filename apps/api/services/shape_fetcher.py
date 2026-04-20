from __future__ import annotations

import logging
import threading
from typing import Any

import requests

logger = logging.getLogger(__name__)

MIXWAY_BASE_URL = "https://mixway.ekispert.jp"
SEARCH_ENDPOINT = "/v1/json/search/course/extreme"
SHAPE_ENDPOINT = "/v1/json/course/shape"


def _join_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}{path}"


class MixwayShapeFetcher:
    """Small helper to call Mixway search + shape APIs for leg polylines."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = MIXWAY_BASE_URL,
        timeout: float = 30.0,
        session: requests.Session | None = None,
        use_cache: bool = True,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = session or requests.Session()
        self._cache: dict[tuple[str, str, str | None], list[dict[str, float]]] = {}
        self._lock = threading.Lock()
        
        # Initialize shape cache if enabled
        self._shape_cache = None
        if use_cache:
            try:
                from .shape_cache import ShapeCache
                self._shape_cache = ShapeCache()
                logger.info("Shape cache enabled")
            except ImportError:
                logger.warning("ShapeCache not available, caching disabled")

    def fetch_leg_shape(
        self,
        from_code: str,
        to_code: str,
        departure: str | None = None,
    ) -> list[dict[str, float]]:
        """Return a list of {lat, lon} dicts describing the leg path."""
        # Check persistent cache first
        if self._shape_cache:
            cached_coords = self._shape_cache.get(from_code, to_code, departure)
            if cached_coords is not None:
                return cached_coords
        
        # Check memory cache
        cache_key = (from_code, to_code, departure or "")
        with self._lock:
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Fetch from API
        serialize_data = self._search_course(from_code, to_code, departure)
        if not serialize_data:
            with self._lock:
                self._cache[cache_key] = []
            if self._shape_cache:
                self._shape_cache.set(from_code, to_code, departure, [])
            return []

        coords = self._fetch_shape(serialize_data)
        
        # Store in both caches
        with self._lock:
            self._cache[cache_key] = coords
        if self._shape_cache:
            self._shape_cache.set(from_code, to_code, departure, coords)
        
        return coords


    # ----- internal helpers -----

    def _search_course(
        self, from_code: str, to_code: str, departure: str | None
    ) -> str | None:
        params: dict[str, Any] = {
            "key": self._api_key,
            "viaList": f"{from_code}:{to_code}",
            "searchType": "departure",
            "addStop": "true",
        }
        if departure:
            params["time"] = departure.replace(":", "")
        url = _join_url(self._base_url, SEARCH_ENDPOINT)
        
        # Helper to execute request
        def _execute(p):
            try:
                resp = self._session.get(url, params=p, timeout=self._timeout)
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, ValueError) as exc:
                logger.warning("Mixway course search failed/invalid: %s", exc)
                return None

        # First attempt (with time if provided)
        payload = _execute(params)
        
        # Check result validity
        def _get_serialize(pl):
            if not isinstance(pl, dict): return None
            res = pl.get("ResultSet")
            if not isinstance(res, dict): return None
            crs = res.get("Course")
            if not crs: return None
            if isinstance(crs, dict): crs = [crs]
            if not crs: return None
            first = crs[0] or {}
            return str(first.get("SerializeData") or first.get("serializeData") or "")

        serialize_data = _get_serialize(payload)

        # Fallback: Retry without time if failed and time was specified
        if not serialize_data and departure:
            logger.info(f"Retrying search for {from_code}->{to_code} without time...")
            params.pop("time", None)
            payload = _execute(params)
            serialize_data = _get_serialize(payload)

        if serialize_data:
            return serialize_data
        return None

    def _fetch_shape(self, serialize_data: str) -> list[dict[str, float]]:
        params = {"key": self._api_key, "serializeData": serialize_data}
        url = _join_url(self._base_url, SHAPE_ENDPOINT)
        try:
            response = self._session.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Mixway shape API failed: %s", exc)
            return []

        try:
            payload = response.json()
        except ValueError:
            logger.warning("Mixway shape API returned non-JSON body.")
            return []

        result = payload.get("ResultSet") if isinstance(payload, dict) else None
        if not isinstance(result, dict):
            return []

        # Newer API format: ResultSet.Course.Line.Element[].Shape[].GeoPoint
        course = result.get("Course") or {}
        lines = course.get("Line") or []
        if isinstance(lines, dict):
            lines = [lines]
        coords: list[dict[str, float]] = []
        for line in lines:
            for element in (line.get("Element") or []):
                for shape in (element.get("Shape") or []):
                    geo = shape.get("GeoPoint") or {}
                    lat = geo.get("lati_d") or geo.get("lati")
                    lon = geo.get("longi_d") or geo.get("longi")
                    if lat is None or lon is None:
                        continue
                    try:
                        coords.append({"lat": float(lat), "lon": float(lon)})
                    except (TypeError, ValueError):
                        continue

        # Legacy API format: ResultSet.Shape[0].Line (string "lon,lat lon,lat")
        if not coords:
            shape_list = result.get("Shape") or []
            if shape_list:
                line = shape_list[0].get("Line")
                for pair in (line or "").strip().split():
                    try:
                        lon_str, lat_str = pair.split(",", 1)
                        coords.append({"lat": float(lat_str), "lon": float(lon_str)})
                    except (ValueError, TypeError):
                        continue

        return coords


__all__ = ["MixwayShapeFetcher"]

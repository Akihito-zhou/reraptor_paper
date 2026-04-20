"""
Shape data caching module for Mixway API responses.

Provides file-based caching to reduce API calls and improve performance.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = Path(__file__).parent.parent / "data" / ".shape_cache"
DEFAULT_TTL_SECONDS = 86400  # 24 hours


class ShapeCache:
    """File-based cache for shape API responses."""

    def __init__(
        self,
        cache_dir: Path | str = DEFAULT_CACHE_DIR,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Shape cache initialized at {self.cache_dir}")

    def _get_cache_path(self, key: str) -> Path:
        """Generate cache file path from key."""
        # Use hash to avoid filesystem issues with special characters
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"

    def get(self, from_code: str, to_code: str, departure: str | None = None) -> list[dict[str, float]] | None:
        """Retrieve cached shape data if available and not expired."""
        key = self._make_key(from_code, to_code, departure)
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with self._lock:
                with cache_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Check expiry
                cached_at = data.get("cached_at", 0)
                if time.time() - cached_at > self.ttl_seconds:
                    logger.debug(f"Cache expired for {key}")
                    return None
                
                coords = data.get("coords", [])
                logger.debug(f"Cache hit for {key} ({len(coords)} points)")
                return coords
                
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(f"Failed to read cache for {key}: {exc}")
            return None

    def set(self, from_code: str, to_code: str, departure: str | None, coords: list[dict[str, float]]) -> None:
        """Store shape data in cache."""
        key = self._make_key(from_code, to_code, departure)
        cache_path = self._get_cache_path(key)

        data = {
            "from_code": from_code,
            "to_code": to_code,
            "departure": departure,
            "coords": coords,
            "cached_at": time.time(),
        }

        try:
            with self._lock:
                with cache_path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            logger.debug(f"Cached {key} ({len(coords)} points)")
        except OSError as exc:
            logger.warning(f"Failed to write cache for {key}: {exc}")

    def clear(self) -> int:
        """Clear all cached files. Returns number of files deleted."""
        count = 0
        with self._lock:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                    count += 1
                except OSError:
                    pass
        logger.info(f"Cleared {count} cache files")
        return count

    def clear_expired(self) -> int:
        """Remove expired cache files. Returns number of files deleted."""
        count = 0
        now = time.time()
        with self._lock:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with cache_file.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    cached_at = data.get("cached_at", 0)
                    if now - cached_at > self.ttl_seconds:
                        cache_file.unlink()
                        count += 1
                except (json.JSONDecodeError, OSError):
                    # If we can't read it, delete it
                    try:
                        cache_file.unlink()
                        count += 1
                    except OSError:
                        pass
        logger.info(f"Cleared {count} expired cache files")
        return count

    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        total = 0
        expired = 0
        total_size = 0
        now = time.time()
        
        with self._lock:
            for cache_file in self.cache_dir.glob("*.json"):
                total += 1
                try:
                    total_size += cache_file.stat().st_size
                    with cache_file.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    cached_at = data.get("cached_at", 0)
                    if now - cached_at > self.ttl_seconds:
                        expired += 1
                except (json.JSONDecodeError, OSError):
                    expired += 1

        return {
            "total_files": total,
            "expired_files": expired,
            "valid_files": total - expired,
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }

    @staticmethod
    def _make_key(from_code: str, to_code: str, departure: str | None) -> str:
        """Generate cache key from parameters."""
        dep = departure or "anytime"
        return f"{from_code}_{to_code}_{dep}"


__all__ = ["ShapeCache"]

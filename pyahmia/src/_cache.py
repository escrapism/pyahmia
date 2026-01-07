import json
import time
import typing as t
from hashlib import sha256
from pathlib import Path
from tempfile import gettempdir

__all__ = ["CacheManager"]


class CacheManager:
    """
    Manages caching of search results and session tokens in the system's temp directory.
    """

    def __init__(self, cache_dir: t.Optional[Path] = None, ttl: int = 3600):
        """
        Initialize the cache manager.

        :param cache_dir: Directory to store cache files. Defaults to system temp directory.
        :param ttl: Time-to-live for cache entries in seconds (default: 3600 = 1 hour)
        """
        if cache_dir is None:
            cache_dir = Path(gettempdir()) / "pyahmia_cache"

        self.cache_dir = cache_dir
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _get_cache_key(key: str) -> str:
        """
        Generate a safe cache key using SHA256 hash.

        :param key: Original cache key
        :return: Hashed cache key
        """
        return sha256(key.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """
        Get the file path for a cache key.

        :param key: Cache key
        :return: Path to cache file
        """
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.json"

    def get(self, key: str) -> t.Optional[t.Any]:
        """
        Retrieve a value from cache if it exists and hasn't expired.

        :param key: Cache key
        :return: Cached value or None if not found or expired
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with cache_path.open("r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # Check if cache has expired
            if time.time() > cache_data.get("expires_at", 0):
                # Cache expired, delete it
                cache_path.unlink(missing_ok=True)
                return None

            return cache_data.get("value")

        except (json.JSONDecodeError, KeyError, OSError):
            # If there's any error reading the cache, treat it as a cache miss
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: t.Any, ttl: t.Optional[int] = None) -> None:
        """
        Store a value in cache with expiration time.

        :param key: Cache key
        :param value: Value to cache (must be JSON serializable)
        :param ttl: Optional custom TTL for this entry (in seconds)
        """
        cache_path = self._get_cache_path(key)
        expires_at = time.time() + (ttl if ttl is not None else self.ttl)

        cache_data = {
            "value": value,
            "expires_at": expires_at,
            "created_at": time.time(),
        }

        try:
            with cache_path.open("w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
        except (OSError, TypeError):
            # If caching fails, just continue without caching
            pass

    def delete(self, key: str) -> None:
        """
        Delete a specific cache entry.

        :param key: Cache key to delete
        """
        cache_path = self._get_cache_path(key)
        cache_path.unlink(missing_ok=True)

    def clear(self) -> int:
        """
        Clear all cache entries.

        :return: Number of cache files deleted
        """
        count = 0
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink(missing_ok=True)
                count += 1
        return count

    def clear_expired(self) -> int:
        """
        Clear only expired cache entries.

        :return: Number of expired cache files deleted
        """
        count = 0
        current_time = time.time()

        if not self.cache_dir.exists():
            return count

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with cache_file.open("r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                if current_time > cache_data.get("expires_at", 0):
                    cache_file.unlink(missing_ok=True)
                    count += 1

            except (json.JSONDecodeError, KeyError, OSError):
                # If we can't read the file, delete it
                cache_file.unlink(missing_ok=True)
                count += 1

        return count

    @staticmethod
    def get_search_cache_key(query: str, time_period: str, use_tor: bool) -> str:
        """
        Generate a cache key for search results.

        :param query: Search query
        :param time_period: Time period filter
        :param use_tor: Whether Tor is being used
        :return: Cache key string
        """
        return f"search:{query}:{time_period}:{use_tor}"

    @staticmethod
    def get_token_cache_key(use_tor: bool) -> str:
        """
        Generate a cache key for session tokens.

        :param use_tor: Whether Tor is being used
        :return: Cache key string
        """
        return f"token:{'tor' if use_tor else 'clearnet'}"

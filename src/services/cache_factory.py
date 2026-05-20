"""Cache factory - creates persistent cache based on configuration."""

from contextlib import contextmanager  # Add this import!
from typing import Optional

from loguru import logger

from src.config import get_settings

settings = get_settings()


class BaseCache:
    """Base cache interface."""

    def get(self, key: str) -> Optional[dict]:
        raise NotImplementedError

    def set(self, key: str, value: dict, ttl: Optional[int] = None):
        raise NotImplementedError

    def delete(self, key: str):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def get_stats(self) -> dict:
        raise NotImplementedError


class JSONCache(BaseCache):
    """JSON file-based persistent cache."""

    def __init__(self, cache_file: str = "cache.json"):
        from pathlib import Path
        from threading import Lock

        self.cache_file = Path(cache_file)
        self.max_size_mb = settings.JSON_CACHE_MAX_SIZE_MB or 100
        self.backup_count = settings.JSON_CACHE_BACKUP_COUNT or 3
        self._lock = Lock()
        self._cache: dict = {}
        self._load()
        logger.info(f"JSONCache initialized: {cache_file}")

    def _load(self):
        import json

        if not self.cache_file.exists():
            self._cache = {}
            return

        try:
            with open(self.cache_file, "r") as f:
                self._cache = json.load(f)
            logger.info(f"Loaded {len(self._cache)} entries from {self.cache_file}")
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            self._cache = {}

    def _save(self):
        import json

        with self._lock:
            temp_file = self.cache_file.with_suffix(".tmp")
            try:
                with open(temp_file, "w") as f:
                    json.dump(self._cache, f, indent=2)
                temp_file.replace(self.cache_file)
            except Exception as e:
                logger.error(f"Failed to save cache: {e}")
                if temp_file.exists():
                    temp_file.unlink()

    def get(self, key: str) -> Optional[dict]:
        return self._cache.get(key)

    def set(self, key: str, value: dict, ttl: Optional[int] = None):
        self._cache[key] = value
        self._save()

    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]
            self._save()

    def clear(self):
        self._cache = {}
        self._save()
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("JSONCache cleared")

    def get_stats(self) -> dict:
        size_mb = 0
        if self.cache_file.exists():
            size_mb = self.cache_file.stat().st_size / (1024 * 1024)

        return {
            "type": "json",
            "total_keys": len(self._cache),
            "file_size_mb": int(round(size_mb, 2)),
            "max_size_mb": self.max_size_mb,
            "cache_file": str(self.cache_file),
        }


class SQLiteCache(BaseCache):
    """SQLite-based persistent cache."""

    def __init__(self, db_path: str = "cache.db"):

        self.db_path = db_path
        self._init_db()
        logger.info(f"SQLiteCache initialized: {db_path}")

    def _init_db(self):

        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    @contextmanager
    def _get_connection(self):
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def get(self, key: str) -> Optional[dict]:
        import json

        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM cache WHERE key = ?", (key,)
            ).fetchone()

            if row:
                return json.loads(row["value"])
            return None

    def set(self, key: str, value: dict, ttl: Optional[int] = None):
        import json

        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
                (key, json.dumps(value)),
            )

    def delete(self, key: str):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))

    def clear(self):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM cache")
        logger.info("SQLiteCache cleared")

    def get_stats(self) -> dict:
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            return {"type": "sqlite", "total_keys": total, "db_path": self.db_path}



def create_cache() -> BaseCache:
    """Factory function to create the appropriate cache backend."""
    backend = (settings.CACHE_BACKEND or "json").lower()
    if backend == "sqlite":
        return SQLiteCache("cache.db")
    else:  # json (default)
        return JSONCache("persistent_cache.json")

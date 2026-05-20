"""Initialize requests-cache without modifying ai/ files."""

import os
from typing import Optional

from loguru import logger

from src.config import get_settings

_cache_initialized = False
_settings = None


def _get_settings():
    """Get settings instance (lazy loading)."""
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings


def setup_http_cache(
    cache_name: str = "nutrition_cache",
    expire_after: Optional[int] = None,
    allowed_domains: Optional[list] = None,
    cache_dir: Optional[str] = None,
):
    """Setup HTTP cache with requests-cache."""
    global _cache_initialized

    if _cache_initialized:
        logger.debug("HTTP cache already initialized, skipping")
        return

    settings = _get_settings()

    if not getattr(settings, "HTTP_CACHE_ENABLED", True):
        logger.info("HTTP cache disabled via HTTP_CACHE_ENABLED=false")
        return

    if expire_after is None:
        expire_after = getattr(settings, "HTTP_CACHE_TTL_SECONDS", 86400)

    try:
        import requests_cache
    except ImportError:
        logger.warning(
            "requests-cache not installed. HTTP caching disabled. "
            "Install with: pip install requests-cache"
        )
        return

    try:
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, cache_name)
        else:
            cache_path = cache_name

        if allowed_domains:
            requests_cache.install_cache(
                cache_name=cache_path,
                expire_after=expire_after,
                allowable_methods=["GET"],
                stale_if_error=True,
                ignored_parameters=["api_key", "pageSize", "pageNumber"],
                urls_expire_after={domain: expire_after for domain in allowed_domains},
            )
        else:
            requests_cache.install_cache(
                cache_name=cache_path,
                expire_after=expire_after,
                allowable_methods=["GET"],
                stale_if_error=True,
                ignored_parameters=["api_key", "pageSize", "pageNumber"],
            )

        _cache_initialized = True
        logger.info(
            f"HTTP cache initialized: {cache_path}.sqlite (TTL: {expire_after}s)"
        )

        if allowed_domains:
            logger.info(f"Caching enabled for domains: {allowed_domains}")

    except PermissionError as e:
        logger.error(f"Permission denied creating cache directory: {e}")
    except OSError as e:
        logger.error(f"OS error creating cache directory: {e}")
    except ValueError as e:
        logger.error(f"Invalid cache configuration value: {e}")
    except TypeError as e:
        logger.error(f"Invalid cache configuration type: {e}")
    except Exception as e:
        logger.error(
            f"Unexpected error initializing HTTP cache: {type(e).__name__}: {e}"
        )


def get_cache_stats():
    """Get cache statistics if available."""
    if not _cache_initialized:
        settings = _get_settings()
        if not getattr(settings, "HTTP_CACHE_ENABLED", True):
            return {"status": "disabled", "reason": "HTTP_CACHE_ENABLED=false"}
        return None

    try:
        import requests_cache
    except ImportError:
        logger.error("requests-cache module not available for stats retrieval")
        return None

    try:
        session = requests_cache.get_cache()
        if not session:
            logger.debug("No cache session available")
            return None

        settings = _get_settings()
        ttl_seconds = getattr(settings, "HTTP_CACHE_TTL_SECONDS", 86400)

        try:
            import sqlite3
        except ImportError:
            logger.warning("sqlite3 not available, cannot get detailed cache stats")
            return {
                "status": "enabled",
                "cache_type": "requests-cache",
                "ttl_seconds": ttl_seconds,
            }

        try:
            if hasattr(session, "db_path") and session.db_path:
                conn = sqlite3.connect(session.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM responses")
                count = cursor.fetchone()[0]
                conn.close()

                return {
                    "status": "enabled",
                    "cache_file": session.db_path,
                    "response_count": count,
                    "cache_type": "SQLite (requests-cache)",
                    "ttl_seconds": ttl_seconds,
                }
        except sqlite3.OperationalError as e:
            logger.error(f"SQLite operational error reading cache: {e}")
        except sqlite3.DatabaseError as e:
            logger.error(f"SQLite database error reading cache: {e}")
        except AttributeError as e:
            logger.debug(f"Cache session missing expected attribute: {e}")

        return {
            "status": "enabled",
            "cache_type": "requests-cache",
            "ttl_seconds": ttl_seconds,
        }

    except AttributeError as e:
        logger.error(f"Cache session attribute error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting cache stats: {type(e).__name__}: {e}")
        return None


def clear_cache():
    """Clear the HTTP cache."""
    if not _cache_initialized:
        settings = _get_settings()
        if not getattr(settings, "HTTP_CACHE_ENABLED", True):
            logger.warning("Cache is disabled, nothing to clear")
            return False
        logger.warning("Cache not initialized, nothing to clear")
        return False

    try:
        import requests_cache
    except ImportError:
        logger.error("requests-cache not installed, cannot clear cache")
        return False

    try:
        requests_cache.clear()
        logger.info("HTTP cache cleared")
        return True
    except PermissionError as e:
        logger.error(f"Permission denied clearing cache: {e}")
        return False
    except OSError as e:
        logger.error(f"OS error clearing cache file: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error clearing cache: {type(e).__name__}: {e}")
        return False

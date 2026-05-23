# # src/database/async_database.py
# import json
# from contextlib import asynccontextmanager
# from typing import Any, Dict, List, Optional

# import asyncpg
# from loguru import logger

# from src.config import get_settings

# settings = get_settings()


# class Database:
#     """Async PostgreSQL database handler using asyncpg with connection pooling."""

#     _pool: Optional[asyncpg.Pool] = None
#     _initialized: bool = False
#     _enabled: bool = True

#     @classmethod
#     async def init_pool(cls, min_size: int = 1, max_size: int = 10) -> bool:
#         """Initialize the connection pool and database tables."""
#         if cls._pool is not None:
#             return True

#         if not cls._enabled:
#             return False

#         try:
#             logger.info(
#                 f"Initializing async database pool (min={min_size}, max={max_size})"
#             )
#             cls._pool = await asyncpg.create_pool(
#                 dsn=settings.DATABASE_URL,
#                 min_size=min_size,
#                 max_size=max_size,
#                 command_timeout=60,
#             )

#             # Initialize tables once after pool is ready
#             await cls._init_tables()
#             cls._initialized = True
#             logger.info("✅ Async database pool initialized successfully")
#             return True

#         except Exception as e:
#             logger.error(f"❌ Failed to initialize async database: {e}")
#             cls._enabled = False
#             return False

#     @classmethod
#     async def _init_tables(cls):
#         """Create database tables if they don't exist (idempotent)."""
#         if cls._pool is None:
#             raise RuntimeError("Pool not initialized. Call init_pool() first.")

#         async with cls._pool.acquire() as conn:
#             async with conn.transaction():
#                 await conn.execute("""
#                     CREATE TABLE IF NOT EXISTS analyses (
#                         id SERIAL PRIMARY KEY,
#                         image_path TEXT NOT NULL,
#                         ingredients JSONB NOT NULL,
#                         total_kcal DOUBLE PRECISION,
#                         total_protein_g DOUBLE PRECISION,
#                         total_carbs_g DOUBLE PRECISION,
#                         total_fat_g DOUBLE PRECISION,
#                         meal_recognized BOOLEAN,
#                         created_at TIMESTAMPTZ DEFAULT NOW()
#                     )
#                 """)

#                 await conn.execute("""
#                     CREATE INDEX IF NOT EXISTS idx_analyses_created_at
#                     ON analyses (created_at DESC)
#                 """)

#                 # Optional: Add GIN index for JSONB queries if you search inside ingredients
#                 await conn.execute("""
#                     CREATE INDEX IF NOT EXISTS idx_analyses_ingredients_gin
#                     ON analyses USING GIN (ingredients)
#                 """)

#         logger.info("Database tables verified/created")

#     @classmethod
#     @asynccontextmanager
#     async def get_connection(cls):
#         """Async context manager for acquiring a connection from the pool."""
#         if not cls._enabled or cls._pool is None:
#             raise RuntimeError("Database not initialized. Call init_pool() first.")

#         conn = await cls._pool.acquire()
#         try:
#             yield conn
#         finally:
#             await cls._pool.release(conn)

#     @classmethod
#     async def save(
#         cls,
#         image_path: str,
#         ingredients: List[Dict[str, Any]],
#         totals: Dict[str, Optional[float]],
#         meal_recognized: bool,
#     ) -> Optional[int]:
#         """Save analysis results to database (async)."""
#         if not cls._enabled or cls._pool is None:
#             logger.warning("Database not available, skipping save")
#             return None

#         # Convert ingredients list to JSON string
#         ingredients_json = json.dumps(ingredients)  # ← Add this conversion

#         def safe_float(value: Optional[float]) -> float:
#             try:
#                 return float(value) if value is not None else 0.0
#             except (TypeError, ValueError):
#                 return 0.0

#         try:
#             async with cls.get_connection() as conn:
#                 async with conn.transaction():
#                     row = await conn.fetchrow(
#                         """
#                         INSERT INTO analyses (
#                             image_path,
#                             ingredients,
#                             total_kcal,
#                             total_protein_g,
#                             total_carbs_g,
#                             total_fat_g,
#                             meal_recognized
#                         )
#                         VALUES ($1, $2, $3, $4, $5, $6, $7)
#                         RETURNING id
#                         """,
#                         image_path,
#                         ingredients_json,  # ← Use JSON string, not the list
#                         safe_float(totals.get("kcal")),
#                         safe_float(totals.get("protein_g")),
#                         safe_float(totals.get("carbs_g")),
#                         safe_float(totals.get("fat_g")),
#                         bool(meal_recognized),
#                     )

#                     analysis_id = row["id"] if row else None

#                     if analysis_id:
#                         logger.info(f"✅ Analysis saved with ID: {analysis_id}")
#                     else:
#                         logger.warning("Analysis save returned no ID")

#                     return analysis_id

#         except asyncpg.PostgresError as e:
#             logger.error(f"PostgreSQL error saving analysis: {e}")
#             return None
#         except Exception as e:
#             logger.error(f"Unexpected error saving analysis: {e}")
#             return None

#     @classmethod
#     async def get_by_id(cls, analysis_id: int) -> Optional[Dict[str, Any]]:
#         """Retrieve analysis by ID (async)."""
#         if not cls._enabled or cls._pool is None:
#             return None

#         try:
#             async with cls.get_connection() as conn:
#                 row = await conn.fetchrow(
#                     "SELECT * FROM analyses WHERE id = $1", analysis_id
#                 )
#                 return dict(row) if row else None
#         except Exception as e:
#             logger.error(f"Failed to get analysis by ID {analysis_id}: {e}")
#             return None

#     @classmethod
#     async def get_last_n(cls, limit: int = 10) -> List[Dict[str, Any]]:
#         """Get last N analyses ordered by created_at DESC (async)."""
#         if not cls._enabled or cls._pool is None:
#             return []

#         try:
#             async with cls.get_connection() as conn:
#                 rows = await conn.fetch(
#                     "SELECT * FROM analyses ORDER BY created_at DESC LIMIT $1", limit
#                 )
#                 return [dict(row) for row in rows]
#         except Exception as e:
#             logger.error(f"Failed to get last {limit} analyses: {e}")
#             return []

#     @classmethod
#     async def get_last_10(cls) -> List[Dict[str, Any]]:
#         """Convenience method: Get last 10 analyses."""
#         return await cls.get_last_n(10)

#     @classmethod
#     async def health_check(cls) -> bool:
#         """Check if database is reachable and responsive."""
#         if not cls._enabled or cls._pool is None:
#             return False

#         try:
#             async with cls.get_connection() as conn:
#                 await conn.fetchval("SELECT 1")
#                 return True
#         except Exception as e:
#             logger.warning(f"Health check failed: {e}")
#             return False

#     @classmethod
#     async def close(cls):
#         """Gracefully close the connection pool."""
#         if cls._pool is not None:
#             await cls._pool.close()
#             cls._pool = None
#             cls._initialized = False
#             logger.info("🔌 Async database pool closed")

#     @classmethod
#     def is_enabled(cls) -> bool:
#         """Check if database operations are enabled."""
#         return cls._enabled

#     @classmethod
#     async def __aenter__(cls):
#         """Async context manager entry - for use with 'async with AsyncDatabase'."""
#         await cls.init_pool()
#         return cls

#     @classmethod
#     async def __aexit__(cls, exc_type, exc_val, exc_tb):
#         """Async context manager exit - ensures cleanup."""
#         await cls.close()
#         return False  # Don't suppress exceptions






























"""Async PostgreSQL database handler using asyncpg with connection pooling."""

import json
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import asyncpg
from loguru import logger

from src.config import get_settings
from src.telemetry import get_tracer

settings = get_settings()
tracer = get_tracer()


class Database:
    """Async PostgreSQL database handler using asyncpg with connection pooling."""

    _pool: Optional[asyncpg.Pool] = None
    _initialized: bool = False
    _enabled: bool = True

    @classmethod
    async def init_pool(cls, min_size: int = 1, max_size: int = 10) -> bool:
        """Initialize the connection pool and database tables."""
        with tracer.start_as_current_span("database.init_pool") as span:
            span.set_attribute("min_size", min_size)
            span.set_attribute("max_size", max_size)

            if cls._pool is not None:
                return True

            if not cls._enabled:
                return False

            try:
                logger.info(f"Initializing async database pool (min={min_size}, max={max_size})")
                cls._pool = await asyncpg.create_pool(
                    dsn=settings.DATABASE_URL,
                    min_size=min_size,
                    max_size=max_size,
                    command_timeout=60,
                )

                await cls._init_tables()
                cls._initialized = True
                logger.info("✅ Async database pool initialized successfully")
                return True

            except Exception as e:
                logger.error(f"❌ Failed to initialize async database: {e}")
                cls._enabled = False
                span.record_exception(e)
                return False

    @classmethod
    async def _init_tables(cls):
        """Create database tables if they don't exist (idempotent)."""
        with tracer.start_as_current_span("database.init_tables"):
            if cls._pool is None:
                raise RuntimeError("Pool not initialized. Call init_pool() first.")

            async with cls._pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS analyses (
                            id SERIAL PRIMARY KEY,
                            image_path TEXT NOT NULL,
                            ingredients JSONB NOT NULL,
                            total_kcal DOUBLE PRECISION,
                            total_protein_g DOUBLE PRECISION,
                            total_carbs_g DOUBLE PRECISION,
                            total_fat_g DOUBLE PRECISION,
                            meal_recognized BOOLEAN,
                            created_at TIMESTAMPTZ DEFAULT NOW()
                        )
                    """)

                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_analyses_created_at
                        ON analyses (created_at DESC)
                    """)

                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_analyses_ingredients_gin
                        ON analyses USING GIN (ingredients)
                    """)

            logger.info("Database tables verified/created")

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """Async context manager for acquiring a connection from the pool."""
        if not cls._enabled or cls._pool is None:
            raise RuntimeError("Database not initialized. Call init_pool() first.")

        conn = await cls._pool.acquire()
        try:
            yield conn
        finally:
            await cls._pool.release(conn)

    @classmethod
    async def save(
        cls,
        image_path: str,
        ingredients: List[Dict[str, Any]],
        totals: Dict[str, Optional[float]],
        meal_recognized: bool,
    ) -> Optional[int]:
        """Save analysis results to database (async)."""
        with tracer.start_as_current_span("database.save") as span:
            span.set_attribute("image_path", image_path)
            span.set_attribute("num_ingredients", len(ingredients))
            span.set_attribute("meal_recognized", meal_recognized)
            span.set_attribute("total_kcal", totals.get("kcal", 0))

            if not cls._enabled or cls._pool is None:
                logger.warning("Database not available, skipping save")
                span.set_attribute("skipped", True)
                return None

            ingredients_json = json.dumps(ingredients)

            def safe_float(value: Optional[float]) -> float:
                try:
                    return float(value) if value is not None else 0.0
                except (TypeError, ValueError):
                    return 0.0

            try:
                async with cls.get_connection() as conn:
                    async with conn.transaction():
                        row = await conn.fetchrow(
                            """
                            INSERT INTO analyses (
                                image_path,
                                ingredients,
                                total_kcal,
                                total_protein_g,
                                total_carbs_g,
                                total_fat_g,
                                meal_recognized
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            RETURNING id
                            """,
                            image_path,
                            ingredients_json,
                            safe_float(totals.get("kcal")),
                            safe_float(totals.get("protein_g")),
                            safe_float(totals.get("carbs_g")),
                            safe_float(totals.get("fat_g")),
                            bool(meal_recognized),
                        )

                        analysis_id = row["id"] if row else None

                        if analysis_id:
                            logger.info(f"✅ Analysis saved with ID: {analysis_id}")
                            span.set_attribute("saved_id", analysis_id)
                        else:
                            logger.warning("Analysis save returned no ID")

                        return analysis_id

            except asyncpg.PostgresError as e:
                logger.error(f"PostgreSQL error saving analysis: {e}")
                span.record_exception(e)
                return None
            except Exception as e:
                logger.error(f"Unexpected error saving analysis: {e}")
                span.record_exception(e)
                return None

    @classmethod
    async def get_by_id(cls, analysis_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve analysis by ID (async)."""
        with tracer.start_as_current_span("database.get_by_id") as span:
            span.set_attribute("analysis_id", analysis_id)

            if not cls._enabled or cls._pool is None:
                span.set_attribute("skipped", True)
                return None

            try:
                async with cls.get_connection() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM analyses WHERE id = $1", analysis_id
                    )
                    result = dict(row) if row else None
                    span.set_attribute("found", result is not None)
                    return result
            except Exception as e:
                logger.error(f"Failed to get analysis by ID {analysis_id}: {e}")
                span.record_exception(e)
                return None

    @classmethod
    async def get_last_n(cls, limit: int = 10) -> List[Dict[str, Any]]:
        """Get last N analyses ordered by created_at DESC (async)."""
        with tracer.start_as_current_span("database.get_last_n") as span:
            span.set_attribute("limit", limit)

            if not cls._enabled or cls._pool is None:
                span.set_attribute("skipped", True)
                return []

            try:
                async with cls.get_connection() as conn:
                    rows = await conn.fetch(
                        "SELECT * FROM analyses ORDER BY created_at DESC LIMIT $1", limit
                    )
                    result = [dict(row) for row in rows]
                    span.set_attribute("returned_count", len(result))
                    return result
            except Exception as e:
                logger.error(f"Failed to get last {limit} analyses: {e}")
                span.record_exception(e)
                return []

    @classmethod
    async def get_last_10(cls) -> List[Dict[str, Any]]:
        """Convenience method: Get last 10 analyses."""
        return await cls.get_last_n(10)

    @classmethod
    async def health_check(cls) -> bool:
        """Check if database is reachable and responsive."""
        with tracer.start_as_current_span("database.health_check"):
            if not cls._enabled or cls._pool is None:
                return False

            try:
                async with cls.get_connection() as conn:
                    await conn.fetchval("SELECT 1")
                    return True
            except Exception as e:
                logger.warning(f"Health check failed: {e}")
                return False

    @classmethod
    async def close(cls):
        """Gracefully close the connection pool."""
        with tracer.start_as_current_span("database.close"):
            if cls._pool is not None:
                await cls._pool.close()
                cls._pool = None
                cls._initialized = False
                logger.info("🔌 Async database pool closed")

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if database operations are enabled."""
        return cls._enabled

    @classmethod
    async def __aenter__(cls):
        """Async context manager entry - for use with 'async with AsyncDatabase'."""
        await cls.init_pool()
        return cls

    @classmethod
    async def __aexit__(cls, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures cleanup."""
        await cls.close()
        return False  # Don't suppress exceptions

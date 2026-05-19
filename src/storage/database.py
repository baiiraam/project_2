import json
import asyncpg
from typing import List, Dict, Optional
from src.config import Settings

import logging

logger = logging.getLogger(__name__)


settings = Settings()


class Database:
    _conn = None

    @classmethod
    async def get_connection(cls):
        if cls._conn is None:
            cls._conn = await asyncpg.connect(settings.DATABASE_URL)
            await cls._init_table()
        return cls._conn

    @classmethod
    async def _init_table(cls):
        if cls._conn is None:
            raise RuntimeError("Database connection not established")
        await cls._conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id SERIAL PRIMARY KEY,
                image_path TEXT NOT NULL,
                ingredients JSONB NOT NULL,
                total_kcal FLOAT,
                total_protein_g FLOAT,
                total_carbs_g FLOAT,
                total_fat_g FLOAT,
                meal_recognized BOOLEAN,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

    @classmethod
    async def save(
        cls, image_path: str, ingredients: list, totals: dict, meal_recognized: bool
    ):
        conn = await cls.get_connection()
        ingredients_json = json.dumps(ingredients)

        # Use fetchrow() instead of execute() when you need RETURNING values
        row = await conn.fetchrow(
            """
            INSERT INTO analyses (image_path, ingredients, total_kcal, total_protein_g, total_carbs_g, total_fat_g, meal_recognized)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
            """,
            image_path,
            ingredients_json,
            totals.get("kcal"),
            totals.get("protein_g"),
            totals.get("carbs_g"),
            totals.get("fat_g"),
            meal_recognized,
        )

        analysis_id = row[0] if row else None
        logger.info(f"Analysis saved to database with ID: {analysis_id}")

        return analysis_id

    @classmethod
    async def get_by_id(cls, analysis_id: int) -> Optional[Dict]:
        conn = await cls.get_connection()
        row = await conn.fetchrow("SELECT * FROM analyses WHERE id = $1", analysis_id)
        return dict(row) if row else None

    @classmethod
    async def get_last_10(cls) -> List[Dict]:
        conn = await cls.get_connection()
        rows = await conn.fetch(
            "SELECT * FROM analyses ORDER BY created_at DESC LIMIT 10"
        )
        return [dict(row) for row in rows]

    @classmethod
    async def close(cls):
        if cls._conn:
            await cls._conn.close()
            cls._conn = None

"""Cost telemetry for AI API calls.

Tracks token usage and estimated costs for all VLM/LLM calls.
"""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

from loguru import logger

# Pricing table: (provider, model) -> (prompt_price_per_1k, completion_price_per_1k)
PRICING_USD_PER_1K_TOKENS: Dict[Tuple[str, str], Tuple[float, float]] = {
    # OpenAI models
    ("openai", "gpt-4o-mini"): (0.00015, 0.0006),
    ("openai", "gpt-4o"): (0.005, 0.015),
    ("openai", "gpt-4-turbo"): (0.01, 0.03),

    # Anthropic models
    ("anthropic", "claude-3-5-sonnet-20241022"): (0.003, 0.015),
    ("anthropic", "claude-3-opus"): (0.015, 0.075),
    ("anthropic", "claude-sonnet-4-6"): (0.003, 0.015),

    # Gemini models
    ("gemini", "gemini-2.0-flash"): (0.000075, 0.0003),
    ("gemini", "gemini-1.5-flash"): (0.000075, 0.0003),
    ("gemini", "gemini-1.5-pro"): (0.00125, 0.005),
}

# Default prices for unknown models
DEFAULT_PRICE = (0.001, 0.002)


@dataclass
class CostRecord:
    """Record of a single AI API call cost."""

    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    timestamp: datetime
    prompt_preview: str = ""

    def to_dict(self) -> Dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "timestamp": self.timestamp.isoformat(),
            "prompt_preview": self.prompt_preview[:100],
        }


class CostMeter:
    """Records and reports cost telemetry for AI calls.

    Uses SQLite for storage. Thread-safe.
    """

    def __init__(self, db_path: str = "costs.db"):
        self.db_path = Path(db_path)
        self._init_db()
        logger.info(f"CostMeter initialized with database: {db_path}")

    def _init_db(self) -> None:
        """Initialize SQLite database table."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cost_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    prompt_preview TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON cost_records(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_provider
                ON cost_records(provider)
            """)

    def estimate_cost(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost based on token counts and pricing table."""
        key = (provider.lower(), model.lower())
        prompt_price, completion_price = PRICING_USD_PER_1K_TOKENS.get(key, DEFAULT_PRICE)

        cost = (prompt_tokens / 1000) * prompt_price + (completion_tokens / 1000) * completion_price
        return round(cost, 8)

    def record(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        prompt_preview: str = "",
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Record a cost entry."""
        if timestamp is None:
            timestamp = datetime.now()

        cost_usd = self.estimate_cost(provider, model, prompt_tokens, completion_tokens)

        record = CostRecord(
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
            timestamp=timestamp,
            prompt_preview=prompt_preview[:200],
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO cost_records
                (provider, model, prompt_tokens, completion_tokens, cost_usd, timestamp, prompt_preview)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.provider,
                    record.model,
                    record.prompt_tokens,
                    record.completion_tokens,
                    record.cost_usd,
                    record.timestamp.isoformat(),
                    record.prompt_preview,
                ),
            )

        logger.debug(f"Recorded cost: {provider}/{model} - ${cost_usd:.6f} ({prompt_tokens}+{completion_tokens} tokens)")

    @contextmanager
    def record_context(self, provider: str, model: str, prompt: str = ""):
        """Context manager that automatically records cost.

        Usage:
            with cost_meter.record_context("openai", "gpt-4o-mini", prompt) as ctx:
                result = api_call()
                ctx.prompt_tokens = 1500  # Set after call
                ctx.completion_tokens = 800
        """
        class Context:
            def __init__(self):
                self.prompt_tokens = 0
                self.completion_tokens = 0

        ctx = Context()
        try:
            yield ctx
        finally:
            if ctx.prompt_tokens > 0 or ctx.completion_tokens > 0:
                self.record(
                    provider=provider,
                    model=model,
                    prompt_tokens=ctx.prompt_tokens,
                    completion_tokens=ctx.completion_tokens,
                    prompt_preview=prompt,
                )

    def get_report(
        self,
        since: Optional[timedelta] = None,
        provider: Optional[str] = None,
        limit: int = 50,
    ) -> Dict:
        """Get cost report.

        Args:
            since: Only include records after this time delta
            provider: Filter by provider
            limit: Max number of records to return

        Returns:
            Dictionary with totals and records
        """
        where_clauses = []
        params = []

        if since is not None:
            cutoff = (datetime.now() - since).isoformat()
            where_clauses.append("timestamp >= ?")
            params.append(cutoff)

        if provider is not None:
            where_clauses.append("provider = ?")
            params.append(provider.lower())

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get totals
            cursor = conn.execute(f"""
                SELECT
                    SUM(cost_usd) as total_cost,
                    SUM(prompt_tokens) as total_prompt_tokens,
                    SUM(completion_tokens) as total_completion_tokens,
                    COUNT(*) as total_calls
                FROM cost_records
                WHERE {where_sql}
            """, params)
            totals = dict(cursor.fetchone())

            # Get breakdown by provider
            cursor = conn.execute(f"""
                SELECT
                    provider,
                    SUM(cost_usd) as cost,
                    COUNT(*) as calls
                FROM cost_records
                WHERE {where_sql}
                GROUP BY provider
                ORDER BY cost DESC
            """, params)
            by_provider = [dict(row) for row in cursor.fetchall()]

            # Get breakdown by model
            cursor = conn.execute(f"""
                SELECT
                    model,
                    SUM(cost_usd) as cost,
                    COUNT(*) as calls
                FROM cost_records
                WHERE {where_sql}
                GROUP BY model
                ORDER BY cost DESC
            """, params)
            by_model = [dict(row) for row in cursor.fetchall()]

            # Get most expensive prompts
            cursor = conn.execute(f"""
                SELECT
                    id, provider, model, prompt_tokens, completion_tokens,
                    cost_usd, timestamp, prompt_preview
                FROM cost_records
                WHERE {where_sql}
                ORDER BY cost_usd DESC
                LIMIT ?
            """, params + [limit])
            top_prompts = [dict(row) for row in cursor.fetchall()]

        return {
            "totals": {
                "total_cost_usd": round(totals["total_cost"] or 0, 6),
                "total_prompt_tokens": totals["total_prompt_tokens"] or 0,
                "total_completion_tokens": totals["total_completion_tokens"] or 0,
                "total_calls": totals["total_calls"] or 0,
            },
            "by_provider": by_provider,
            "by_model": by_model,
            "top_prompts": top_prompts,
        }

    def clear(self) -> None:
        """Clear all cost records."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cost_records")
        logger.info("Cost records cleared")


_cost_meter_instance: Optional[CostMeter] = None


def get_cost_meter() -> CostMeter:
    """Get singleton CostMeter instance."""
    global _cost_meter_instance
    if _cost_meter_instance is None:
        _cost_meter_instance = CostMeter()
    return _cost_meter_instance

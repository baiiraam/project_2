"""Tests for database storage operations."""

import json
from unittest.mock import AsyncMock, Mock

import pytest

from src.storage.database import Database

pytestmark = pytest.mark.asyncio


class TestDatabaseInit:
    """Test database connection pool initialization."""

    async def test_init_pool_success(self, mocker):
        """Test successful pool initialization."""
        mock_pool = AsyncMock()

        # Create an awaitable mock for create_pool
        async def mock_create_pool(*args, **kwargs):
            return mock_pool

        mocker.patch("asyncpg.create_pool", side_effect=mock_create_pool)
        mocker.patch(
            "src.storage.database.settings.DATABASE_URL",
            "postgresql://test:test@localhost/test",
        )

        # Mock _init_tables to avoid actual table creation
        mocker.patch.object(Database, "_init_tables", new=AsyncMock())

        # Reset state
        Database._pool = None
        Database._enabled = True
        Database._initialized = False

        result = await Database.init_pool(min_size=1, max_size=5)

        assert result is True
        assert Database._pool == mock_pool

    async def test_init_pool_already_initialized(self, mocker):
        """Test that pool isn't re-initialized if already exists."""
        mock_pool = AsyncMock()
        Database._pool = mock_pool

        result = await Database.init_pool()

        assert result is True

    async def test_init_pool_disabled(self, mocker):
        """Test init when database is explicitly disabled."""
        Database._enabled = False
        Database._pool = None

        result = await Database.init_pool()

        assert result is False

    async def test_init_pool_failure(self, mocker):
        """Test pool initialization failure."""

        async def mock_create_pool_fail(*args, **kwargs):
            raise Exception("Connection failed")

        mocker.patch("asyncpg.create_pool", side_effect=mock_create_pool_fail)
        mocker.patch(
            "src.storage.database.settings.DATABASE_URL",
            "postgresql://test:test@localhost/test",
        )

        Database._pool = None
        Database._enabled = True

        result = await Database.init_pool()

        assert result is False
        assert Database._enabled is False


class TestDatabaseTables:
    """Test table creation."""

    async def test_init_tables_creates_tables(self, mocker):
        """Test that _init_tables creates required tables."""
        mock_conn = AsyncMock()

        # Mock the connection and transaction
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = Mock(return_value=mock_transaction)

        # Mock pool.acquire context manager
        mock_acquire_cm = AsyncMock()
        mock_acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_cm.__aexit__ = AsyncMock(return_value=None)

        mock_pool = AsyncMock()
        mock_pool.acquire = Mock(return_value=mock_acquire_cm)

        Database._pool = mock_pool

        await Database._init_tables()

        # Verify execute was called for table creation
        assert mock_conn.execute.call_count >= 3


class TestDatabaseSave:
    """Test saving analyses to database."""

    async def test_save_analysis_success(self, mocker):
        """Test successful save of analysis results."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={"id": 123})

        # Mock transaction
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = Mock(return_value=mock_transaction)

        # Mock get_connection context manager
        mock_get_conn_cm = AsyncMock()
        mock_get_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_conn_cm.__aexit__ = AsyncMock(return_value=None)

        mocker.patch.object(Database, "get_connection", return_value=mock_get_conn_cm)

        Database._pool = AsyncMock()
        Database._enabled = True

        ingredients = [
            {"name": "rice", "estimated_grams": 100, "confidence": 0.9},
            {"name": "chicken", "estimated_grams": 150, "confidence": 0.85},
        ]
        totals = {"kcal": 250, "protein_g": 30, "carbs_g": 40, "fat_g": 10}

        analysis_id = await Database.save(
            image_path="test.jpg",
            ingredients=ingredients,
            totals=totals,
            meal_recognized=True,
        )

        assert analysis_id == 123
        mock_conn.fetchrow.assert_called_once()

    async def test_save_analysis_database_disabled(self, mocker):
        """Test save when database is disabled."""
        Database._enabled = False
        Database._pool = None

        result = await Database.save("test.jpg", [], {}, False)

        assert result is None

    async def test_save_analysis_no_pool(self, mocker):
        """Test save when pool doesn't exist."""
        Database._enabled = True
        Database._pool = None

        result = await Database.save("test.jpg", [], {}, False)

        assert result is None

    async def test_save_analysis_with_empty_ingredients(self, mocker):
        """Test saving analysis with no ingredients."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={"id": 456})

        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = Mock(return_value=mock_transaction)

        mock_get_conn_cm = AsyncMock()
        mock_get_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_conn_cm.__aexit__ = AsyncMock(return_value=None)

        mocker.patch.object(Database, "get_connection", return_value=mock_get_conn_cm)

        Database._pool = AsyncMock()
        Database._enabled = True

        result = await Database.save(
            image_path="empty.jpg",
            ingredients=[],
            totals={"kcal": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0},
            meal_recognized=False,
        )

        assert result == 456

    async def test_save_handles_none_totals(self, mocker):
        """Test save handles None values in totals."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={"id": 789})

        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = Mock(return_value=mock_transaction)

        mock_get_conn_cm = AsyncMock()
        mock_get_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_conn_cm.__aexit__ = AsyncMock(return_value=None)

        mocker.patch.object(Database, "get_connection", return_value=mock_get_conn_cm)

        Database._pool = AsyncMock()
        Database._enabled = True

        result = await Database.save(
            image_path="test.jpg",
            ingredients=[],
            totals={"kcal": None, "protein_g": None, "carbs_g": None, "fat_g": None},
            meal_recognized=False,
        )

        assert result == 789

    async def test_save_database_error(self, mocker):
        """Test save when database raises an error."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(side_effect=Exception("DB Error"))

        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = Mock(return_value=mock_transaction)

        mock_get_conn_cm = AsyncMock()
        mock_get_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_conn_cm.__aexit__ = AsyncMock(return_value=None)

        mocker.patch.object(Database, "get_connection", return_value=mock_get_conn_cm)

        Database._pool = AsyncMock()
        Database._enabled = True

        result = await Database.save(
            "test.jpg", [{"name": "rice"}], {"kcal": 100}, True
        )

        assert result is None


class TestDatabaseRetrieve:
    """Test retrieving analyses from database."""

    async def test_get_by_id_success(self, mocker):
        """Test retrieving analysis by ID."""
        expected_row = {
            "id": 1,
            "image_path": "test.jpg",
            "ingredients": '[{"name": "rice", "estimated_grams": 100}]',
            "total_kcal": 250.0,
            "created_at": "2024-01-01T00:00:00",
        }

        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=expected_row)

        mock_get_conn_cm = AsyncMock()
        mock_get_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_conn_cm.__aexit__ = AsyncMock(return_value=None)

        mocker.patch.object(Database, "get_connection", return_value=mock_get_conn_cm)

        Database._pool = AsyncMock()
        Database._enabled = True

        result = await Database.get_by_id(1)

        assert result is not None
        assert result["id"] == 1
        assert result["image_path"] == "test.jpg"

    async def test_get_by_id_not_found(self, mocker):
        """Test retrieving non-existent ID returns None."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)

        mock_get_conn_cm = AsyncMock()
        mock_get_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_conn_cm.__aexit__ = AsyncMock(return_value=None)

        mocker.patch.object(Database, "get_connection", return_value=mock_get_conn_cm)

        Database._pool = AsyncMock()
        Database._enabled = True

        result = await Database.get_by_id(999)

        assert result is None

    async def test_get_by_id_database_disabled(self, mocker):
        """Test get_by_id when database is disabled."""
        Database._enabled = False
        Database._pool = None

        result = await Database.get_by_id(1)

        assert result is None

    async def test_get_last_n_success(self, mocker):
        """Test retrieving last N analyses."""
        expected_rows = [
            {"id": 3, "image_path": "test3.jpg", "total_kcal": 300},
            {"id": 2, "image_path": "test2.jpg", "total_kcal": 200},
            {"id": 1, "image_path": "test1.jpg", "total_kcal": 100},
        ]

        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=expected_rows)

        mock_get_conn_cm = AsyncMock()
        mock_get_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_conn_cm.__aexit__ = AsyncMock(return_value=None)

        mocker.patch.object(Database, "get_connection", return_value=mock_get_conn_cm)

        Database._pool = AsyncMock()
        Database._enabled = True

        results = await Database.get_last_n(3)

        assert len(results) == 3
        assert results[0]["id"] == 3

    async def test_get_last_n_empty(self, mocker):
        """Test get_last_n when no records exist."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])

        mock_get_conn_cm = AsyncMock()
        mock_get_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_conn_cm.__aexit__ = AsyncMock(return_value=None)

        mocker.patch.object(Database, "get_connection", return_value=mock_get_conn_cm)

        Database._pool = AsyncMock()
        Database._enabled = True

        results = await Database.get_last_n(5)

        assert results == []

    async def test_get_last_n_database_disabled(self, mocker):
        """Test get_last_n when database is disabled."""
        Database._enabled = False
        Database._pool = None

        results = await Database.get_last_n(5)

        assert results == []

    async def test_get_last_10_convenience(self, mocker):
        """Test get_last_10 convenience method."""
        mock_get_last_n = mocker.patch.object(
            Database, "get_last_n", new=AsyncMock(return_value=[])
        )

        await Database.get_last_10()

        mock_get_last_n.assert_called_with(10)


class TestDatabaseHealth:
    """Test database health checks."""

    async def test_health_check_success(self, mocker):
        """Test health check when database is responsive."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)

        mock_get_conn_cm = AsyncMock()
        mock_get_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_conn_cm.__aexit__ = AsyncMock(return_value=None)

        mocker.patch.object(Database, "get_connection", return_value=mock_get_conn_cm)

        Database._pool = AsyncMock()
        Database._enabled = True

        result = await Database.health_check()

        assert result is True

    async def test_health_check_failure(self, mocker):
        """Test health check when database is unresponsive."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=Exception("Connection error"))

        mock_get_conn_cm = AsyncMock()
        mock_get_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_conn_cm.__aexit__ = AsyncMock(return_value=None)

        mocker.patch.object(Database, "get_connection", return_value=mock_get_conn_cm)

        Database._pool = AsyncMock()
        Database._enabled = True

        result = await Database.health_check()

        assert result is False

    async def test_health_check_database_disabled(self, mocker):
        """Test health check when database is disabled."""
        Database._enabled = False
        Database._pool = None

        result = await Database.health_check()

        assert result is False

    async def test_health_check_no_pool(self, mocker):
        """Test health check when pool doesn't exist."""
        Database._enabled = True
        Database._pool = None

        result = await Database.health_check()

        assert result is False


class TestDatabaseLifecycle:
    """Test database connection lifecycle."""

    async def test_close_pool(self, mocker):
        """Test graceful pool closure."""
        mock_pool = AsyncMock()
        Database._pool = mock_pool
        Database._initialized = True
        Database._enabled = True

        await Database.close()

        mock_pool.close.assert_called_once()
        assert Database._pool is None
        assert Database._initialized is False

    async def test_close_when_pool_none(self, mocker):
        """Test close when pool doesn't exist."""
        Database._pool = None

        await Database.close()  # Should not raise error

        assert Database._pool is None

    async def test_is_enabled(self, mocker):
        """Test is_enabled method."""
        Database._enabled = True
        assert Database.is_enabled() is True

        Database._enabled = False
        assert Database.is_enabled() is False


class TestDatabaseGetConnection:
    """Test get_connection context manager."""

    async def test_get_connection_success(self, mocker):
        """Test acquiring a connection from the pool."""
        mock_conn = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_pool.release = AsyncMock()

        Database._pool = mock_pool
        Database._enabled = True

        async with Database.get_connection() as conn:
            assert conn == mock_conn

        mock_pool.release.assert_called_once_with(mock_conn)

    async def test_get_connection_not_initialized(self, mocker):
        """Test get_connection when database not initialized."""
        Database._enabled = True
        Database._pool = None

        with pytest.raises(RuntimeError, match="Database not initialized"):
            async with Database.get_connection():
                pass

    async def test_get_connection_disabled(self, mocker):
        """Test get_connection when database is disabled."""
        Database._enabled = False
        Database._pool = AsyncMock()

        with pytest.raises(RuntimeError, match="Database not initialized"):
            async with Database.get_connection():
                pass


class TestDatabaseJSONSerialization:
    """Test JSON serialization of ingredients."""

    async def test_ingredients_json_serialization(self, mocker):
        """Test that ingredients are properly serialized to JSON."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={"id": 1})

        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = Mock(return_value=mock_transaction)

        mock_get_conn_cm = AsyncMock()
        mock_get_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_conn_cm.__aexit__ = AsyncMock(return_value=None)

        mocker.patch.object(Database, "get_connection", return_value=mock_get_conn_cm)

        Database._pool = AsyncMock()
        Database._enabled = True

        ingredients = [
            {"name": "rice", "estimated_grams": 100.5, "confidence": 0.95},
            {
                "name": "chicken with spices",
                "estimated_grams": 150.75,
                "confidence": 0.88,
            },
        ]

        await Database.save("test.jpg", ingredients, {}, True)

        # Verify fetchrow was called
        assert mock_conn.fetchrow.called

        # Get the call arguments
        call_args = mock_conn.fetchrow.call_args[0]
        # The second argument should be the JSON string
        assert len(call_args) >= 3
        # Verify the ingredients_json is a string
        assert isinstance(call_args[2], str)
        # Verify it's valid JSON
        parsed = json.loads(call_args[2])
        assert len(parsed) == 2
        assert parsed[0]["name"] == "rice"

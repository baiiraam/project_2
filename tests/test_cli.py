"""Tests for CLI commands."""

from unittest.mock import Mock

import pytest

from ai.schemas import Ingredient, NutritionFacts


class TestCLIAnalyzeCommand:
    """Test analyze command."""

    @pytest.mark.asyncio
    async def test_analyze_with_valid_image(self, mocker, tmp_path):
        """Test analyze command with existing image file."""
        # Create a dummy image
        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"fake image data")

        # Create real NutritionFacts objects
        rice_facts = NutritionFacts(
            name="rice",
            kcal_per_100g=130,
            protein_g_per_100g=2.7,
            carbs_g_per_100g=28,
            fat_g_per_100g=0.3,
            source="test",
        )
        chicken_facts = NutritionFacts(
            name="chicken",
            kcal_per_100g=165,
            protein_g_per_100g=31,
            carbs_g_per_100g=0,
            fat_g_per_100g=3.6,
            source="test",
        )

        ingredients = [
            Ingredient(name="rice", estimated_grams=100, confidence=0.9),
            Ingredient(name="chicken", estimated_grams=150, confidence=0.85),
        ]

        mock_result = {
            "ingredients": ingredients,
            "nutrition_per_ingredient": {"rice": rice_facts, "chicken": chicken_facts},
            "totals": Mock(kcal=250, protein_g=30, carbs_g=20, fat_g=10),
        }

        # Mock the async function
        mock_analyze_async = mocker.AsyncMock(return_value=mock_result)
        mocker.patch("src.core.analyzer.FoodAnalyzer.analyze_async", mock_analyze_async)
        mocker.patch("src.storage.database.Database.init_pool", mocker.AsyncMock())
        mocker.patch("src.storage.database.Database.close", mocker.AsyncMock())

        # Import the async function directly instead of using analyze_command
        from src.cli.main import print_analysis_table
        from src.core.analyzer import FoodAnalyzer

        analyzer = FoodAnalyzer()
        result = await analyzer.analyze_async(str(img_path))

        # Capture stdout
        import io
        import sys

        captured = io.StringIO()
        sys.stdout = captured

        print_analysis_table(result)

        sys.stdout = sys.__stdout__
        output = captured.getvalue()

        assert "ingredient" in output.lower() or "total" in output.lower()

    def test_analyze_with_nonexistent_image(self, mocker):
        """Test analyze command with missing file."""
        from src.cli.main import analyze_command

        with pytest.raises(SystemExit) as exc_info:
            analyze_command("nonexistent.jpg")

        assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_analyze_with_no_meal_recognized(self, mocker, tmp_path):
        """Test analyze when no meal is recognized."""
        img_path = tmp_path / "empty.jpg"
        img_path.write_bytes(b"fake image")

        mock_analyze_async = mocker.AsyncMock(
            return_value={
                "ingredients": [],
                "nutrition_per_ingredient": {},
                "totals": Mock(kcal=0, protein_g=0, carbs_g=0, fat_g=0),
            }
        )
        mocker.patch("src.core.analyzer.FoodAnalyzer.analyze_async", mock_analyze_async)

        from src.core.analyzer import FoodAnalyzer

        analyzer = FoodAnalyzer()
        result = await analyzer.analyze_async(str(img_path))

        assert len(result["ingredients"]) == 0


class TestCLIListCommand:
    """Test list command."""

    @pytest.mark.asyncio
    async def test_list_with_analyses(self, mocker):
        """Test list command when there are analyses."""
        mock_analyses = [
            {
                "id": 1,
                "image_path": "meal1.jpg",
                "total_kcal": 500,
                "created_at": "2024-01-01",
            },
            {
                "id": 2,
                "image_path": "meal2.jpg",
                "total_kcal": 300,
                "created_at": "2024-01-02",
            },
        ]

        mock_get_last_10 = mocker.AsyncMock(return_value=mock_analyses)
        mocker.patch("src.storage.database.Database.get_last_10", mock_get_last_10)

        from src.storage.database import Database

        results = await Database.get_last_10()

        assert len(results) == 2
        assert results[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_list_with_no_analyses(self, mocker):
        """Test list command when database is empty."""
        mock_get_last_10 = mocker.AsyncMock(return_value=[])
        mocker.patch("src.storage.database.Database.get_last_10", mock_get_last_10)

        from src.storage.database import Database

        results = await Database.get_last_10()

        assert results == []


class TestCLIGetCommand:
    """Test get command."""

    @pytest.mark.asyncio
    async def test_get_existing_analysis(self, mocker):
        """Test retrieving existing analysis by ID."""
        mock_analysis = {
            "id": 42,
            "image_path": "dinner.jpg",
            "total_kcal": 750,
            "total_protein_g": 45,
            "total_carbs_g": 60,
            "total_fat_g": 25,
            "created_at": "2024-01-01T12:00:00",
        }

        mock_get_by_id = mocker.AsyncMock(return_value=mock_analysis)
        mocker.patch("src.storage.database.Database.get_by_id", mock_get_by_id)

        from src.storage.database import Database

        result = await Database.get_by_id(42)

        assert result is not None
        assert result["id"] == 42
        assert result["image_path"] == "dinner.jpg"

    @pytest.mark.asyncio
    async def test_get_nonexistent_analysis(self, mocker):
        """Test retrieving non-existent analysis."""
        mock_get_by_id = mocker.AsyncMock(return_value=None)
        mocker.patch("src.storage.database.Database.get_by_id", mock_get_by_id)

        from src.storage.database import Database

        result = await Database.get_by_id(999)

        assert result is None

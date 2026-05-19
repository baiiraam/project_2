import argparse
import sys
import asyncio
from pathlib import Path

# All imports at top
from src.services.http_cache import setup_http_cache
from src.config import Settings
from src.core.analyzer import FoodAnalyzer
from src.logging_config import setup_logging
from src.storage.database import Database

# Initialize cache (after imports)
settings = Settings()
setup_http_cache(
    cache_name="nutrition_cli_cache",
    expire_after=settings.NUTRITION_CACHE_TTL_SECONDS,
    allowed_domains=["api.nal.usda.gov", "world.openfoodfacts.net"],
    cache_dir=".cache",
)


def print_analysis_table(result):
    ingredients = result["ingredients"]
    nutrition_per_ingredient = result["nutrition_per_ingredient"]

    # Print header
    print(
        f"{'ingredient':<20} {'g':>6} {'kcal':>6} {'protein':>6} {'carbs':>6} {'fat':>6}"
    )
    print("-" * 55)

    # Print each ingredient
    for ingredient in ingredients:
        facts = nutrition_per_ingredient[ingredient.name]
        grams = ingredient.estimated_grams
        kcal = (grams / 100) * facts.kcal_per_100g
        protein = (grams / 100) * facts.protein_g_per_100g
        carbs = (grams / 100) * facts.carbs_g_per_100g
        fat = (grams / 100) * facts.fat_g_per_100g

        print(
            f"{ingredient.name:<20} {grams:>6.0f} {kcal:>6.0f} {protein:>6.1f} {carbs:>6.1f} {fat:>6.1f}"
        )

    # Print separator
    print("-" * 55)

    # Print totals
    totals = result["totals"]
    total_grams = sum(i.estimated_grams for i in ingredients)
    print(
        f"{'TOTAL':<20} {total_grams:>6.0f} {totals.kcal:>6.0f} {totals.protein_g:>6.1f} {totals.carbs_g:>6.1f} {totals.fat_g:>6.1f}"
    )


def analyze_command(image_path):

    path = Path(image_path)
    if not path.is_file():
        print(f"❌ Error: File not found: {image_path}")
        sys.exit(1)

    async def _analyze():
        analyzer = FoodAnalyzer()
        result = await analyzer.analyze_async(str(path))

        if not result["ingredients"]:
            print("⚠️ No meal recognized in image.")
            return

        print_analysis_table(result)

    asyncio.run(_analyze())


def list_command(limit: int = 10):
    """List last N analyses."""

    async def _list():
        await Database.get_connection()
        results = await Database.get_last_10()
        await Database.close()
        if results:
            print(f"Last {len(results)} analyses:")
            for r in results:
                print(
                    f"#{r['id']}: {r['image_path']} - {r['total_kcal']} kcal ({r['created_at']})"
                )
        else:
            print("No analyses found in database")

    asyncio.run(_list())


def get_command(analysis_id: int):
    """Retrieve analysis by ID."""

    async def _get():
        await Database.get_connection()
        result = await Database.get_by_id(analysis_id)
        await Database.close()
        if result:
            print(f"Analysis #{result['id']}")
            print(f"Image: {result['image_path']}")
            print(f"Date: {result['created_at']}")
            print(
                f"Totals: {result['total_kcal']} kcal, {result['total_protein_g']}g protein, {result['total_carbs_g']}g carbs, {result['total_fat_g']}g fat"
            )
        else:
            print(f"Analysis #{analysis_id} not found")

    asyncio.run(_get())


def main():
    setup_logging()
    parser = argparse.ArgumentParser(
        description="AI Food Analyzer - Analyze meal photos for nutrition information"
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Commands")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a meal photo")
    analyze_parser.add_argument("image_path", help="Path to the meal image file")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get analysis by ID")
    get_parser.add_argument("id", type=int, help="Analysis ID")

    # List command
    _list_parser = subparsers.add_parser("list", help="List last 10 analyses")

    args = parser.parse_args()

    if args.command == "analyze":
        analyze_command(args.image_path)
    elif args.command == "get":
        get_command(args.id)
    elif args.command == "list":
        list_command()


if __name__ == "__main__":
    main()

"""CLI command for cost reporting."""

from datetime import timedelta
from typing import Optional

from loguru import logger

from src.telemetry import get_cost_meter


def cost_report_command(since: str = "24h", provider: Optional[str] = None, top: int = 10) -> None:
    """Display cost report."""

    # Parse time range
    since_delta = None
    if since:
        value = int(since[:-1])
        unit = since[-1].lower()
        if unit == "h":
            since_delta = timedelta(hours=value)
        elif unit == "d":
            since_delta = timedelta(days=value)
        elif unit == "w":
            since_delta = timedelta(weeks=value)
        elif unit == "m":
            since_delta = timedelta(days=value * 30)
        else:
            logger.error(f"Unknown time unit: {unit}. Use h, d, w, m")
            return

    meter = get_cost_meter()
    report = meter.get_report(since=since_delta, provider=provider, limit=top)
    totals = report["totals"]

    print("\n" + "=" * 60)
    print("COST REPORT")
    if since_delta:
        print(f"Period: last {since}")
    else:
        print("Period: all time")
    print("=" * 60)

    # Totals
    print("\n📊 TOTAL:")
    print(f"   Cost:        ${totals['total_cost_usd']:.6f}")
    print(f"   API calls:   {totals['total_calls']}")
    print(f"   Prompt tokens:  {totals['total_prompt_tokens']:,}")
    print(f"   Completion tokens: {totals['total_completion_tokens']:,}")

    # By provider
    if report["by_provider"]:
        print("\n📊 BY PROVIDER:")
        for item in report["by_provider"]:
            cost = item.get("cost", 0)
            calls = item.get("calls", 0)
            percentage = (cost / totals["total_cost_usd"] * 100) if totals["total_cost_usd"] > 0 else 0
            print(f"   {item['provider']:12} ${cost:.6f}  ({calls} calls, {percentage:.1f}%)")

    # By model
    if report["by_model"]:
        print("\n📊 BY MODEL:")
        for item in report["by_model"]:
            cost = item.get("cost", 0)
            calls = item.get("calls", 0)
            percentage = (cost / totals["total_cost_usd"] * 100) if totals["total_cost_usd"] > 0 else 0
            print(f"   {item['model']:20} ${cost:.6f}  ({calls} calls, {percentage:.1f}%)")

    # Top prompts
    if report["top_prompts"]:
        print(f"\n💰 TOP {len(report['top_prompts'])} MOST EXPENSIVE CALLS:")
        for i, item in enumerate(report["top_prompts"], 1):
            preview = item.get("prompt_preview", "")[:60]
            print(f"   {i}. ${item['cost_usd']:.6f} | {item['provider']}/{item['model']}")
            print(f"      Tokens: {item['prompt_tokens']}+{item['completion_tokens']}")
            if preview:
                print(f"      Prompt: {preview}...")
            print()

    print("=" * 60 + "\n")


def add_cost_report_parser(subparsers) -> None:
    """Add cost-report subparser to main CLI."""
    parser = subparsers.add_parser(
        "cost-report",
        help="Show cost report for AI API calls"
    )
    parser.add_argument(
        "--since",
        default="24h",
        help="Time range: 24h, 7d, 1w, 1m (default: 24h)"
    )
    parser.add_argument(
        "--provider",
        help="Filter by provider (openai, gemini, anthropic)"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top prompts to show (default: 10)"
    )
    parser.set_defaults(func=cost_report_command)

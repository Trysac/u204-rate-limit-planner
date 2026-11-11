"""Command-line interface for rate_limit_planner."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from rate_limit_planner import Limits, PlannerError, Profile, explain, plan


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: List of command-line arguments; uses ``sys.argv[1:]`` if ``None``.

    Returns:
        Exit code: 0 on success, 1 on domain error, 2 on usage error.
    """
    parser = argparse.ArgumentParser(
        prog="rate-limit-planner",
        description="Compute a safe request plan for an LLM provider.",
    )
    parser.add_argument("--rpm", type=int, required=True, help="Requests per minute limit")
    parser.add_argument("--tpm", type=int, required=True, help="Tokens per minute limit")
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=None,
        help="Optional hard cap on concurrent requests",
    )
    parser.add_argument("--input", type=int, required=True, help="Average input tokens per request")
    parser.add_argument(
        "--output", type=int, required=True, help="Average output tokens per request"
    )
    parser.add_argument("--latency", type=float, required=True, help="Average latency in seconds")
    parser.add_argument("--safety", type=float, default=0.9, help="Safety factor (0,1]")
    parser.add_argument(
        "--explain", action="store_true", help="Print human-readable explanation instead of JSON"
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    limits = Limits(rpm=args.rpm, tpm=args.tpm, max_concurrency=args.max_concurrency)
    profile = Profile(
        input_tokens=args.input,
        output_tokens=args.output,
        latency_s=args.latency,
    )

    try:
        result = plan(limits, profile, safety=args.safety)
    except PlannerError as exc:
        print(exc.code, file=sys.stderr)
        return 1

    if args.explain:
        print(explain(result))
    else:
        print(json.dumps(asdict(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

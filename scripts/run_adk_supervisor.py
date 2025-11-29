"""Run the IT observability supervisor with the ADK InMemoryRunner.

This helper spins up the production agent tree and sends a prompt via the
ADK runner so you can exercise planning, delegation, and tool calls end to end.
It is ideal for verifying API credentials before moving to Try ADK web or a UI.

Usage (from repository root):

    PYTHONPATH=src python scripts/run_adk_supervisor.py \
        "Summarize the overnight reliability posture for prod-app-01."

Set the environment variable `GOOGLE_API_KEY` (or configure your ADK
credentials file) so Gemini requests succeed. Use `--verbose` to print tool
call details, and `--quiet` to capture the returned events without console
logging.
"""
from __future__ import annotations

import argparse
import asyncio
from typing import Sequence

from google.adk.runners import InMemoryRunner

from it_ops_observability import AgentSettings
from it_ops_observability import create_supervisor_agent


async def _run_with_runner(
    prompts: Sequence[str], *, verbose: bool, quiet: bool
) -> None:
    agent = create_supervisor_agent(AgentSettings())
    runner = InMemoryRunner(agent=agent)
    try:
        events = await runner.run_debug(prompts, verbose=verbose, quiet=quiet)
        if quiet:
            print(f"Captured {len(events)} events from the runner.")
    finally:
        await runner.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "prompts",
        nargs="*",
        default=[
            "Give me an ops briefing: what happened overnight, what are the top risks, and what should leadership do next?",
        ],
        help="One or more user prompts routed through the supervisor agent.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print tool call details and intermediate responses.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console transcripts and only report event counts.",
    )
    args = parser.parse_args()

    asyncio.run(_run_with_runner(args.prompts, verbose=args.verbose, quiet=args.quiet))


if __name__ == "__main__":
    main()

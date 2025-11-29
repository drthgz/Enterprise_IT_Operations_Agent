"""Quick smoke demo for the IT observability supervisor agent.

This script instantiates the production supervisor agent, inspects its
sub-agent tree, and exercises the data tools directly so we can verify
everything is wired up before making live API calls.

Run from the project root:

    PYTHONPATH=src python scripts/quick_supervisor_demo.py

The script prints a concise summary of the agent hierarchy along with trimmed
samples from each tool invocation. This is intentionally top-line so we can
slot the transcript into evaluation docs or share it in the README.
"""
from __future__ import annotations

import argparse
from textwrap import shorten

from it_ops_observability import AgentSettings
from it_ops_observability import create_supervisor_agent
from it_ops_observability import fetch_incident_digest
from it_ops_observability import fetch_server_logs
from it_ops_observability import summarize_utilization


def _print_agent_tree(agent, indent: int = 0) -> None:
    prefix = "  " * indent
    tool_names = [tool.name for tool in getattr(agent, "tools", [])]
    print(f"{prefix}- {agent.name} [{agent.__class__.__name__}]")
    if tool_names:
        print(f"{prefix}  tools: {', '.join(tool_names)}")
    for sub_agent in getattr(agent, "sub_agents", []):
        _print_agent_tree(sub_agent, indent + 1)


def run_demo(server_id: str, hours: int) -> None:
    settings = AgentSettings()
    supervisor = create_supervisor_agent(settings)

    print("Agent hierarchy:\n")
    _print_agent_tree(supervisor)
    print("\nTool samples:\n")

    logs = fetch_server_logs(server_id=server_id, window_minutes=60)
    metrics = summarize_utilization(hours=hours, include_recent=3)
    ticket = fetch_incident_digest()

    print("fetch_server_logs →")
    print(shorten(logs.replace("\n", " | "), width=160, placeholder="…"))
    print("\nsummarize_utilization →")
    print(metrics)
    print("\nfetch_incident_digest →")
    print(ticket)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server-id", default="prod-app-01", help="Server identifier to pull logs for.")
    parser.add_argument("--hours", type=int, default=12, help="Lookback window (hours) for utilization summary.")
    args = parser.parse_args()
    run_demo(server_id=args.server_id, hours=args.hours)


if __name__ == "__main__":
    main()

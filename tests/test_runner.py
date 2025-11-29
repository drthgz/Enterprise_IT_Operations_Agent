"""End-to-end smoke test for the ADK supervisor runner."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Iterator

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _inject_src_path() -> Iterator[None]:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    try:
        yield
    finally:
        sys.path = [p for p in sys.path if p != str(PROJECT_ROOT / "src")]


@pytest.mark.skipif(
    "GOOGLE_API_KEY" not in os.environ,
    reason="GOOGLE_API_KEY is required to run the ADK supervisor runner.",
)
def test_supervisor_runner_outputs_summary(monkeypatch) -> None:
    """Ensure the supervisor produces a leadership summary with key sections."""
    from it_ops_observability import AgentSettings, create_supervisor_agent
    from google.adk.runners import InMemoryRunner
    from google.adk.models.google_llm import _ResourceExhaustedError

    # Seed determinism for synthetic fallbacks so the assertion is stable.
    monkeypatch.setenv("PYTHONHASHSEED", "0")

    agent = create_supervisor_agent(AgentSettings())
    runner = InMemoryRunner(agent=agent)

    prompts = [
        "Give me an ops briefing: what happened overnight, what are the top risks, and what should leadership do next?",
        "Investigate prod-app-01 with the default window and summarize key log anomalies.",
        "Provide the utilization stats and risks.",
        "Draft the leadership summary and actions.",
    ]

    loop = asyncio.new_event_loop()
    try:
        events = loop.run_until_complete(runner.run_debug(prompts, quiet=True))
    except _ResourceExhaustedError as exc:
        pytest.skip(f"Gemini quota exhausted: {exc}")
    finally:
        loop.run_until_complete(runner.close())
        loop.close()

    assert events, "Runner returned no events"
    text_parts: list[str] = []
    for event in events:
        content = getattr(event, "content", None)
        if not content:
            continue
        parts = getattr(content, "parts", None)
        if not parts:
            continue
        for part in parts:
            text = getattr(part, "text", None)
            if text:
                text_parts.append(text)

    combined = "\n".join(text_parts)

    normalized = combined.lower()
    assert len(normalized) > 300, "Narrative is unexpectedly short"
    for keyword in ("prod-app-01", "disk", "database", "risk", "leadership"):
        assert keyword in normalized, f"Missing keyword '{keyword}' in narrative"

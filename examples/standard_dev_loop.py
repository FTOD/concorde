#!/usr/bin/env python3
"""Run Concorde's standard LangGraph loop with a deterministic recording executor."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from concorde.workflows import StageExecution, build_standard_dev_loop  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", help="Development request carried through the four workflow stages.")
    arguments = parser.parse_args()
    visits: list[dict[str, object]] = []

    def record(invocation: StageExecution) -> str:
        visits.append(
            {
                "stage": invocation.stage.name,
                "prompts": [prompt.command_id for prompt in invocation.stage.prompts],
                "prior_stages": [result.stage for result in invocation.prior_results],
            }
        )
        return f"prepared:{invocation.stage.name}"

    graph = build_standard_dev_loop(REPOSITORY_ROOT, record, framework_prefix="")
    result = graph.invoke({"request": arguments.request, "stage_results": []})
    print(
        json.dumps(
            {
                "request": arguments.request,
                "stages": visits,
                "results": [asdict(item) for item in result["stage_results"]],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

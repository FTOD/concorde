#!/usr/bin/env python3
"""Reflection investigation, routing, implementation, and validation Operation."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


OPERATION_NAME = "concorde-reflections-triage"
OPERATION_SKILLS = (
    "concorde-analyze",
    "concorde-fast-loop",
    "concorde-plan",
    "concorde-tasks",
    "concorde-implement",
    "concorde-validate",
)
OPERATION_STAGES = (
    ("investigate", ("concorde-analyze",)),
    ("route", ("concorde-fast-loop", "concorde-plan")),
    ("implement", ("concorde-tasks", "concorde-implement")),
    ("validate", ("concorde-validate",)),
)


def package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _runtime():
    root = package_root()
    source = str(root / "src")
    if source not in sys.path:
        sys.path.insert(0, source)
    from concorde.operation_runtime import OperationExecution, build_operation

    return OperationExecution, build_operation


def build_reflections_triage(executor, *, framework_prefix: str = "") -> Any:
    """Compile the reflection-triage Operation for an injected executor."""

    _, build_operation = _runtime()
    return build_operation(
        package_root(),
        OPERATION_STAGES,
        executor,
        framework_prefix=framework_prefix,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", nargs="?", default="status")
    parser.add_argument("--framework-prefix", default="")
    arguments = parser.parse_args()
    visits: list[dict[str, object]] = []
    OperationExecution, _ = _runtime()

    def record(invocation: OperationExecution) -> str:
        visits.append(
            {
                "stage": invocation.stage.name,
                "skills": [skill.name for skill in invocation.stage.skills],
                "prior_stages": [result.stage for result in invocation.prior_results],
            }
        )
        return f"prepared:{invocation.stage.name}"

    graph = build_reflections_triage(record, framework_prefix=arguments.framework_prefix)
    result = graph.invoke({"request": arguments.request, "stage_results": []})
    print(
        json.dumps(
            {
                "operation": OPERATION_NAME,
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

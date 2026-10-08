"""A stand-in ``claude`` for project review tests that picks one plan per worker.

The environment variable ``FAKE_REVIEW_PLANS`` holds an object whose keys are
``"<role> <module> <n>"`` and whose values are plans in the form of the worker tests' fake
``claude``. The role is read from the brief's ``Your role: <role>.``, ``code`` for the code
reviewer, whose brief names none; the Module from ``Reviewed Module: `<id>```, ``project`` for the
architecture review; ``n`` is a panel worker's seat or the chair's attempt, ``1`` for the code
reviewer. A worker without a plan returns no finding.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

FAKE = Path(__file__).resolve().parents[1] / "harness/workers/fake_claude.py"


def main() -> int:
    prompt = sys.stdin.read()
    plans = json.loads(os.environ.get("FAKE_REVIEW_PLANS", "{}"))
    role = re.search(r"Your role: (\w+)\.", prompt)
    module = re.search(r"Reviewed Modules?: `([^`]+)`", prompt)
    number = re.search(r"(?:Panel seat|Chair attempt): (\d+)", prompt)
    key = " ".join(
        [
            role.group(1) if role else "code",
            module.group(1) if module else "?",
            number.group(1) if number else "1",
        ]
    )
    default = {"findings": []}
    if role and role.group(1) == "chair":
        default["rejected"] = []
    plan = json.dumps(plans.get(key, [{"result": {"output": default}}]))
    return subprocess.run(
        [sys.executable, str(FAKE), *sys.argv[1:]],
        input=f"FAKE-PLAN: {plan}\n{prompt}",
        text=True,
        check=False,
    ).returncode


if __name__ == "__main__":
    sys.exit(main())

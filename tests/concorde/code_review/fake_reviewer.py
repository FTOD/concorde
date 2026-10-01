"""A stand-in ``claude`` for code review tests that picks one plan per reviewed Module.

The brief carries ``FAKE-PLANS: <json>`` (in the focus), an object whose keys are Module
identities and whose values are plans in the form of the worker tests' fake ``claude``. The Module
is read from the brief's ``Reviewed Module: `<id>``` line; the chosen plan is handed to that fake as
``FAKE-PLAN``.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

FAKE = Path(__file__).resolve().parents[1] / "harness/workers/fake_claude.py"


def main() -> int:
    prompt = sys.stdin.read()
    match = re.search(r"FAKE-PLANS: (.*)", prompt)
    plans = json.loads(match.group(1)) if match else {}
    module = re.search(r"Reviewed Modules?: `([^`]+)`", prompt)
    plan = json.dumps(plans.get(module.group(1) if module else "?", [{}]))
    return subprocess.run(
        [sys.executable, str(FAKE), *sys.argv[1:]],
        input=f"FAKE-PLAN: {plan}\n{prompt}",
        text=True,
        check=False,
    ).returncode


if __name__ == "__main__":
    sys.exit(main())

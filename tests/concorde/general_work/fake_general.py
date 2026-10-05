"""A stand-in ``claude`` for the ``general`` tests that picks one plan per worker.

The file the environment variable ``FAKE_GENERAL_PLANS`` names holds an object whose keys are
``worker`` and ``reviewer`` and whose values are plans in the form of the worker tests' fake
``claude``. The reviewer is told apart by its brief's ``## This review`` section; the chosen plan
is handed to that fake as ``FAKE-PLAN``.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

FAKE = Path(__file__).resolve().parents[1] / "harness/workers/fake_claude.py"


def main() -> int:
    prompt = sys.stdin.read()
    plans = json.loads(Path(os.environ["FAKE_GENERAL_PLANS"]).read_text())
    role = "reviewer" if "## This review" in prompt else "worker"
    plan = json.dumps(plans.get(role, [{}]))
    return subprocess.run(
        [sys.executable, str(FAKE), *sys.argv[1:]],
        input=f"FAKE-PLAN: {plan}\n{prompt}",
        text=True,
        check=False,
    ).returncode


if __name__ == "__main__":
    sys.exit(main())

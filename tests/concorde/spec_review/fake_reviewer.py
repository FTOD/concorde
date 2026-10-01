"""A stand-in ``claude`` for Spec review tests that picks one plan per reviewer and checker.

The task goal carries ``FAKE-PLANS: <json>``, or, for an unbound run without a goal, the
environment variable ``FAKE_REVIEW_PLANS`` does, an object whose keys are ``"<role> <module>"``, for
example ``"reviewer module.a"`` or ``"checker module.a"``, and whose values are plans in the form of
the worker tests' fake ``claude``. The role and Module are read from the Spec review brief; the
chosen plan is handed to that fake as ``FAKE-PLAN``, with every ``@WORKTREE@`` replaced by the
task worktree's absolute path taken from the brief.
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
    match = re.search(r"FAKE-PLANS: (.*)", prompt)
    if match:
        plans = json.loads(match.group(1))
    role = re.search(r"Your role: (\w+)\.", prompt)
    module = re.search(r"Reviewed Module: `([^`]+)`", prompt)
    key = f"{role.group(1) if role else '?'} {module.group(1) if module else '?'}"
    plan = json.dumps(plans.get(key, [{}]))
    worktree = re.search(r"The task worktree is (\S+?);", prompt)
    if worktree:
        plan = plan.replace("@WORKTREE@", worktree.group(1))
    return subprocess.run(
        [sys.executable, str(FAKE), *sys.argv[1:]],
        input=f"FAKE-PLAN: {plan}\n{prompt}",
        text=True,
        check=False,
    ).returncode


if __name__ == "__main__":
    sys.exit(main())

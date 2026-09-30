"""A stand-in ``claude`` for Spec panel tests that picks one plan per reviewer seat and chair attempt.

The task goal carries ``FAKE-PLANS: <json>``, or, for an unbound run without a goal, the
environment variable ``FAKE_REVIEW_PLANS`` does, an object whose keys are ``"<role> <module> <n>"``,
where ``n`` is the reviewer's seat or the chair's attempt, for example ``"reviewer module.a 2"`` or
``"chair module.a 1"``, and whose values are plans in the form of the worker tests' fake
``claude``. The role, Module and number are read from the Spec panel brief; the chosen plan is
handed to that fake as ``FAKE-PLAN``, with every ``@WORKTREE@`` replaced by the task worktree's
absolute path taken from the brief.
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
    number = re.search(r"(?:Panel seat|Chair attempt): (\d+)", prompt)
    key = " ".join(found.group(1) if found else "?" for found in (role, module, number))
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

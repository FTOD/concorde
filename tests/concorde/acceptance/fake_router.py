"""A stand-in ``claude`` that picks a fake worker's plan from what the brief asks.

``FAKE_ROUTES`` names a JSON file holding a list of ``[pattern, plan]`` pairs; the first pattern
that occurs in the brief chooses the plan, in the form of the worker tests' fake ``claude``,
with every ``@WORKTREE@`` replaced by the task worktree named in the brief. A brief no pattern
matches gets an empty plan. It lets a whole workflow run with fake workers, since no Operation of
a workflow carries a plan in its arguments.
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
    routes = json.loads(Path(os.environ["FAKE_ROUTES"]).read_text())
    plan = next((plan for pattern, plan in routes if pattern in prompt), [{}])
    text = json.dumps(plan)
    worktree = re.search(r"The task worktree is (\S+?);", prompt)
    if worktree:
        text = text.replace("@WORKTREE@", worktree.group(1))
    return subprocess.run(
        [sys.executable, str(FAKE), *sys.argv[1:]],
        input=f"FAKE-PLAN: {text}\n{prompt}",
        text=True,
        check=False,
    ).returncode


if __name__ == "__main__":
    sys.exit(main())

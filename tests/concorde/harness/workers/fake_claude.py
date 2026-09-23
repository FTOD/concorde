"""A deterministic stand-in for ``claude -p`` used by the worker tests.

The test puts a plan in the worker instructions as ``FAKE-PLAN: <json>``: a list of rounds, each
with ``writes`` (absolute path to content), ``result`` (the structured output, merged over a valid
``ok`` result), and optional ``sleep``, ``spawn`` (start a detached sleeper that records its PID),
``raw`` (print this instead of an envelope) or ``no_structured`` (omit the structured output).
The fake records its argument list, environment and prompt per round in its working directory. It
does not enforce anything: enforcement is Claude Code's and is covered by the live test.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = {
    "status": "ok",
    "summary": "done",
    "problem": "",
    "attempts": [],
    "evidence": [],
    "options": [],
    "recommendation": "",
    "blocking": False,
    "impact": "",
    "proposed_deletions": [],
    "output": {},
}


def main() -> int:
    prompt = sys.stdin.read()
    state_file = Path("fake-state.json")
    state = json.loads(state_file.read_text()) if state_file.exists() else {"round": 0}
    if state["round"] == 0:
        match = re.search(r"FAKE-PLAN: (.*)", prompt)
        state["plan"] = json.loads(match.group(1)) if match else [{}]
    state["round"] += 1
    number = state["round"]
    state_file.write_text(json.dumps(state))
    Path(f"fake-round-{number}.json").write_text(
        json.dumps({"argv": sys.argv[1:], "env": dict(os.environ), "prompt": prompt})
    )
    step = state["plan"][min(number, len(state["plan"])) - 1]
    for path, content in step.get("writes", {}).items():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content)
    if step.get("spawn"):
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(120)"],
        )
        Path(step["spawn"]).write_text(str(child.pid))
    if step.get("sleep"):
        time.sleep(step["sleep"])
    if "raw" in step:
        print(step["raw"])
        return 0
    envelope = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "session_id": f"fake-session-{number}",
        "result": "",
    }
    if not step.get("no_structured"):
        envelope["structured_output"] = {**BASE, **step.get("result", {})}
    print(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    sys.exit(main())

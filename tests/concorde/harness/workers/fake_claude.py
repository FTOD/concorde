"""A deterministic stand-in for ``claude -p`` used by the worker tests.

The test puts a plan in the worker instructions as ``FAKE-PLAN: <json>``: a list of rounds, each
with ``writes`` (absolute path to content), ``result`` (the structured output, merged over a valid
``ok`` result), and optional ``sleep``, ``spawn`` (start a detached sleeper that records its PID),
``raw`` (print this instead of an envelope), ``envelope`` (fields merged over the result envelope,
such as an error subtype), ``no_structured`` (omit the structured output) or ``actions``
(``[tool, input]`` pairs printed first as ``stream-json`` assistant tool uses).
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
    "error": None,
    "proposed_deletions": [],
    "output": {},
}

# A worker error for plans that end blocked or failed without spelling one out.
ERROR = {
    "code": "spec_gap",
    "detail": "the rounding rule is not specified",
    "evidence": [{"kind": "spec", "ref": "specs/a/module.md", "detail": "no rule"}],
    "attempts": ["read specs/a/module.md"],
    "unhandled": {
        "reason": "decision",
        "explanation": "what the Spec promises is decided above the worker",
    },
    "options": ["specify the rounding rule"],
    "recommendation": "specify the rounding rule",
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
    for tool, arguments in step.get("actions", []):
        print(
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {"type": "tool_use", "name": tool, "input": arguments}
                        ]
                    },
                }
            ),
            flush=True,
        )
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
    envelope.update(step.get("envelope", {}))
    if not step.get("no_structured"):
        result = {**BASE, **step.get("result", {})}
        if result["status"] in ("blocked", "failed") and "error" not in step.get(
            "result", {}
        ):
            result["error"] = ERROR
        envelope["structured_output"] = result
    print(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    sys.exit(main())

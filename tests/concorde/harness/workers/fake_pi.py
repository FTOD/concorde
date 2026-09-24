"""A deterministic stand-in for ``pi -p --mode json`` used by the pi worker tests.

The test puts a plan in the worker instructions as ``FAKE-PLAN: <json>``: a list of rounds, each
with ``writes`` (absolute path to content), ``actions`` (``[tool, arguments]`` pairs reported as
tool executions), ``result`` (merged over a valid ``ok`` result and reported as the
``concorde_result`` tool), ``no_result`` (end without calling it), ``error`` (end with an
assistant error message), ``limit`` (append a ``concorde-limit`` entry) and ``exit`` (the exit
code). The fake records its argument list, environment and prompt per round in its working
directory and writes a session file where pi would. It enforces nothing: enforcement is the
permission extension's and is covered by the live test.
"""

import json
import os
import re
import sys
from pathlib import Path

BASE = {
    "status": "ok",
    "summary": "done",
    "error": None,
    "proposed_deletions": [],
    "output": {},
}


def option(name: str) -> str | None:
    arguments = sys.argv[1:]
    return arguments[arguments.index(name) + 1] if name in arguments else None


def emit(record: dict) -> None:
    print(json.dumps(record), flush=True)


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
    session = option("--session-id") or "fake-session"
    directory = Path(option("--session-dir") or ".")
    directory.mkdir(parents=True, exist_ok=True)
    transcript = directory / f"2026-01-01T00-00-00-000Z_{session}.jsonl"
    with transcript.open("a") as handle:
        handle.write(json.dumps({"type": "session", "id": session}) + "\n")
    emit({"type": "session", "version": 3, "id": session, "cwd": os.getcwd()})
    emit({"type": "agent_start"})
    for path, content in step.get("writes", {}).items():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content)
    for index, (tool, arguments) in enumerate(step.get("actions", [])):
        emit(
            {
                "type": "tool_execution_start",
                "toolCallId": f"call-{index}",
                "toolName": tool,
                "args": arguments,
            }
        )
        emit({"type": "turn_end", "message": {}, "toolResults": []})
    if step.get("limit"):
        emit(
            {
                "type": "entry_appended",
                "entry": {
                    "type": "custom",
                    "customType": "concorde-limit",
                    "data": step["limit"],
                },
            }
        )
    if step.get("error"):
        emit(
            {
                "type": "message_end",
                "message": {
                    "role": "assistant",
                    "content": [],
                    "stopReason": "error",
                    "errorMessage": step["error"],
                    "usage": {"cost": {"total": 0.01}},
                },
            }
        )
    elif not step.get("no_result") and not step.get("limit"):
        result = {**BASE, **step.get("result", {})}
        emit(
            {
                "type": "tool_execution_start",
                "toolCallId": "call-result",
                "toolName": "concorde_result",
                "args": result,
            }
        )
        emit(
            {
                "type": "tool_execution_end",
                "toolCallId": "call-result",
                "toolName": "concorde_result",
                "result": {
                    "content": [{"type": "text", "text": "Result recorded."}],
                    "details": result,
                },
                "isError": False,
            }
        )
    else:
        emit(
            {
                "type": "message_end",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": step.get("text", "I am done.")}
                    ],
                    "stopReason": "stop",
                },
            }
        )
    emit({"type": "turn_end", "message": {}, "toolResults": []})
    emit({"type": "agent_end", "messages": [], "willRetry": False})
    return int(step.get("exit", 0))


if __name__ == "__main__":
    sys.exit(main())

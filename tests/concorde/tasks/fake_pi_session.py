"""A deterministic stand-in for ``pi -p --mode json`` running one round of a pi task session.

The test puts a plan in the prompt as ``FAKE-PLAN: <json>``: an object with ``actions``
(``[tool, arguments]`` pairs reported as tool executions), ``sleep`` (seconds to wait after them),
``report`` (the ``concorde_report`` arguments to end with), ``error`` (end with an assistant error
message instead), ``stderr`` (text written to standard error) and ``exit`` (the exit code). The
fake appends its argument list, environment, working directory and prompt to the file
``FAKE_PI_LOG`` names, one JSON line per round. It enforces nothing: the boundary is exercised live.
"""

import json
import os
import re
import sys
import time


def emit(record: dict) -> None:
    print(json.dumps(record), flush=True)


def main() -> int:
    prompt = sys.stdin.read()
    match = re.search(r"FAKE-PLAN: (.*)", prompt)
    plan = json.loads(match.group(1)) if match else {}
    with open(os.environ["FAKE_PI_LOG"], "a", encoding="utf-8") as log:
        log.write(
            json.dumps(
                {
                    "argv": sys.argv[1:],
                    "env": dict(os.environ),
                    "cwd": os.getcwd(),
                    "prompt": prompt,
                }
            )
            + "\n"
        )
    session = sys.argv[sys.argv.index("--session-id") + 1]
    emit({"type": "session", "version": 3, "id": session, "cwd": os.getcwd()})
    emit({"type": "agent_start"})
    for index, (tool, arguments) in enumerate(plan.get("actions", [])):
        emit(
            {
                "type": "tool_execution_start",
                "toolCallId": f"call-{index}",
                "toolName": tool,
                "args": arguments,
            }
        )
        emit({"type": "turn_end", "message": {}, "toolResults": []})
    time.sleep(float(plan.get("sleep", 0)))
    if plan.get("stderr"):
        sys.stderr.write(plan["stderr"])
        sys.stderr.flush()
    if "report" in plan:
        emit(
            {
                "type": "tool_execution_start",
                "toolCallId": "call-report",
                "toolName": "concorde_report",
                "args": plan["report"],
            }
        )
        emit(
            {
                "type": "tool_execution_end",
                "toolCallId": "call-report",
                "toolName": "concorde_report",
                "result": {
                    "content": [{"type": "text", "text": "Report recorded."}],
                    "details": plan["report"],
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
                    "content": [{"type": "text", "text": "I stop here."}],
                    "stopReason": "error" if plan.get("error") else "stop",
                    **({"errorMessage": plan["error"]} if plan.get("error") else {}),
                },
            }
        )
    emit({"type": "turn_end", "message": {}, "toolResults": []})
    emit({"type": "agent_end", "messages": [], "willRetry": False})
    return int(plan.get("exit", 0))


if __name__ == "__main__":
    sys.exit(main())

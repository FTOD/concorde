"""A stand-in for `pi --mode rpc` that exercises the RPC client's framing and lifecycle handling.

The scenario is chosen by the FAKE_PI_SCENARIO environment variable:
- ``settle``: answer the prompt, ask one dialog, emit a tool result whose text contains U+2028 and
  U+2029, settle, then answer the statistics request;
- ``eof``: answer the prompt and exit before the run settles;
- ``hang``: answer the prompt and never settle.
"""
import json
import os
import sys
import time


def emit(record):
    sys.stdout.buffer.write(json.dumps(record, ensure_ascii=False).encode("utf-8") + b"\n")
    sys.stdout.buffer.flush()


def main():
    scenario = os.environ.get("FAKE_PI_SCENARIO", "settle")
    command = json.loads(sys.stdin.buffer.readline())
    emit({"type": "response", "id": command.get("id"), "command": "prompt", "success": True})
    if scenario == "eof":
        return
    if scenario == "hang":
        time.sleep(60)
        return
    emit({"type": "extension_ui_request", "id": "dialog-1", "method": "confirm", "title": "Allow?"})
    answer = json.loads(sys.stdin.buffer.readline())
    emit({"type": "tool_execution_end", "toolCallId": "call_1", "toolName": "submit_result",
          "result": {"details": {"text": "line separator paragraph", "dialog": answer}}, "isError": False})
    sys.stdout.buffer.write(b'{"type":"agent_settled"}\r\n')
    sys.stdout.buffer.flush()
    stats = json.loads(sys.stdin.buffer.readline())
    emit({"type": "response", "id": stats.get("id"), "command": "get_session_stats", "success": True,
          "data": {"tokens": {"input": 7, "output": 3, "cacheRead": 1, "total": 10}, "cost": 0.5,
                   "assistantMessages": 2}})
    sys.stdin.buffer.read()


if __name__ == "__main__":
    main()

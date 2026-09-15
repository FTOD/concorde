"""A strict JSONL client for one Pi process in RPC mode.

Pi's RPC mode reads commands from stdin and writes responses and events to stdout, one JSON object
per LF-terminated record. Records are split on ``\\n`` only (never on other Unicode line
separators, which may occur inside JSON strings) and an optional trailing ``\\r`` is dropped.

``run_prompt`` sends one ``prompt`` command, collects every event until ``agent_settled``, reads
the session statistics and ends the process. It knows nothing about Concorde contracts: the caller
interprets the collected tool results.
"""
from __future__ import annotations

import json
import queue
import subprocess
import threading
from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Mapping, Sequence


class PiRpcError(RuntimeError):
    """The Pi process failed, broke the protocol or exited before the run settled."""


class PiRpcTimeout(PiRpcError):
    """The run did not settle before its deadline; the process has been killed."""


class PiRpcCancelled(PiRpcError):
    """The host interrupted the run; the process has been killed."""


@dataclass
class PiRun:
    events: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, Any] | None = None
    stderr: str = ""
    exit_code: int | None = None
    wall_seconds: float = 0.0

    def results_of(self, tool_name: str) -> list[dict[str, Any]]:
        return [item for item in self.tool_results if item.get("toolName") == tool_name]


_DIALOG_METHODS = frozenset({"select", "confirm", "input", "editor"})


def _records(stream, sink: queue.Queue) -> None:
    buffer = b""
    try:
        while True:
            chunk = stream.read1(65536) if hasattr(stream, "read1") else stream.read(65536)
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                sink.put(("line", line[:-1] if line.endswith(b"\r") else line))
        if buffer.strip():
            sink.put(("line", buffer))
    finally:
        sink.put(("eof", None))


def run_prompt(argv: Sequence[str], *, cwd: str, env: Mapping[str, str], message: str,
               timeout: float, popen=subprocess.Popen) -> PiRun:
    """Run one prompt to settlement and return everything the process reported."""
    started = monotonic()
    deadline = started + timeout
    process = popen(list(argv), cwd=cwd, env=dict(env), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, bufsize=0)
    records: queue.Queue = queue.Queue()
    stderr_chunks: list[bytes] = []
    threading.Thread(target=_records, args=(process.stdout, records), daemon=True).start()
    stderr_reader = threading.Thread(target=lambda: stderr_chunks.append(process.stderr.read()), daemon=True)
    stderr_reader.start()
    run = PiRun()

    def send(command: dict[str, Any]) -> None:
        process.stdin.write((json.dumps(command, separators=(",", ":")) + "\n").encode("utf-8"))
        process.stdin.flush()

    def stop() -> None:
        if process.poll() is None:
            process.kill()
        process.wait()

    def finish() -> PiRun:
        stderr_reader.join(timeout=5)
        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                stream.close()
            except OSError:
                pass
        run.stderr = b"".join(stderr_chunks).decode("utf-8", "replace")
        run.exit_code = process.returncode
        run.wall_seconds = monotonic() - started
        return run

    def next_record() -> dict[str, Any]:
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise PiRpcTimeout(f"Pi run did not settle within {timeout}s")
        try:
            kind, line = records.get(timeout=remaining)
        except queue.Empty as error:
            raise PiRpcTimeout(f"Pi run did not settle within {timeout}s") from error
        if kind == "eof":
            raise PiRpcError("Pi process closed its output before the run settled")
        try:
            record = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise PiRpcError(f"Pi wrote a record that is not JSON: {error}") from error
        if not isinstance(record, dict):
            raise PiRpcError("Pi wrote a record that is not a JSON object")
        return record

    def await_response(request_id: str) -> dict[str, Any]:
        while True:
            record = next_record()
            if record.get("type") == "response" and record.get("id") == request_id:
                if record.get("success") is not True:
                    raise PiRpcError(f"Pi rejected {record.get('command')}: {record.get('error')}")
                return record
            observe(record)

    settled = False

    def observe(record: dict[str, Any]) -> None:
        nonlocal settled
        kind = record.get("type")
        if kind == "extension_ui_request" and record.get("method") in _DIALOG_METHODS:
            # A worker has no human at the other end: every dialog is answered as cancelled.
            send({"type": "extension_ui_response", "id": record.get("id"), "cancelled": True})
            return
        run.events.append(record)
        if kind == "tool_execution_end":
            run.tool_results.append(record)
        elif kind == "agent_settled":
            settled = True

    try:
        send({"id": "prompt", "type": "prompt", "message": message})
        await_response("prompt")
        while not settled:
            observe(next_record())
        send({"id": "stats", "type": "get_session_stats"})
        run.stats = await_response("stats").get("data")
        process.stdin.close()
        try:
            process.wait(timeout=max(0.1, min(10.0, deadline - monotonic())))
        except subprocess.TimeoutExpired:
            stop()
    except KeyboardInterrupt as error:
        stop()
        finish()
        raise PiRpcCancelled("Pi run cancelled by the host") from error
    except PiRpcError:
        stop()
        finish()
        raise
    except OSError as error:
        stop()
        finish()
        raise PiRpcError(f"Pi process I/O failed: {error}") from error
    return finish()

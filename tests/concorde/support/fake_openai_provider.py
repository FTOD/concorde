"""A scripted OpenAI-compatible Chat Completions server for exercising a real Pi process offline.

Each request pops the next scripted turn and streams it back as Server-Sent Events: a turn is either
a tool call (``{"tool": name, "arguments": {...}}``) or plain assistant text (``{"text": ...}``),
optionally delayed by ``"delay"`` seconds before the response starts.
Every request body is recorded so a test can inspect the system prompt and advertised tools Pi sent.
"""
from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class FakeOpenAIProvider:
    def __init__(self, turns: list[dict]):
        self.turns = list(turns)
        self.requests: list[dict] = []
        provider = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length) or b"{}")
                provider.requests.append(body)
                turn = provider.turns.pop(0) if provider.turns else {"text": "No scripted turn remains."}
                if turn.get("delay"):
                    time.sleep(turn["delay"])
                try:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()
                    for chunk in provider._chunks(body, turn, len(provider.requests)):
                        self.wfile.write(b"data: " + json.dumps(chunk).encode() + b"\n\n")
                        self.wfile.flush()
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    # The client abandoned the stream, as an aborted or timed-out run does.
                    pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}/v1"

    def __enter__(self) -> "FakeOpenAIProvider":
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._server.shutdown()
        self._server.server_close()

    @staticmethod
    def _chunks(body: dict, turn: dict, number: int) -> list[dict]:
        base = {"id": f"chatcmpl-{number}", "object": "chat.completion.chunk", "created": 0,
                "model": body.get("model", "fake")}
        if "tool" in turn:
            delta = {"role": "assistant", "tool_calls": [{
                "index": 0, "id": f"call_{number}", "type": "function",
                "function": {"name": turn["tool"], "arguments": json.dumps(turn.get("arguments", {}))}}]}
            finish = "tool_calls"
        else:
            delta = {"role": "assistant", "content": turn["text"]}
            finish = "stop"
        return [
            {**base, "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
            {**base, "choices": [{"index": 0, "delta": {}, "finish_reason": finish}]},
            {**base, "choices": [], "usage": {"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110}},
        ]

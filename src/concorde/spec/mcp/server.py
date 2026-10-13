"""The stdio MCP session: newline-delimited JSON-RPC 2.0 on standard input and output.

The server declares only the tools capability. It resolves its root once, after the client's
``initialized`` notification: ``CLAUDE_PROJECT_DIR`` when set, otherwise the single ``file://``
root the client reports through ``roots/list``. Every tool call is answered from that root; a
session without a root answers every call with ``no_root``. Nothing here writes a file or opens a
listener.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import IO
from urllib.parse import unquote, urlparse

from ..errors import SpecError, unexpected
from .tools import TOOLS, ToolError, call, canonical

SERVER_INFO = {"name": "concorde-spec", "version": "1"}
SUPPORTED_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")


class Session:
    def __init__(self, reader: IO[str], writer: IO[str], environment=None):
        self.reader = reader
        self.writer = writer
        self.environment = dict(os.environ if environment is None else environment)
        self.root: Path | None = None
        self.root_error: str | None = None
        self.resolved = False
        self.client_roots = False
        self.pending: list[dict] = []
        self.next_id = 0

    # --- transport --------------------------------------------------------------------------

    def send(self, message: dict) -> None:
        self.writer.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.writer.flush()

    def parsed(self, line: str) -> dict | None:
        """The JSON-RPC message of one input line, or ``None`` once a malformed line was
        answered: invalid JSON with a parse error, any other value than an object with an
        invalid-request error, both without an identity the server could not read."""
        try:
            message = json.loads(line)
        except ValueError:
            self.send(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "parse error"},
                }
            )
            return None
        if not isinstance(message, dict):
            self.send(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32600,
                        "message": "invalid request: a message is a JSON object, not a "
                        f"JSON {type(message).__name__}",
                    },
                }
            )
            return None
        return message

    def receive(self) -> dict | None:
        """The next message, or ``None`` only at the end of the input."""
        if self.pending:
            return self.pending.pop(0)
        while line := self.reader.readline():
            if line.strip() and (message := self.parsed(line)) is not None:
                return message
        return None

    def request_client(self, method: str, params: dict | None = None) -> dict | None:
        """Send a request to the client and wait for its response, queueing other messages."""
        self.next_id += 1
        identity = f"server-{self.next_id}"
        self.send(
            {"jsonrpc": "2.0", "id": identity, "method": method, "params": params or {}}
        )
        while line := self.reader.readline():
            if not line.strip() or (message := self.parsed(line)) is None:
                continue
            if message.get("id") == identity and "method" not in message:
                return message
            self.pending.append(message)
        return None

    # --- root -------------------------------------------------------------------------------

    def resolve_root(self) -> None:
        configured = self.environment.get("CLAUDE_PROJECT_DIR")
        if configured:
            self.set_root(Path(configured))
            return
        if not self.client_roots:
            self.root_error = (
                "no CLAUDE_PROJECT_DIR and the client declared no roots capability"
            )
            return
        response = self.request_client("roots/list")
        if response is None:
            self.root_error = "the input ended before the client answered roots/list"
            return
        if "error" in response:
            self.root_error = "the client refused roots/list with a JSON-RPC error"
            return
        result = response.get("result")
        roots = result.get("roots") if isinstance(result, dict) else None
        if not isinstance(roots, list):
            self.root_error = "the client's roots/list reply holds no roots list"
            return
        # Exactly one root, whatever its scheme: several roots never resolve to one of them.
        if len(roots) != 1:
            self.root_error = f"expected exactly one client root, got {len(roots)}"
            return
        uri = roots[0].get("uri") if isinstance(roots[0], dict) else None
        if not isinstance(uri, str) or not uri.startswith("file://"):
            self.root_error = f"the client's one root is not a file:// URI: {uri!r}"
            return
        self.set_root(Path(unquote(urlparse(uri).path)))

    def set_root(self, path: Path) -> None:
        resolved = Path(os.path.realpath(path))
        if not resolved.is_dir():
            self.root_error = f"root is not a directory: {path}"
            return
        self.root = resolved

    # --- dispatch ---------------------------------------------------------------------------

    def handle(self, message: dict) -> None:
        method = message.get("method")
        identity = message.get("id")
        if method is None:
            return  # a stray response
        if identity is None:
            if method == "notifications/initialized" and not self.resolved:
                self.resolved = True
                self.resolve_root()
            return
        if method == "initialize":
            params = message.get("params")
            params = params if isinstance(params, dict) else {}
            requested = params.get("protocolVersion")
            capabilities = params.get("capabilities")
            self.client_roots = (
                isinstance(capabilities, dict) and "roots" in capabilities
            )
            self.reply(
                identity,
                {
                    "protocolVersion": requested
                    if requested in SUPPORTED_VERSIONS
                    else SUPPORTED_VERSIONS[0],
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": SERVER_INFO,
                    "instructions": (
                        "Read-only answers about the Concorde Specs of one worktree: grants, "
                        "Modules, Spec context, impact and structural validation."
                    ),
                },
            )
        elif method == "ping":
            self.reply(identity, {})
        elif method == "tools/list":
            self.reply(
                identity,
                {
                    "tools": [
                        {"name": name, **definition}
                        for name, definition in TOOLS.items()
                    ]
                },
            )
        elif method == "tools/call":
            self.reply(identity, self.tool_result(message.get("params", {})))
        else:
            self.send(
                {
                    "jsonrpc": "2.0",
                    "id": identity,
                    "error": {"code": -32601, "message": f"method not found: {method}"},
                }
            )

    def tool_result(self, params) -> dict:
        """Answer one ``tools/call``; arguments default to ``{}`` only when they are absent."""
        try:
            if self.root is None:
                raise ToolError(
                    "no_root",
                    self.root_error
                    or "the session has no root yet: the client has not sent initialized",
                )
            if not isinstance(params, dict):
                raise ToolError(
                    "invalid_input",
                    "the params of tools/call must be an object, not a JSON "
                    f"{type(params).__name__}",
                    "params",
                )
            value = call(self.root, params.get("name"), params.get("arguments", {}))
            error = False
        except SpecError as failure:
            value, error = {"error": failure.record()}, True
        return {
            "content": [{"type": "text", "text": canonical(value)}],
            "isError": error,
        }

    def reply(self, identity, result: dict) -> None:
        self.send({"jsonrpc": "2.0", "id": identity, "result": result})

    def run(self) -> int:
        while (message := self.receive()) is not None:
            try:
                self.handle(message)
            except Exception as error:  # noqa: BLE001 -- one bad message never ends the session
                if message.get("method") is not None and message.get("id") is not None:
                    record = unexpected(error).record()
                    self.send(
                        {
                            "jsonrpc": "2.0",
                            "id": message["id"],
                            "error": {
                                "code": -32603,
                                "message": record["message"],
                                "data": {"error": record},
                            },
                        }
                    )
        return 0


def main() -> int:
    return Session(sys.stdin, sys.stdout).run()

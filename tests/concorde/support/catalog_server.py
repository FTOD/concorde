#!/usr/bin/env python3
"""Localhost-only static server for clean-project catalog acceptance."""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import threading
from pathlib import Path


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class CatalogServer(contextlib.AbstractContextManager["CatalogServer"]):
    def __init__(self, directory: Path, port: int = 0):
        self.directory = directory.resolve()
        handler = functools.partial(_QuietHandler, directory=str(self.directory))
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}"

    def __enter__(self) -> "CatalogServer":
        self.thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--port", type=int, default=8765)
    arguments = parser.parse_args()
    handler = functools.partial(_QuietHandler, directory=str(arguments.dist.resolve()))
    with http.server.ThreadingHTTPServer(("127.0.0.1", arguments.port), handler) as server:
        print(f"Serving {arguments.dist.resolve()} at http://127.0.0.1:{arguments.port}", flush=True)
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

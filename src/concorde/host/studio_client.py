"""Opt-in CLI transport to a local Studio server (standard library only)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import UUID

from .typed_data import decode
from ..specification.repository import SpecError


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def run_in_studio(url: str, invocation: dict, project_root: Path, package_root: Path) -> dict:
    parsed = urlsplit(url)
    if (parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in {"", "/"}):
        raise SpecError("CONCORDE_STUDIO_URL must be a local http://localhost:port URL", "invalid_input")
    base = url.rstrip("/")
    # Neither environment proxies nor HTTP redirects may forward invocation data.
    opener = build_opener(ProxyHandler({}), _NoRedirect())

    def request(path, payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        try:
            with opener.open(Request(base + path, data=body,
                             headers={"Content-Type": "application/json"}), timeout=30) as response:
                return decode(response.read().decode("utf-8"))
        except (HTTPError, URLError, OSError) as error:
            raise SpecError(f"Studio request {path} failed: {error}. No local fallback or retry; "
                            "inspect the Studio thread before submitting again (a run may still be active).",
                            "studio_transport_failed") from error
        except (ValueError, UnicodeError) as error:
            raise SpecError("Studio returned invalid JSON", "incompatible_handoff") from error

    # Never retry run creation or fall back: a mutation may already be executing.
    thread = str(UUID(request("/threads", {})["thread_id"]))
    print(f"Concorde Studio thread: {thread} ({base})", file=sys.stderr, flush=True)
    prefix = f"/threads/{thread}"
    run = request(prefix + "/runs", {
        "assistant_id": invocation["operation_id"],
        "input": {"invocation": invocation, "expected_workspace": {
            "project_root": str(project_root.resolve()), "package_root": str(package_root.resolve())}},
        "multitask_strategy": "reject",
    })
    run_id = str(UUID(run["run_id"]))
    run_path = prefix + "/runs/" + run_id
    print(f"Concorde Studio run: {run_id}", file=sys.stderr, flush=True)
    while run["status"] in {"pending", "running"}:
        time.sleep(0.5)
        run = request(run_path)
    if run["status"] != "success":
        raise SpecError(f"Studio run {run_id} ended with {run['status']}; inspect thread {thread}",
                        "studio_run_failed")
    state = request(prefix + "/state")["values"]
    result = state.get("result")
    if (not isinstance(result, dict) or result.get("type_id") != "concorde-operation-result"
            or type(result.get("schema_version")) is not int or result["schema_version"] != 2
            or result.get("operation_id") != invocation["operation_id"]
            or result.get("status") not in {"succeeded", "described", "blocked", "failed"}
            or not isinstance(result.get("errors"), list)
            or (result.get("mode") != invocation["mode"]
                and not (result.get("mode") is None and result["status"] == "blocked" and result["errors"]))):
        raise SpecError("Studio returned an incompatible capability result", "incompatible_handoff")
    return state

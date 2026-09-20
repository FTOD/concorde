"""The execution environment every Concorde worker shares.

A Harness is context, control flow, models and per-worker permissions and environment
(workflow/agents-and-harnesses.md). In Concorde the per-worker part is the worker profile each
WorkerProfile declares (``worker_profile.WorkerProfile``): its workspace kind, tools, timeout and contract
effects. What every worker shares is the host environment allowlist below, the Pi worker runtime
(``pi_worker``) and the LangGraph Graphs that orchestrate them.
"""

from __future__ import annotations

SAFE_ENVIRONMENT: tuple[str, ...] = tuple(
    sorted(
        {
            "COMSPEC",
            "HOME",
            "LANG",
            "LC_ALL",
            "LC_CTYPE",
            "LOGNAME",
            "PATH",
            "PATHEXT",
            "SYSTEMROOT",
            "TEMP",
            "TMP",
            "TMPDIR",
            "USER",
            "WINDIR",
        }
    )
)

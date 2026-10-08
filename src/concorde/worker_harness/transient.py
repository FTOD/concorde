"""Which errors an agent program reports are transient errors of the model service.

A transient model-service error ended the round for a reason outside the worker: the service
refused the call for now (a concurrency or rate limit, an overload, an explicit retry-later) or the
call was lost on its way (an upstream or stream failure, a reset connection, a timeout). The same
call can succeed later, so Workers retries such a round (launch.md#retries). An exhausted quota,
billing or usage limit is no transient error: waiting minutes does not lift it.
"""

from __future__ import annotations

import re

# Exhausted accounts: never transient, whatever else the message says.
_LASTING = re.compile(
    r"insufficient_quota|quota exceeded|out of budget|billing|usage limit reached"
    r"|available balance|UsageLimitError",
    re.IGNORECASE,
)
_TRANSIENT = re.compile(
    "|".join(
        (
            # The service refused the call for now.
            r"concurrency.?limit",
            r"rate.?limit",
            r"too many requests",
            r"overloaded",
            r"high demand",
            r"\b(?:429|500|502|503|504|529)\b",
            r"service.?unavailable",
            r"temporarily unavailable",
            r"internal.?server.?error",
            r"retry later",
            r"try again later",
            r"retry your request",
            r"try your request again",
            r"ResourceExhausted",
            # The call was lost on its way.
            r"upstream\b.{0,40}\b(?:fail|error|connect|reset)",
            r"stream (?:failed|error|ended|closed)",
            r"connection.?(?:reset|refused|error|lost|closed)",
            r"ECONNRESET",
            r"socket hang up",
            r"fetch failed",
            r"network.?error",
            r"timed? out",
        )
    ),
    re.IGNORECASE,
)


def transient(message: str | None) -> bool:
    """Whether an error message the agent program reported names a transient model-service
    error."""
    if not message:
        return False
    return not _LASTING.search(message) and bool(_TRANSIENT.search(message))


__all__ = ["transient"]

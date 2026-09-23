"""Bounded control documents of the native result gate.

A native child submits a proposal; its post-run gate prints one staging control document without
asserting execution success. These helpers bound and read those documents. The Host steps that
submit, stage and accept a proposal use them; neither a submission nor staging is completion.
"""

from __future__ import annotations

import re

from ..spec.repository import SpecError
from ..spec.typed_data import canonical, decode

MAX_PROPOSAL_BYTES = 1024 * 1024
MAX_CONTROL_BYTES = 8000


def control_value(value: dict) -> dict:
    """Never truncate a gate's typed control value into apparent successful JSON."""
    encoded = canonical(value).encode("utf-8")
    if len(encoded) > MAX_CONTROL_BYTES:
        raise SpecError(
            "native gate control value exceeds its bound", "invalid_completion"
        )
    return decode(encoded.decode("utf-8"))


def staging_control(
    text: str, *, ticket: str, invocation_id: str, proposal_digest: str
) -> dict:
    """One complete, bounded Host stdout document; never a model-text substring."""
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_CONTROL_BYTES:
        raise SpecError(
            "native staging control exceeds its bound", "invalid_completion"
        )
    try:
        value = decode(text)
    except ValueError as error:
        raise SpecError(
            "native staging control is not one JSON document", "invalid_completion"
        ) from error
    if (
        not isinstance(value, dict)
        or set(value)
        != {
            "schema_version",
            "ticket",
            "invocation_id",
            "proposal_digest",
            "state",
            "accepted",
        }
        or type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or value["ticket"] != ticket
        or value["invocation_id"] != invocation_id
        or value["proposal_digest"] != proposal_digest
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", proposal_digest)
        or value["state"] != "staged"
        or value["accepted"] is not False
    ):
        raise SpecError(
            "native staging control does not match its invocation",
            "incompatible_handoff",
        )
    if canonical(value) != text.strip():
        raise SpecError(
            "native staging control is not canonical JSON", "invalid_completion"
        )
    return value

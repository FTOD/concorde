"""Untrusted native Pi submissions and deterministic, single-use Host acceptance.

This service does not launch or schedule Agents. The native child submits a proposal;
its documented post-run gate calls ``stage`` without asserting execution success.
File scope is prompt-level on this path. Digests detect changed proposals, not reads
or arbitrary filesystem access. Neither a submission nor a native receipt is business
completion. The caller supplies current-input checks and the domain acceptance service.
"""

from __future__ import annotations

import threading
import re
from pathlib import Path
from typing import Callable

from ..spec.repository import SpecError, digest
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


class NativeResultGate:
    """One invocation's proposal, owned by its live trusted Host.

    ``recheck`` checks current task/context/configuration and the effective declared
    policy; ``validate`` checks schema and business-result identity. ``persist`` is
    the provider's trusted acceptance transaction, never supplied by a model. The
    Host retains the actual proposal digest independently from writable scratch.
    A failed persistence attempt is terminal: retrying the workflow requires fresh
    admission or the provider's explicit recovery (not blind effect replay).
    """

    def __init__(
        self,
        invocation_id: str,
        proposal_path: Path,
        *,
        ticket: str,
        recheck: Callable[[], None],
        validate: Callable[[dict], None],
        persist: Callable[[dict], dict],
        verify_execution: Callable[[], None],
    ):
        if not invocation_id or not proposal_path.is_absolute():
            raise ValueError(
                "native result gate requires a Host identity and absolute path"
            )
        if not isinstance(ticket, str) or not ticket:
            raise ValueError("native result gate requires a workflow ticket")
        self.ticket = ticket
        self.invocation_id = invocation_id
        self.proposal_path = proposal_path
        self.recheck = recheck
        self.validate = validate
        self.persist = persist
        self.verify_execution = verify_execution
        self._lock = threading.RLock()
        self._proposal: bytes | None = None
        self._digest: str | None = None
        self._accepted: dict | None = None
        self._failure: str | None = None

    def submit(self, invocation_id: str, value: dict) -> dict:
        """Stage one schema/business-checked proposal, without accepting completion."""
        with self._lock:
            self._identity(invocation_id)
            if self._proposal is not None:
                raise SpecError("native result already submitted", "invalid_completion")
            if not isinstance(value, dict):
                raise SpecError("native result must be an object", "invalid_completion")
            raw = canonical(value).encode("utf-8")
            if len(raw) > MAX_PROPOSAL_BYTES:
                raise SpecError("native result exceeds 1 MiB", "invalid_completion")
            candidate = decode(raw.decode("utf-8"))
            self.validate(candidate)
            # A host-created per-invocation directory is a caller prerequisite. It
            # is scratch, never a second authoritative status or runs archive.
            with self.proposal_path.open("xb") as stream:
                stream.write(raw)
                stream.flush()
            self._proposal, self._digest = raw, digest(raw)
            return {
                "invocation_id": self.invocation_id,
                "proposal_digest": self._digest,
                "accepted": False,
            }

    def _checked_proposal(self, invocation_id: str) -> dict:
        self._identity(invocation_id)
        if self._proposal is None:
            raise SpecError("native child submitted no result", "invalid_completion")
        if any(
            path.is_symlink()
            for path in (self.proposal_path, *self.proposal_path.parents)
        ):
            raise SpecError("native proposal is aliased", "unsafe_path")
        with self.proposal_path.open("rb") as stream:
            raw = stream.read(MAX_PROPOSAL_BYTES + 1)
        if raw != self._proposal or digest(raw) != self._digest:
            raise SpecError(
                "native proposal changed after submission", "stale_evidence"
            )
        self.recheck()
        value = decode(raw.decode("utf-8"))
        self.validate(value)
        return value

    def stage(self, invocation_id: str) -> dict:
        """Plain gate validation, deliberately WITHOUT domain persistence.

        pi-subagents can execute a gate after a failed child. Gate execution
        is not proof of native success, even if submission previously succeeded.
        """
        with self._lock:
            self._checked_proposal(invocation_id)
            return control_value(
                {
                    "schema_version": 1,
                    "ticket": self.ticket,
                    "invocation_id": self.invocation_id,
                    "proposal_digest": self._digest,
                    "accepted": False,
                    "state": "staged",
                }
            )

    def finalize(self, invocation_id: str) -> dict:
        """Reconcile native terminal evidence independently before domain commit."""
        with self._lock:
            self._identity(invocation_id)
            try:
                # The caller's verifier reads independently correlated native
                # evidence. A caller-supplied success boolean is not this service.
                self.verify_execution()
                value = self._checked_proposal(invocation_id)
                if self._accepted is not None:
                    return control_value(self._accepted)
                result = self.persist(value)
                self._accepted = control_value(result)
                return control_value(self._accepted)
            except BaseException:
                # In particular, an uncertain persistence acknowledgement must
                # never invoke the mutation again from a duplicate command.
                self._failure = "native acceptance failed; fresh admission or explicit recovery required"
                raise

    @property
    def committed_result(self) -> dict | None:
        """Historical committed effects survive a later failed execution recheck.

        This accessor does not assert current readiness or native success. The
        provider's durable journal/receipt remains authoritative across restart.
        """
        with self._lock:
            return None if self._accepted is None else control_value(self._accepted)

    def stop(self, reason: str) -> None:
        """Cancellation/failure revokes unsettled acceptance; it does not undo edits."""
        with self._lock:
            if self._accepted is None:
                self._failure = reason

    def _identity(self, invocation_id: str) -> None:
        if invocation_id != self.invocation_id:
            raise SpecError("foreign native invocation", "incompatible_handoff")
        if self._failure is not None:
            raise SpecError(self._failure, "invalid_completion")

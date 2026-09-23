"""A deterministic single Agent call driven through the native driver's actions.

``NativeCallFixture`` is a ``unittest.TestCase`` mixin: ``setUp`` writes the transfer fixture
project, admits a stand-in pi-subagents binding and keeps every prepared call directory inside the
test's own scratch. Nothing launches Pi or a model; the native records an accepted run would leave
are written synthetically by :meth:`NativeCallFixture.evidence`.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from concorde.harness.native_driver import execute
from concorde.harness.native_runtime import FORMAT, NativeRuntimeBinding
from concorde.operations.dispatch import services
from concorde.spec.typed_data import canonical, typed
from tests.concorde.support.spec_project import PACKAGE, project

CONTROL = ("schema_version", "ticket", "invocation_id", "proposal_digest", "state")
LAUNCH_DIGEST = "sha256:" + "1" * 64


def errors(value: dict) -> list[dict]:
    """The error entries of a rejected native answer."""
    return value["result"]["errors"]


def codes(value: dict) -> set[str]:
    return {entry["code"] for entry in errors(value)}


class NativeCallFixture:
    operation = "concorde-context-solve"

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name) / "project"
        self.root.mkdir()
        # Every directory the driver creates with ``tempfile`` lands here, where it is counted.
        self.calls = Path(self.scratch.name) / "tmp"
        self.calls.mkdir()
        tempdir = patch.object(tempfile, "tempdir", str(self.calls))
        tempdir.start()
        self.addCleanup(tempdir.stop)
        project(self.root)
        before = Path.cwd()
        self.addCleanup(os.chdir, before)
        os.chdir(self.root)
        self.native = Path(self.scratch.name) / "native"
        self.native.mkdir()
        runtime = patch(
            "concorde.harness.native_driver.admit_native_runtime",
            return_value=NativeRuntimeBinding(
                FORMAT, str(self.native), "sha256:" + "0" * 64
            ),
        )
        runtime.start()
        self.addCleanup(runtime.stop)
        self.envelope = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": self.operation,
            "mode": "execute",
            "configuration": None,
            "input": typed(
                self.operation + "-request",
                {"target_id": "service.transfer", "task": "Assess transfer"},
            ),
        }

    # -- actions -------------------------------------------------------------------------

    def prepare(self, **payload):
        value = {
            "invocation": self.envelope,
            "native_root": str(self.native),
            "session_id": "unit-session",
            **payload,
        }
        return execute(PACKAGE, "prepare", value, services=services())

    def command(self, prepared, action, payload=None):
        return execute(
            PACKAGE,
            action,
            {} if payload is None else payload,
            prepared["descriptor"],
            prepared["digest"],
            services=services(),
        )

    def directory(self, prepared) -> Path:
        return Path(prepared["descriptor"]).parent

    def descriptor(self, prepared) -> dict:
        return json.loads(Path(prepared["descriptor"]).read_text())

    def proposal(self, prepared, **data):
        return {
            "invocation_id": prepared["ticket"],
            "result": typed(
                "concorde-agent-stage-result",
                {
                    "context_id": self.descriptor(prepared)["snapshot"]["context_id"],
                    "outcome": "sufficient",
                    "answer": "Sufficient",
                    "blockers": [],
                    "documents": [],
                    "plan": "",
                    "tasks": [],
                    **data,
                },
            ),
        }

    def staged(self, prepared, **data):
        """Submit a valid proposal and stage it, as the child extension and the gate would."""
        proposal = self.proposal(prepared, **data)
        submitted = self.command(prepared, "submit", proposal)
        assert submitted.get("state") == "proposed", submitted
        staged = self.command(prepared, "stage")
        assert staged.get("state") == "staged", staged
        return proposal, {key: staged[key] for key in (*CONTROL, "accepted")}

    def evidence(self, prepared, proposal, control, *, row=None, metadata=None):
        """The correlated native result the call extension hands ``accept`` after a run.

        The structured output and the run metadata are written as pi-subagents would leave them;
        ``row`` and ``metadata`` override their fields.
        """
        records = Path(self.scratch.name) / "records" / prepared["ticket"]
        records.mkdir(parents=True, exist_ok=True)
        output = records / "output.json"
        output.write_text(canonical(proposal))
        external = prepared["call"]["agent"]
        gate = prepared["call"]["gate"]["command"]
        written = {
            "runId": "run-1",
            "agent": external,
            "launchContractDigest": LAUNCH_DIGEST,
            "exitCode": 0,
            "acceptance": {
                "status": "verified",
                "verifyRuns": [
                    {
                        "command": gate,
                        "status": "passed",
                        "exitCode": 0,
                        "stdout": canonical(control),
                    }
                ],
            },
            **(metadata or {}),
        }
        (records / "metadata.json").write_text(canonical(written))
        return {
            "details": {
                "mode": "single",
                "runId": "run-1",
                "results": [
                    {
                        "agent": external,
                        "exitCode": 0,
                        "launchContractDigest": LAUNCH_DIGEST,
                        "structuredOutputPath": str(output),
                        "artifactPaths": {
                            "metadataPath": str(records / "metadata.json")
                        },
                        **(row or {}),
                    }
                ],
            },
            "isError": False,
            "tool_call_id": "tool-1",
            "session_id": "unit-session",
            "launch_contract_digest": LAUNCH_DIGEST,
            "gate_command": gate,
        }

    def archives(self) -> list[Path]:
        return sorted(self.root.glob(".concorde/runs/*/native-context.json"))

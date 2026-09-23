"""Drive the solve workflow through the production native driver with synthetic native evidence.

``SolveCandidate`` is a ``unittest.TestCase`` mixin over ``WorktreeProject``: the transfer fixture
is committed in a primary worktree, an Issue about the transfer Module is reported and committed
in the linked candidate, and the solve runs there. Every step goes through
``concorde.harness.native_driver`` exactly as the Pi entry calls it; only what pi-subagents would
publish (the launch binding, the workflow status, each child's metadata and structured output and
the preflight contract) is written by the test. No model runs.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

from concorde.harness import native_driver
from concorde.harness.change_worktree import git, read_change
from concorde.harness.native_runtime import FORMAT, NativeRuntimeBinding
from concorde.issue_solving.records import solutions
from concorde.issues.store import read_issue, report_issue
from concorde.operations.dispatch import services
from concorde.spec.typed_data import canonical, typed
from tests.concorde.support.issue_reports import report, source
from tests.concorde.support.spec_project import PACKAGE
from tests.concorde.support.worktree_project import WorktreeProject

CONTROL = ("schema_version", "ticket", "invocation_id", "proposal_digest", "state")
SESSION = "native-session"
LAUNCH = "sha256:" + "c" * 64
FIXED = (
    "def transfer(balance, amount):\n"
    "    if amount <= 0 or amount > balance:\n"
    '        raise ValueError("invalid transfer")\n'
    "    return balance - amount\n"
)


def write(path: Path, value) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(value))
    return str(path)


def transfer_report(key="overdraft", **changes) -> dict:
    return report(
        **{
            "report_key": key,
            "type": "bug",
            "subtype": None,
            "title": "Transfer accepts an overdraft",
            "description": "transfer(10, 20) returns a balance instead of refusing.",
            "impact": "An unaffordable transfer succeeds.",
            "basis": "scenario.transfer.reject requires ValueError.",
            "owner_target_id": "service.transfer",
            "evidence": [],
            **changes,
        }
    )


def commit_issues(root, message="Record Issues", *paths):
    """Commit the Issue records (and ``paths``), never the store's lock in the run records."""
    git(root, "add", "--", ".concorde/issues", *paths)
    git(root, "commit", "-qm", message)


class SolveCandidate(WorktreeProject):
    """A candidate holding one committed open Issue of the transfer Module."""

    def setUp(self):
        super().setUp()
        self.evidence = self.directory / "native-evidence"
        scratch = self.directory / "scratch"
        scratch.mkdir()
        for patcher in (
            patch.object(tempfile, "tempdir", str(scratch)),
            patch(
                "concorde.harness.native_driver.admit_native_runtime",
                return_value=NativeRuntimeBinding(
                    FORMAT, str(self.directory), "sha256:" + "0" * 64
                ),
            ),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        before = Path.cwd()
        self.addCleanup(os.chdir, before)
        self.context = {"services": services(), "provenance": None}
        self.issue = self.file_issue(self.change)

    def file_issue(self, root, key="overdraft", **changes):
        """Report an Issue in ``root`` and commit it there; the user session already fixed it."""
        receipt = report_issue(
            root,
            transfer_report(key, **changes),
            source(target_id="service.transfer"),
        )
        (root / "app/transfer.py").write_text(FIXED)
        commit_issues(root, "Record the overdraft Issue and fix it", "app/transfer.py")
        return receipt["issue_id"]

    # -- requests ---------------------------------------------------------------------------

    def envelope(self, data, mode="execute"):
        return {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-issues",
            "mode": mode,
            "configuration": None,
            "input": typed("concorde-issues-request", data),
        }

    def prepare(self, mode="execute", *, root=None, **data):
        """The native ``prepare`` of a ``solve`` request, started in the candidate or ``root``."""
        os.chdir(root or self.change)
        return native_driver.execute(
            PACKAGE,
            "prepare",
            {
                "invocation": self.envelope(
                    {"action": "solve", "issue_id": self.issue, **data}, mode
                ),
                "native_root": str(self.directory),
                "session_id": SESSION,
            },
            **self.context,
        )

    def start(self, **data):
        prepared = self.prepare(**data)
        self.assertEqual("prepared", prepared["state"], prepared)
        return SolveWorkflow(self, prepared)

    def action(self, slot, action, payload=None):
        return native_driver.execute(
            PACKAGE,
            action,
            payload or {},
            slot["descriptor"],
            slot["digest"],
            **self.context,
        )

    # -- records ----------------------------------------------------------------------------

    def record(self, root=None):
        return read_issue(root or self.change, self.issue)

    def issue_bytes(self, root=None):
        return (
            (root or self.change) / f".concorde/issues/{self.issue}.md"
        ).read_bytes()

    def change_state(self, root=None):
        return read_change(root or self.change, required=True)

    def solution(self, root=None):
        return solutions(self.change_state(root)).get(self.issue)

    # -- native evidence ----------------------------------------------------------------------

    def evidence_row(self, call, proposal, control, **row):
        """The native terminal row and metadata pi-subagents publishes for one child."""
        run_id = "run-" + uuid.uuid4().hex
        output = write(self.evidence / run_id / "output.json", proposal)
        metadata = {
            "runId": run_id,
            "agent": call["agent"],
            "launchContractDigest": LAUNCH,
            "exitCode": 0,
            "acceptance": {
                "status": "verified",
                "verifyRuns": [
                    {
                        "command": call["gate"]["command"],
                        "status": "passed",
                        "exitCode": 0,
                        "stdout": canonical(control),
                    }
                ],
            },
        }
        path = write(self.evidence / run_id / "metadata.json", metadata)
        return run_id, {
            "agent": call["agent"],
            "exitCode": 0,
            "launchContractDigest": LAUNCH,
            "structuredOutputPath": output,
            "artifactPaths": {"metadataPath": path},
            **row,
        }


class SolveWorkflow:
    """One launched solve Workflow whose solver and reviewers are scripted by the test."""

    def __init__(self, test: SolveCandidate, prepared: dict):
        self.test = test
        self.prepared = prepared
        self.path = prepared["descriptor"]
        self.digest = prepared["digest"]
        self.directory = Path(self.path).parent
        self.run_id = "workflow-" + uuid.uuid4().hex
        self.status_dir = test.evidence / self.run_id
        self.status = {
            "runId": self.run_id,
            "mode": "workflow",
            "sessionId": SESSION,
            "state": "running",
            "steps": [],
            "workflow": {"emits": []},
        }
        self.save()
        write(
            self.directory / "workflow-binding.json",
            {"asyncDir": str(self.status_dir), "runId": self.run_id},
        )

    def save(self):
        write(self.status_dir / "status.json", self.status)

    def slot(self, key):
        return json.loads((self.directory / "bindings" / f"{key}.json").read_text())

    def slot_descriptor(self, key):
        return json.loads(Path(self.slot(key)["descriptor"]).read_text())

    def keys(self, prefix):
        return sorted(
            path.stem for path in (self.directory / "bindings").glob(prefix + "*.json")
        )

    def host_step(self, name):
        """One Host step: the Python ``workflow-<name>`` service, then each new slot's preflight."""
        value = native_driver.workflow_step(
            PACKAGE, name, self.path, self.digest, self.test.context
        )
        for binding in sorted((self.directory / "bindings").glob("*.json")):
            slot = json.loads(binding.read_text())
            preflight = Path(slot["descriptor"]).parent / "preflight.json"
            if not preflight.exists():
                write(preflight, {"launchContractDigest": LAUNCH})
        return value

    def child(self, key, data, *, publish=True, **row):
        """Run one issued slot's child: submit, pass its slot gate and publish its evidence."""
        slot = self.slot(key)
        descriptor = self.slot_descriptor(key)
        proposal = {
            "invocation_id": slot["ticket"],
            "result": typed(descriptor["result_type"], data),
        }
        submitted = self.test.action(slot, "submit", proposal)
        self.test.assertEqual("proposed", submitted.get("state"), submitted)
        staged = native_driver.slot_gate(
            PACKAGE, self.path, self.digest, key, self.test.context
        )
        self.test.assertEqual("staged", staged.get("state"), staged)
        if not publish:
            return proposal
        control = {name: staged[name] for name in (*CONTROL, "accepted")}
        run_id, result = self.test.evidence_row(slot["call"], proposal, control, **row)
        self.status["steps"].append(
            {
                "workflowKey": key,
                "runId": run_id,
                "parentWorkflowRunId": self.run_id,
                "agent": slot["call"]["agent"],
                "status": "completed",
            }
        )
        self.status["workflow"]["emits"].append(
            {
                "kind": "concorde.child-terminal",
                "ticket": self.prepared["ticket"],
                "key": key,
                "agent": slot["call"]["agent"],
                "runId": run_id,
                "invocation_id": slot["ticket"],
                "proposal_digest": control["proposal_digest"],
                "metadata": result["artifactPaths"]["metadataPath"],
                "result": result,
            }
        )
        self.save()
        return proposal

    # -- scripted answers ---------------------------------------------------------------------

    def decision(
        self, index, action, *, duplicate_of=None, outcome="completed", **extra
    ):
        """The solver's answer in slot ``d-<index>``."""
        descriptor = self.slot_descriptor(f"d-{index}")
        data = {
            "context_id": descriptor["snapshot"]["context_id"],
            "outcome": outcome,
            "answer": "Decided " + action,
            "blockers": [],
            "documents": [],
            "plan": "",
            "tasks": [],
            "issue_decision": {
                "action": action,
                "intent": "Settle the overdraft Issue by " + action,
                "rationale": "scenario.transfer.reject requires ValueError; " + action,
                "duplicate_of": duplicate_of,
            },
            **extra,
        }
        return self.child(f"d-{index}", data)

    def selection(self, index):
        """The Issue selection the Host admitted for solver slot ``d-<index>``."""
        inputs = self.slot_descriptor(f"d-{index}")["snapshot"]["stage_inputs"]
        return next(
            item["data"]
            for item in inputs
            if item["type_id"] == "concorde-issue-selection"
        )

    def review(self, key, *, blocking=False):
        """A reviewer's answer for review slot ``key``; a blocking one reports an Issue."""
        descriptor = self.slot_descriptor(key)
        review = descriptor["review_input"]
        issues = []
        if blocking:
            slot = self.slot(key)
            receipt = self.test.action(
                slot,
                "report",
                transfer_report(
                    "review-" + key,
                    title="Transfer still accepts an overdraft",
                    owner_target_id=descriptor["snapshot"]["target_id"],
                ),
            )["receipt"]
            issues = [
                {
                    **receipt,
                    "severity": "blocking",
                    "affected_task": "Reject overdrafts",
                }
            ]
        return self.child(
            key,
            {
                "context_id": descriptor["snapshot"]["context_id"],
                "input_digest": review["input_digest"],
                "review_mode": review["review_mode"],
                "status": "findings" if issues else "no_findings",
                "representative_tasks": ["Verify the overdraft Issue"],
                "issues": issues,
                "answer": "Reviewed " + descriptor["snapshot"]["target_id"],
            },
        )

    def review_all(self, index, *, blocking=()):
        for key in self.keys(f"v-{index}-"):
            self.review(key, blocking=key in blocking)

    def result(self):
        """``workflow-result``: the receipt, or the running or failed native state."""
        return native_driver.workflow_result(
            PACKAGE, self.path, self.digest, self.test.context
        )

    def output(self):
        value = self.result()
        self.test.assertTrue(value.get("accepted"), value)
        return value["output"]["data"]

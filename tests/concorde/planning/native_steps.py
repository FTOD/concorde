"""Drive the production native driver in a managed candidate with synthetic native evidence.

``NativeCandidate`` is a ``unittest.TestCase`` mixin over ``WorktreeProject``: the transfer
fixture project is committed in a primary worktree and the tests run in its linked candidate. Every
action goes through ``concorde.harness.native_driver`` exactly as the Pi entry calls it; only what
pi-subagents would publish (the launch binding, the workflow status, each child's metadata, its
structured output and the preflight contract) is written by the test. No model runs.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

from concorde.harness import native_driver
from concorde.harness.change_worktree import bind_owner, ensure_change, read_change
from concorde.harness.configuration import load_configuration
from concorde.harness.host import OperationHost
from concorde.harness.invocation import Invocation
from concorde.harness.native_runtime import FORMAT, NativeRuntimeBinding
from concorde.operations.dispatch import services
from concorde.planning.plan import persist_plan_result
from concorde.planning.records import targets
from concorde.planning.tasks import persist_tasks, prepare_tasks, validate_tasks
from concorde.spec.repository import digest
from concorde.spec.typed_data import canonical, typed
from tests.concorde.support.spec_project import PACKAGE
from tests.concorde.support.worktree_project import WorktreeProject

CONTROL = ("schema_version", "ticket", "invocation_id", "proposal_digest", "state")
SESSION = "native-session"
LAUNCH = "sha256:" + "c" * 64


def _write(path: Path, value) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(value))
    return str(path)


class NativeCandidate(WorktreeProject):
    """A managed candidate of the transfer fixture and the native actions run inside it."""

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
        os.chdir(self.change)
        self.context = {"services": services(), "provenance": None}

    # -- requests ---------------------------------------------------------------------------

    def envelope(self, operation, data, mode="execute"):
        return {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": operation,
            "mode": mode,
            "configuration": None,
            "input": typed(operation + "-request", data),
        }

    def prepare(self, operation, data=None, mode="execute", *, root=None):
        """The native ``prepare`` action of one request, started in the candidate or ``root``."""
        os.chdir(root or self.change)
        return native_driver.execute(
            PACKAGE,
            "prepare",
            {
                "invocation": self.envelope(operation, data or self.task, mode),
                "native_root": str(self.directory),
                "session_id": SESSION,
            },
            **self.context,
        )

    def action(self, prepared, action, payload=None):
        return native_driver.execute(
            PACKAGE,
            action,
            payload or {},
            prepared["descriptor"],
            prepared["digest"],
            **self.context,
        )

    def invocation(self, operation, data=None):
        """The Module-bound invocation of a request, as dispatch binds it, for record checks."""
        return Invocation(
            operation,
            load_configuration(self.change),
            dict(data or self.task),
            OperationHost(self.change, PACKAGE),
        )

    def change_state(self):
        return read_change(self.change, required=True)

    def own(self, data=None):
        """Register the candidate's change and bind its owner, as a first mutating request does."""
        ensure_change(self.change, task=data or self.task)
        bind_owner(self.change, data or self.task)

    def target(self, target_id="service.transfer"):
        """The planning progress entry of one Module, or None."""
        return targets(read_change(self.change)).get(target_id)

    def accepted_plan(self, plan="Accepted plan", data=None):
        """Accept a plan through Planning's plan record, as the planner hook does."""
        run = self.invocation("concorde-plan", data)
        run.completed = ["concorde-context-solve", "concorde-plan"]
        return persist_plan_result(run, {"plan": plan, "answer": "Planned"})

    def accepted_tasks(self, tasks, data=None):
        """Accept a task list through Planning's task record, as the task-author hook does."""
        run = self.invocation("concorde-tasks", data)
        state, _, reserved, repair, scope = prepare_tasks(run)
        validate_tasks(run, {"tasks": tasks}, reserved)
        return persist_tasks(
            run, {"tasks": tasks, "answer": "Tasks"}, state, repair, scope
        )

    def refused(self, value, code):
        """Assert a native action was refused with ``code`` before anything was prepared."""
        self.assertEqual("rejected", value.get("state"), value)
        self.assertFalse(value.get("accepted"))
        self.assertNotIn("descriptor", value)
        self.assertEqual(
            [code], [error["code"] for error in value["result"]["errors"]], value
        )

    # -- one Agent call -----------------------------------------------------------------------

    def descriptor(self, prepared):
        return json.loads(Path(prepared["descriptor"]).read_text())

    def proposal(self, prepared, data):
        descriptor = self.descriptor(prepared)
        return {
            "invocation_id": prepared["ticket"],
            "result": typed(descriptor["result_type"], data),
        }

    def report(self, prepared, key="gap", **fields):
        """Report one Issue through the call's reporting service; returns its receipt."""
        report = {
            "report_key": key,
            "type": "gap",
            "subtype": "missing-contract",
            "title": "Missing promise",
            "description": "The transfer Spec does not state the rounding rule.",
            "impact": "The task cannot be planned.",
            "basis": "The transfer Spec is silent on rounding.",
            "owner_target_id": self.descriptor(prepared)["snapshot"]["target_id"],
            "evidence": [],
            **fields,
        }
        value = self.action(prepared, "report", report)
        return value["receipt"]

    def evidence_row(self, prepared_call, proposal, control, **row):
        """The native terminal row and metadata pi-subagents publishes for one child."""
        run_id = "run-" + uuid.uuid4().hex
        output = _write(self.evidence / run_id / "output.json", proposal)
        metadata = {
            "runId": run_id,
            "agent": prepared_call["agent"],
            "launchContractDigest": LAUNCH,
            "exitCode": 0,
            "acceptance": {
                "status": "verified",
                "verifyRuns": [
                    {
                        "command": prepared_call["gate"]["command"],
                        "status": "passed",
                        "exitCode": 0,
                        "stdout": canonical(control),
                    }
                ],
            },
        }
        path = _write(self.evidence / run_id / "metadata.json", metadata)
        return run_id, {
            "agent": prepared_call["agent"],
            "exitCode": 0,
            "launchContractDigest": LAUNCH,
            "structuredOutputPath": output,
            "artifactPaths": {"metadataPath": path},
            **row,
        }

    def stage(self, prepared, data):
        """Submit ``data`` as the child's proposal and pass its staging gate."""
        proposal = self.proposal(prepared, data)
        submitted = self.action(prepared, "submit", proposal)
        self.assertEqual("proposed", submitted.get("state"), submitted)
        staged = self.action(prepared, "stage")
        self.assertEqual("staged", staged.get("state"), staged)
        return proposal, {key: staged[key] for key in (*CONTROL, "accepted")}

    def correlation(self, prepared, proposal, control, **row):
        run_id, value = self.evidence_row(prepared["call"], proposal, control, **row)
        return {
            "details": {"mode": "single", "runId": run_id, "results": [value]},
            "isError": False,
            "tool_call_id": "tool-" + run_id,
            "session_id": SESSION,
            "launch_contract_digest": LAUNCH,
            "gate_command": prepared["call"]["gate"]["command"],
        }

    def complete(self, prepared, data, **row):
        """Run the prepared call to acceptance: submit, stage, then accept its native evidence."""
        proposal, control = self.stage(prepared, data)
        return self.action(
            prepared, "accept", self.correlation(prepared, proposal, control, **row)
        )

    def stage_result(self, prepared, **fields):
        """A ``concorde-agent-stage-result`` for the prepared call's frozen context."""
        return {
            "context_id": self.descriptor(prepared)["snapshot"]["context_id"],
            "outcome": "sufficient",
            "answer": "Answered",
            "blockers": [],
            "documents": [],
            "plan": "",
            "tasks": [],
            **fields,
        }

    # -- one Workflow ---------------------------------------------------------------------------

    def workflow(self, prepared):
        """Launch the prepared Workflow as pi-subagents would: its binding and running status."""
        return NativeWorkflow(self, prepared)

    def start_review(self, mode, data=None, *, root=None):
        """Prepare and launch a review workflow and run its ``bind`` step."""
        prepared = self.prepare(f"concorde-{mode}-review", data, root=root)
        self.assertEqual("prepared", prepared["state"], prepared)
        workflow = self.workflow(prepared)
        self.assertEqual({"state": "ready"}, workflow.host_step("bind"))
        return workflow

    def review_result(self, workflow, key, *, blocking=False, **fields):
        """A reviewer's answer for one member; a blocking one reports and cites an Issue."""
        descriptor = workflow.slot_descriptor(key)
        review = descriptor["review_input"]
        issues = []
        if blocking:
            target_id = descriptor["snapshot"]["target_id"]
            slot = workflow.slot(key)
            issue = self.report(
                slot,
                key="review-" + target_id,
                type="bug",
                subtype=None,
                title="Transfer accepts an overdraft",
                description="transfer(10, 20) returns a balance instead of refusing.",
                impact="An unaffordable transfer succeeds.",
                basis="scenario.transfer.reject requires ValueError.",
                owner_target_id=target_id,
            )
            issues = [
                {**issue, "severity": "blocking", "affected_task": "Reject overdrafts"}
            ]
        return {
            "context_id": descriptor["snapshot"]["context_id"],
            "input_digest": review["input_digest"],
            "review_mode": review["review_mode"],
            "status": "findings" if issues else "no_findings",
            "representative_tasks": ["Review the transfer contract"],
            "issues": issues,
            "answer": "Reviewed " + descriptor["snapshot"]["target_id"],
            **fields,
        }

    def run_review(self, mode, data=None, *, root=None, blocking=()):
        """A complete review workflow; members whose Module is in ``blocking`` block."""
        workflow = self.start_review(mode, data, root=root)
        for key in workflow.review_keys():
            target_id = workflow.slot_descriptor(key)["snapshot"]["target_id"]
            workflow.child(
                key,
                self.review_result(workflow, key, blocking=target_id in blocking),
            )
        finished = workflow.host_step("finalize")
        self.assertTrue(finished["accepted"], finished)
        receipt = workflow.result()
        self.assertTrue(receipt["accepted"], receipt)
        return workflow, receipt["output"]["data"]


class NativeWorkflow:
    """One launched native Workflow whose children are scripted by the test."""

    def __init__(self, test: NativeCandidate, prepared: dict):
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
        _write(
            self.directory / "workflow-binding.json",
            {"asyncDir": str(self.status_dir), "runId": self.run_id},
        )

    def save(self):
        _write(self.status_dir / "status.json", self.status)

    def slot(self, key):
        return json.loads((self.directory / "bindings" / f"{key}.json").read_text())

    def slot_descriptor(self, key):
        return json.loads(Path(self.slot(key)["descriptor"]).read_text())

    def review_keys(self):
        """The reviewer slots of a review workflow, in scope order."""
        return json.loads((self.directory / "review-scope.json").read_text())["keys"]

    def members(self):
        """The Modules of a review workflow's scope, in scope order."""
        return [
            self.slot_descriptor(key)["snapshot"]["target_id"]
            for key in self.review_keys()
        ]

    def host_step(self, name):
        """One Host step: the Python ``workflow-<name>`` service, then each new slot's preflight."""
        value = native_driver.workflow_step(
            PACKAGE, name, self.path, self.digest, self.test.context
        )
        for binding in sorted((self.directory / "bindings").glob("*.json")):
            slot = json.loads(binding.read_text())
            preflight = Path(slot["descriptor"]).parent / "preflight.json"
            if not preflight.exists():
                _write(preflight, {"launchContractDigest": LAUNCH})
        return value

    def child(self, key, data, **row):
        """Run one issued slot's child: submit, pass its slot gate and publish its evidence."""
        slot = self.slot(key)
        prepared = {**slot, "call": slot["call"]}
        proposal = self.test.proposal(prepared, data)
        submitted = self.test.action(prepared, "submit", proposal)
        self.test.assertEqual("proposed", submitted.get("state"), submitted)
        staged = native_driver.slot_gate(
            PACKAGE, self.path, self.digest, key, self.test.context
        )
        self.test.assertEqual("staged", staged.get("state"), staged)
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

    def stop_native(self, state="failed"):
        """The native Workflow ends without a receipt (a failed child or a stop)."""
        self.status["state"] = state
        if state == "failed":
            self.status["error"] = "Native child did not complete"
        self.save()

    def result(self):
        """``workflow-result``: the receipt, or the running or failed native state."""
        return native_driver.workflow_result(
            PACKAGE, self.path, self.digest, self.test.context
        )


def stage_result_for(descriptor: dict, **fields) -> dict:
    """A ``concorde-agent-stage-result`` for a slot descriptor's frozen context."""
    return {
        "context_id": descriptor["snapshot"]["context_id"],
        "outcome": "sufficient",
        "answer": "Answered",
        "blockers": [],
        "documents": [],
        "plan": "",
        "tasks": [],
        **fields,
    }


def tasks_digest(tasks) -> str:
    return digest(canonical(tasks).encode())


def task_item(identity, target_id="service.transfer", *, complete=False) -> dict:
    """One implementation task of the ``contract.planning.implementation-task`` shape."""
    return {
        "id": identity,
        "target_id": target_id,
        "description": f"Implement {identity}",
        "acceptance": f"A check shows {identity} works",
        "complete": complete,
    }


def failure_codes(error) -> set[str]:
    """Every code in an error's causal feedback, so a wrapped refusal keeps its cause."""
    codes = {getattr(error, "code", None)}
    pending = [getattr(error, "feedback", None) or {}]
    while pending:
        feedback = pending.pop()
        codes.add(feedback.get("code"))
        pending.extend(feedback.get("causes", []))
    return codes - {None}

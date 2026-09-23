"""A scripted user session for the Framework acceptance tests: real Host code, no model.

``ScriptedSession`` plays the parts of a user session that are outside Concorde's Python code: the
Pi session extension that calls the native driver, and pi-subagents, which launches each prepared
Agent, runs its staging gate and publishes native terminal records. Every Agent answer comes from a
function the test supplies; the synthetic native records are exactly the fields the Host verifies.
Everything else (admission, context freezing, hooks, acceptance, records, checks) is the
production code path.
"""

from __future__ import annotations

import itertools
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from concorde.harness.native_driver import (
    execute,
    workflow_result,
    workflow_step,
)
from concorde.harness.native_runtime import FORMAT, NativeRuntimeBinding
from concorde.operations.dispatch import services
from concorde.spec.typed_data import canonical, typed

from tests.concorde.support.spec_project import PACKAGE

LAUNCH = "sha256:" + "1" * 64
SESSION = "acceptance-session"
CONTROL_FIELDS = (
    "schema_version",
    "ticket",
    "invocation_id",
    "proposal_digest",
    "state",
    "accepted",
)


def _json(path) -> dict:
    return json.loads(Path(path).read_text())


@dataclass
class Child:
    """What one launched Agent sees and may do: its frozen context and its reporting service."""

    session: ScriptedSession
    descriptor_path: str
    descriptor_digest: str

    @property
    def descriptor(self) -> dict:
        return _json(self.descriptor_path)

    @property
    def context_id(self) -> str:
        return self.descriptor["snapshot"]["context_id"]

    @property
    def review_input(self) -> dict:
        return self.descriptor["review_input"]

    @property
    def stage_inputs(self) -> list[dict]:
        return self.descriptor["stage_inputs"]

    def report(self, report: dict) -> dict:
        """File an Issue through the call's ``report_issue`` tool; returns its receipt."""
        value = self.session.action(
            "report", report, self.descriptor_path, self.descriptor_digest
        )
        return value["receipt"]


def stage_result(child: Child, outcome: str, answer: str, **fields) -> dict:
    """An Agent's ``concorde-agent-stage-result`` for its own frozen context."""
    return typed(
        "concorde-agent-stage-result",
        {
            "context_id": child.context_id,
            "outcome": outcome,
            "answer": answer,
            "blockers": [],
            "documents": [],
            "plan": "",
            "tasks": [],
            **fields,
        },
    )


def review_result(child: Child, status: str, answer: str, **fields) -> dict:
    """A reviewer's ``concorde-review-stage-result`` for its own review input."""
    review = child.review_input
    return typed(
        "concorde-review-stage-result",
        {
            "context_id": child.context_id,
            "input_digest": review["input_digest"],
            "review_mode": review["review_mode"],
            "status": status,
            "representative_tasks": ["Check the transfer contract"],
            "issues": [],
            "answer": answer,
            **fields,
        },
    )


class AgentFailed(Exception):
    """Raised by an answer function: the Agent's run ends in failure without a result."""


class ScriptedSession:
    """The user session's native side, in process, working in ``root``."""

    def __init__(self, test, root: Path):
        self.test = test
        self.root = Path(root)
        scratch = tempfile.TemporaryDirectory(prefix="concorde-acceptance-native-")
        test.addCleanup(scratch.cleanup)
        self.scratch = Path(scratch.name)
        self.runtime = self.scratch / "runtime"
        self.runtime.mkdir()
        self.services = services()
        self.context = {"services": self.services, "provenance": None}
        self.counter = itertools.count()
        binding = NativeRuntimeBinding(FORMAT, str(self.runtime), "sha256:" + "0" * 64)
        runtime = patch(
            "concorde.harness.native_driver.admit_native_runtime",
            return_value=binding,
        )
        runtime.start()
        test.addCleanup(runtime.stop)
        before = Path.cwd()
        test.addCleanup(os.chdir, before)

    # -- the native driver's actions ---------------------------------------------------------

    def envelope(self, operation: str, request: dict) -> dict:
        return {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": operation,
            "mode": "execute",
            "configuration": None,
            "input": typed(operation + "-request", request),
        }

    def prepare(self, operation: str, request: dict) -> dict:
        os.chdir(self.root)
        return execute(
            PACKAGE,
            "prepare",
            {
                "invocation": self.envelope(operation, request),
                "native_root": str(self.runtime),
                "session_id": SESSION,
            },
            services=self.services,
        )

    def action(self, action: str, payload: dict, descriptor: str, identity: str):
        return execute(
            PACKAGE,
            action,
            payload,
            descriptor,
            identity,
            services=self.services,
        )

    # -- one launched Agent ------------------------------------------------------------------

    def run_child(self, descriptor: str, identity: str, gate: str, answer) -> dict:
        """Launch one prepared Agent: its answer is submitted and staged by its gate.

        Returns the native result row pi-subagents publishes for the completed child.
        """
        child = Child(self, descriptor, identity)
        slot = child.descriptor
        proposal = {"invocation_id": slot["ticket"], "result": answer(child)}
        submitted = self.action("submit", proposal, descriptor, identity)
        if submitted.get("state") != "proposed":
            raise AssertionError(f"the Host refused the proposal: {submitted}")
        staged = self.action("stage", {}, descriptor, identity)
        if staged.get("state") != "staged":
            raise AssertionError(f"the staging gate refused the proposal: {staged}")
        control = {key: staged[key] for key in CONTROL_FIELDS}
        index = next(self.counter)
        run_id = f"child-run-{index}"
        output = self.scratch / f"output-{index}.json"
        output.write_text(canonical(proposal))
        metadata = self.scratch / f"metadata-{index}.json"
        metadata.write_text(
            canonical(
                {
                    "runId": run_id,
                    "agent": slot["external"],
                    "launchContractDigest": LAUNCH,
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
                }
            )
        )
        return {
            "run_id": run_id,
            "control": control,
            "row": {
                "agent": slot["external"],
                "exitCode": 0,
                "launchContractDigest": LAUNCH,
                "structuredOutputPath": str(output),
                "artifactPaths": {"metadataPath": str(metadata)},
            },
        }

    # -- an Agent call -----------------------------------------------------------------------

    def call(self, operation: str, request: dict, answer) -> dict:
        """An Agent call: prepare, launch the Agent with ``answer``, then accept its result.

        Returns the operation result envelope; a request the Host ends before any Agent starts
        returns that result without calling ``answer``.
        """
        prepared = self.prepare(operation, request)
        if prepared.get("state") != "prepared":
            return prepared["result"]
        gate = prepared["call"]["gate"]["command"]
        try:
            child = self.run_child(
                prepared["descriptor"], prepared["digest"], gate, answer
            )
        except AgentFailed:
            return self._failed(prepared, gate)
        accepted = self.action(
            "accept",
            {
                "details": {
                    "mode": "single",
                    "runId": child["run_id"],
                    "results": [child["row"]],
                },
                "isError": False,
                "tool_call_id": "tool-call-" + child["run_id"],
                "session_id": SESSION,
                "launch_contract_digest": LAUNCH,
                "gate_command": gate,
            },
            prepared["descriptor"],
            prepared["digest"],
        )
        return accepted["result"]

    def _failed(self, prepared: dict, gate: str) -> dict:
        """What the session extension hands the Host when the Agent's run failed."""
        failed = self.action(
            "accept",
            {
                "details": {
                    "mode": "single",
                    "runId": "failed-run",
                    "results": [
                        {
                            "agent": _json(prepared["descriptor"])["external"],
                            "exitCode": 1,
                            "error": "model provider error",
                        }
                    ],
                },
                "isError": True,
                "tool_call_id": "tool-call-failed",
                "session_id": SESSION,
                "launch_contract_digest": LAUNCH,
                "gate_command": gate,
            },
            prepared["descriptor"],
            prepared["digest"],
        )
        return failed["result"]

    # -- a Workflow --------------------------------------------------------------------------

    def workflow(self, operation: str, request: dict, answers):
        """Run a prepared Workflow as its authored script does, with scripted Agents.

        ``answers(key)`` returns the answer function of the slot ``key``. An answer that raises
        ``AgentFailed`` fails the native Workflow at that child, as pi-subagents reports a failed
        child. Returns the Workflow's result: its receipt's output, or the Host's failure record.
        """
        prepared = self.prepare(operation, request)
        if prepared.get("state") != "prepared":
            return prepared["result"]
        run = _WorkflowRun(self, prepared)
        script = {
            "concorde-plan": run.plan,
            "concorde-code-review": run.review,
            "concorde-spec-review": run.review,
            "concorde-issues": run.issues,
        }[operation]
        try:
            script(answers)
        except AgentFailed:
            run.status["state"] = "failed"
            run.status["error"] = "a native child failed"
            run.publish()
        else:
            run.status["state"] = "complete"
            run.publish()
        value = workflow_result(PACKAGE, run.path, run.identity, self.context)
        return {
            "status": "succeeded" if value.get("accepted") else "failed",
            "state": value["state"],
            "output": value.get("output"),
            "failure": value.get("failure"),
        }


class _WorkflowRun:
    """The native state of one Workflow run and the script steps that drive it."""

    def __init__(self, session: ScriptedSession, prepared: dict):
        self.session = session
        self.path = prepared["descriptor"]
        self.identity = prepared["digest"]
        self.descriptor = _json(self.path)
        self.directory = Path(self.descriptor["directory"])
        self.run_id = "workflow-run-" + self.descriptor["ticket"]
        self.async_dir = session.scratch / ("async-" + self.descriptor["ticket"])
        self.async_dir.mkdir()
        self.status = {
            "runId": self.run_id,
            "mode": "workflow",
            "sessionId": SESSION,
            "state": "running",
            "steps": [],
            "workflow": {"emits": []},
        }
        self.publish()
        (self.directory / "workflow-binding.json").write_text(
            canonical({"asyncDir": str(self.async_dir), "runId": self.run_id})
        )
        self.preflight()

    def publish(self) -> None:
        (self.async_dir / "status.json").write_text(canonical(self.status))

    def preflight(self) -> None:
        """What the Host-step helper does after a step: check and preflight each new slot."""
        bindings = self.directory / "bindings"
        for path in sorted(bindings.glob("*.json")) if bindings.is_dir() else ():
            entry = _json(path)
            slot = Path(entry["descriptor"]).parent
            if (slot / "preflight.json").exists():
                continue
            checked = self.session.action(
                "check", {}, entry["descriptor"], entry["digest"]
            )
            if checked.get("state") != "prepared":
                raise AssertionError(f"slot {entry['key']} failed prelaunch: {checked}")
            (slot / "preflight.json").write_text(
                canonical({"launchContractDigest": LAUNCH})
            )

    def step(self, name: str) -> dict:
        value = workflow_step(
            PACKAGE, name, self.path, self.identity, self.session.context
        )
        self.preflight()
        return value

    def leaf(self, key: str, answers) -> None:
        entry = _json(self.directory / "bindings" / f"{key}.json")
        gate = entry["call"]["gate"]["command"]
        child = self.session.run_child(
            entry["descriptor"], entry["digest"], gate, answers(key)
        )
        self.status["steps"].append(
            {
                "workflowKey": key,
                "runId": child["run_id"],
                "parentWorkflowRunId": self.run_id,
                "agent": child["row"]["agent"],
                "status": "completed",
            }
        )
        self.status["workflow"]["emits"].append(
            {
                "kind": "concorde.child-terminal",
                "ticket": self.descriptor["ticket"],
                "key": key,
                "agent": child["row"]["agent"],
                "runId": child["run_id"],
                "invocation_id": child["control"]["invocation_id"],
                "proposal_digest": child["control"]["proposal_digest"],
                "metadata": child["row"]["artifactPaths"]["metadataPath"],
                "result": child["row"],
            }
        )
        self.publish()

    # pi/workflows/plan.js
    def plan(self, answers):
        self.step("bind")
        self.leaf("assessor", answers)
        advance = self.step("advance")
        if advance["state"] != "prepared":
            return
        self.leaf("planner", answers)
        self.step("finalize")

    # pi/workflows/review.js
    def review(self, answers):
        self.step("bind")
        keys = sorted(
            path.stem for path in (self.directory / "bindings").glob("review-*.json")
        )
        for key in keys:
            self.leaf(key, answers)
        self.step("finalize")

    # pi/workflows/issues.js
    def issues(self, answers):
        for iteration in range(6):
            if self.step(f"next-{iteration}")["route"] == "finished":
                return
            self.leaf(f"d-{iteration}", answers)
            decision = self.step(f"decision-{iteration}")
            if decision["route"] == "finished":
                return
            for group, count in enumerate(decision["groups"]):
                for member in range(count):
                    self.leaf(f"v-{iteration}-{group}-{member}", answers)
            if self.step(f"verified-{iteration}")["route"] == "finished":
                return
        raise AssertionError("the Issue workflow did not finish")

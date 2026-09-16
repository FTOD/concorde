"""Bounded historical-reflection probes; no model, linked worktree or production repair.

Run from the checkout: PYTHONPATH=src:. .venv/bin/python docs/reports/2026-09-16-reflection-history-probes.py
Fixture writes, including fixture Issues, stay in disposable directories. JSON goes to stdout.
These are investigation observations, not new specification obligations or lifecycle reviews.
"""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
from pathlib import Path

from concorde.development.capability_service import CapabilityHost, run_capability
from concorde.harness.change_worktree import (
    bind_owner, blocker_scope, ensure_change, read_change, record_task_gaps, save_change, workspace_context,
)
from concorde.issues.store import read_issue, report_issue
from concorde.spec.repository import SpecRepository, digest
from concorde.spec.repository_base import bound_by, expand_entry
from concorde.spec.typed_data import typed
from tests.concorde.issues.test_store import report, source
from tests.concorde.spec.support import CONFIGURATION, PACKAGE, ModelProcessDouble, project


def hidden_entries():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for name in (".github/workflows/check.yml", "source/.hidden.py", "source/visible.py"):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n")
        entries = (".github/workflows/check.yml", ".github/workflows/", ".github/",
                   "source/", "source/.hidden.py")
        result = {entry: expand_entry(root, entry) for entry in entries}
        assert result[".github/workflows/check.yml"] == [".github/workflows/check.yml"]
        assert result[".github/"] == [".github/workflows/check.yml"]
        assert result["source/"] == ["source/visible.py"]
        assert result["source/.hidden.py"] == ["source/.hidden.py"]
        assert bound_by(".github/", ".github/workflows/check.yml")
        assert not bound_by("source/", "source/.hidden.py")
        return result


def component_acceptance():
    """Inject a forbidden-to-complete acceptance; observe dispatch, not model reliability."""
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        project(root)
        observed = {}

        def callback(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"][0]["acceptance"] = (
                    "Inspect Banking's scenario.bank.settlement declaration and verify that its "
                    "consumer-side obligations agree with the transfer provider."
                )
            if stage == "specify" and snapshot["target_id"] == "service.transfer":
                paths = [item["path"] for item in snapshot["spec_resolution"]["sources"]]
                observed.update(task=snapshot["task"], spec_paths=paths,
                                consumer_spec_granted="specs/bank/module.md" in paths)
                ref = double.calls[-1]["report_issue"](report(
                    report_key="foreign-acceptance", owner_target_id=None, evidence=[],
                    title="Consumer declaration is outside the provider context",
                    description="The task requests inspection of Banking's declaration, absent here.",
                    basis="Only the transfer and its explicit references are granted.",
                    impact="Cannot perform the requested consumer verification in the provider phase.",
                ))["receipt"]
                data.update(outcome="spec_incomplete", documents=[], blockers=[
                    {**ref, "blocked_step": "Verify the consumer declaration"}])

        double = ModelProcessDouble(callback)
        host = CapabilityHost(root, PACKAGE, executor=double.executor, allow_primary_worktree=True)
        result = run_capability("concorde-dev-loop", CONFIGURATION,
            typed("concorde-dev-loop-request", {"target_id": "scope.bank", "task": "Implement transfer"}),
            host_context=host)
        observed.update(status=result["status"], outcome=result["output"]["data"]["outcome"],
                        stages=[call["stage"] for call in double.calls])
        assert "scenario.bank.settlement" in observed["task"]
        assert not observed["consumer_spec_granted"]
        assert observed["outcome"] == "spec_incomplete"
        assert "implementation" not in observed["stages"]
        return observed


def blocker_replanning():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        project(root)
        ensure_change(root, allow_primary=True)
        bind_owner(root, {"target_id": "scope.bank", "task": "Implement transfer"})
        state = read_change(root, required=True)
        state["targets"] = {"scope.bank": {"coordination": {
            "service.transfer": {"task": "First component intent", "spec_status": "pending",
                                 "implementation_status": "pending", "outcome": None}}}}
        save_change(root, state)
        ref = report_issue(root, report(owner_target_id="service.transfer", evidence=[]),
                           source(target_id="service.transfer"))
        blocker = {**ref, "blocked_step": "Assess transfer"}
        record_task_gaps(root, "service.transfer", "First component intent", "plan", [blocker], "old")
        first = read_change(root, required=True)["issue_blockers"][0]
        state = read_change(root, required=True)
        # The coordinator's accepted replacement supplies a changed label, not a new problem ID.
        state["targets"]["scope.bank"]["coordination"]["service.transfer"]["task"] = "Replanned intent"
        state["targets"]["scope.audit"] = {"coordination": {
            "service.transfer": {"task": "Equivalent nested component intent", "spec_status": "pending",
                                 "implementation_status": "pending", "outcome": None}}}
        save_change(root, state)
        scopes = [blocker_scope(state, "service.transfer", task)
                  for task in ("Replanned intent", "Equivalent nested component intent")]
        record_task_gaps(root, "service.transfer", "Equivalent nested component intent", "plan", [blocker], "old")
        assert len(read_change(root, required=True)["issue_blockers"]) == 1
        assert workspace_context(root, target_id="scope.bank")["blockers"] == []
        record_task_gaps(root, "service.transfer", "Replanned intent", "plan", [], "new")
        final = read_change(root, required=True)["issue_blockers"][0]
        result = {"accepted_scope_ids": scopes, "stable_relation": first["id"] == final["id"],
                  "relation_status": final["status"], "issue_status": read_issue(root, ref["issue_id"])[0]["status"],
                  "foreign_worker_blockers": workspace_context(root, target_id="scope.bank")["blockers"]}
        assert result["stable_relation"] and result["relation_status"] == "resolved"
        assert result["issue_status"] == "open"
        return result


def topology_recovery():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        project(root)
        task = "Clarify the Ledger title"
        ensure_change(root, allow_primary=True)
        bind_owner(root, {"target_id": "module.ledger", "task": task})

        def callback(stage, snapshot, data, cwd):
            if stage != "route" or snapshot["action"] != "design-topology":
                return
            if "module.ledger" not in [item["target_id"] for item in snapshot["targets"]]:
                data.update(outcome="expand", expand_targets=["module.ledger"])
                return
            registry = copy.deepcopy(snapshot["topology"])
            next(item for item in registry["targets"] if item["id"] == "module.ledger")["title"] = "Account ledger"
            data.update(outcome="topology_proposed", routes=[], expand_targets=[],
                topology_design=typed("concorde-topology-design", {
                    "summary": task, "registry": registry,
                    "spec_tasks": [{"target_id": "module.ledger", "task": task}],
                    "migration_constraints": [], "acceptance": ["The ledger title is clarified."]}))

        double = ModelProcessDouble(callback)

        def call(payload):
            return run_capability("concorde-main", CONFIGURATION,
                typed("concorde-main-request", payload), host_context=CapabilityHost(
                    root, PACKAGE, executor=double.executor, allow_primary_worktree=True))

        designed = call({"action": "design-topology", "task": task})
        assert designed["status"] == "succeeded", designed
        prepared = call({"action": "accept-topology", "topology_proposal": designed["output"]["data"]["topology_proposal"]})
        assert prepared["status"] == "succeeded", prepared
        before = (root / ".concorde/specs.json").read_bytes()
        applied = call({"action": "apply-topology", "application": prepared["output"]["data"]["application"]})
        state = read_change(root, required=True)
        result = {"status": applied["status"], "errors": applied["errors"],
                  "owner_retained": state["target_id"],
                  "registry_unchanged": before == (root / ".concorde/specs.json").read_bytes()}
        assert result["status"] == "blocked", applied
        assert result["errors"][0]["code"] == "incompatible_handoff"
        assert result["owner_retained"] == "module.ledger" and result["registry_unchanged"]
        return result


def review_reference():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        project(root)

        def callback(stage, snapshot, data, cwd):
            if stage != "spec-review":
                return
            ref = double.calls[-1]["report_issue"](report(
                report_key="reference-not-text", owner_target_id="service.transfer", evidence=[],
                description="Retry semantics are not specified.", basis="A repeat decision needs an explicit contract.",
                impact="A caller cannot safely retry."))["receipt"]
            data.update(status="findings", issues=[{**ref, "severity": "blocking",
                "affected_task": "Assess idempotence for repeated transfers"}])

        double = ModelProcessDouble(callback)
        result = run_capability("concorde-review", CONFIGURATION,
            typed("concorde-review-request", {"target_id": "service.transfer",
                "task": "Review retry behavior", "review_mode": "spec"}),
            host_context=CapabilityHost(root, PACKAGE, executor=double.executor))
        output = result["output"]["data"]
        assert output["outcome"] == "spec_incomplete", result
        assert output["reviews"][0]["data"]["status"] == "findings"
        assert output["blockers"][0]["blocked_step"] == "Assess idempotence for repeated transfers"
        return {"outcome": output["outcome"], "review_status": output["reviews"][0]["data"]["status"],
                "blocker_derived_from_judgment": True,
                "persisted_issue_status": read_issue(root, output["blockers"][0]["issue_id"])[0]["status"]}


def main():
    evidence = {
        "baseline": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PACKAGE, text=True).strip(),
        "method": "Deterministic current-code probes using temporary fixtures and ModelProcessDouble; no model calls.",
        "hidden_entries": hidden_entries(),
        "topology_recovery": topology_recovery(),
        "review_reference": review_reference(),
        "component_acceptance": component_acceptance(),
        "blocker_replanning": blocker_replanning(),
    }
    paths = ("src/concorde/spec/repository_base.py", "src/concorde/development/capability_host.py",
             "src/concorde/harness/change_worktree.py", "src/concorde/issues/references.py",
             "agents/task_author/spec.md", "prompts/protocol/framework-profile.md")
    evidence["source_digests"] = {path: digest((PACKAGE / path).read_bytes()) for path in paths}
    repository = SpecRepository(PACKAGE, PACKAGE)
    evidence["contract_context_digests"] = {
        owner: digest(repository.spec_context(owner).value)
        for owner in ("module.spec", "module.planning", "module.topology", "module.dev-loop")
    }
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()

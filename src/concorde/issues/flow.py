"""Issue management and bounded solving through the ordinary development providers."""
from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ..spec.repository import SpecError, SpecRepository, digest, read_file
from ..spec.typed_data import typed, canonical, checked_path
from ..spec.changes import apply_files
from .store import (MAX_RECORD_BYTES, disposition_record, dispose_issue, issue_path, list_issues,
                    parse, read_issue, render, restore_issue, validate_report)

MAX_DECISIONS = 6
DECISION_ROUTES = {
    "develop": "develop", "spec-repair": "repair_spec", "verify": "verify",
    "resolved": "close", "duplicate": "close", "not-actionable": "close",
    "needs-decision": "finish",
}
NODES = ("select_operation", "inspect", "report", "reopen", "prepare", "decide", "develop",
         "repair_spec", "verify", "close", "ready", "finish")


class IssueState(TypedDict, total=False):
    route: str
    output: dict
    result: dict | None


def build_issue_flow(node_factory):
    graph = StateGraph(IssueState)
    for name in NODES:
        graph.add_node(name, node_factory(name))
    graph.add_edge(START, "select_operation")
    graph.add_conditional_edges("select_operation", lambda state: state["route"],
                                ["inspect", "report", "reopen", "prepare", END])
    for name in ("inspect", "report", "reopen", "ready", "finish"):
        graph.add_edge(name, END)
    graph.add_conditional_edges("prepare", lambda state: state["route"], ["decide", "finish", END])
    graph.add_conditional_edges("decide", lambda state: state["route"],
                                ["develop", "repair_spec", "verify", "close", "finish", END])
    for name in ("develop", "repair_spec", "verify"):
        graph.add_conditional_edges(name, lambda state: state["route"], ["decide", "finish", END])
    graph.add_conditional_edges("close", lambda state: END if state.get("result") else "ready", ["ready", END])
    return graph.compile(name="issue_flow", checkpointer=False)


class VerificationState(TypedDict):
    index: int
    stop: bool
    output: dict | None


def build_issue_verification_flow(node_factory):
    graph = StateGraph(VerificationState)
    graph.add_node("review_item", node_factory("review_item"))
    graph.add_edge(START, "review_item")
    graph.add_conditional_edges("review_item", lambda state: END if state["stop"] else "review_item", [END, "review_item"])
    return graph.compile(name="issue_verification_flow", checkpointer=False)


def pending_disposition(change: dict | None, identifier: str) -> dict | None:
    """Validate a candidate-local write-ahead record before it can authorize any restoration."""
    solution = (change or {}).get("issue_solutions", {}).get(identifier) or {}
    if "pending_disposition" not in solution:
        return None
    journal = solution["pending_disposition"]
    try:
        if (not isinstance(journal, dict) or set(journal) != {
                "schema_version", "change_id", "issue_id", "before", "before_digest", "after", "after_digest"}
                or type(journal["schema_version"]) is not int or journal["schema_version"] != 1
                or journal["change_id"] != (change or {}).get("change_id") or journal["issue_id"] != identifier):
            raise ValueError("pending disposition identity is invalid")
        for name in ("before", "after"):
            text = journal[name]
            if (not isinstance(text, str) or len(text.encode()) > MAX_RECORD_BYTES
                    or digest(text.encode()) != journal[name + "_digest"]):
                raise ValueError("pending disposition bytes do not match their digest")
        before, after = parse(journal["before"], identifier), parse(journal["after"], identifier)
        if (before["status"] != "open" or after["status"] != "closed"
                or len(after["dispositions"]) != len(before["dispositions"]) + 1
                or {**after, "status": "open", "dispositions": after["dispositions"][:-1]} != before
                or after["dispositions"][-1]["actor"] != "concorde-issue-solver"
                or solution["revision"] != journal["before_digest"]):
            raise ValueError("pending disposition is not this solve's single closing write")
    except (ValueError, KeyError, TypeError) as error:
        raise SpecError(f"invalid pending Issue disposition: {error}", "invalid_worktree_state") from error
    return journal


def prepare_request(root: Path, package: Path, task: dict) -> dict:
    """Bind the explicit selection before workspace creation, without mutating either worktree."""
    task = dict(task)
    action = task["action"]
    repository = SpecRepository(root, package)
    task["_issue_filter"] = task.get("target_id")
    if action in {"show", "solve", "reopen"}:
        if "issue_id" not in task:
            raise SpecError("this action requires an explicit issue_id", "invalid_input")
        record, revision = read_issue(root, task["issue_id"])
        from ..harness.change_worktree import read_change
        change = read_change(root) if action == "solve" else None
        journal = pending_disposition(change, task["issue_id"])
        if journal is not None:
            versions = {journal["before_digest"], journal["after_digest"]}
            if revision not in versions or task.get("expected_revision", revision) not in versions:
                raise SpecError("Issue changed outside the pending disposition; preserve it for reconciliation", "stale_issue")
            task["_issue_recovery"] = True
            if change is None:
                raise SpecError("pending disposition requires its owning change", "invalid_worktree_state")
            for field in ("task", "constraints", "focus_id", "change_id"):
                if change.get(field) is not None:
                    task.setdefault(field, change[field])
        elif task.get("expected_revision", revision) != revision:
            raise SpecError("selected Issue has changed", "stale_issue")
        elif record["status"] == "closed" and change:
            solution = change.get("issue_solutions", {}).get(task["issue_id"]) or {}
            closing = record["dispositions"][-1]
            contexts = {item.get("context_id") for item in solution.get("history", [])}
            if (solution and solution.get("status") != "completed"
                    and closing["actor"] == "concorde-issue-solver" and contexts.intersection(closing["evidence"])):
                raise SpecError("unfinished Issue disposition has no recovery journal; reconcile it explicitly", "invalid_worktree_state")
        task["_issue_closed"] = record["status"] == "closed" and journal is None
        latest = record["reports"][-1]
        owner = latest["report"]["owner_target_id"] or latest["source"]["target_id"]
        if task.get("target_id", owner) != owner:
            raise SpecError("Issue selection cannot grant another Module's authority", "permission_denied")
        task["target_id"] = owner
        task["expected_revision"] = revision
        task.setdefault("task", f"Resolve Issue {record['id']}: {latest['report']['title']}\n"
                        f"Problem: {latest['report']['description']}\nImpact: {latest['report']['impact']}")
    elif action == "report":
        if "target_id" not in task or "report" not in task:
            raise SpecError("report requires target_id and a classified report", "invalid_input")
        validate_report(task["report"])
    for field in ("report",):
        if field in task and action != field:
            raise SpecError(f"{field} is only accepted by its own action", "invalid_input")
    if action == "reopen" and not task.get("note", "").strip():
        raise SpecError("reopen requires a rationale", "invalid_input")
    task.setdefault("target_id", repository.entry_target)
    repository.select(task["target_id"], task.get("focus_id"))
    task.setdefault("task", "Inspect project Issues")
    return task


def copy_selection(source: Path, destination: Path, task: dict) -> None:
    """Carry only the selected exact Issue into a host-created candidate, including uncommitted reports."""
    relative = issue_path(task["issue_id"])
    raw = read_file(source, relative)
    if digest(raw) != task["expected_revision"]:
        raise SpecError("Issue changed while preparing its candidate", "stale_issue")
    target = destination / relative
    before = digest(read_file(destination, relative)) if target.exists() else None
    apply_files(destination, [{"path": relative, "before_digest": before, "content": raw.decode()}], {relative})


def issue_nodes(run):
    from ..development.capability_host import Invocation, invoke_capability, _target_revision, _implementation_digest
    from ..harness.change_worktree import progress, read_change, save_change
    from .references import review_blockers

    root, task = run.repository.root, run.task
    identifier = task.get("issue_id", "")
    selected: dict = {}
    solution: dict = {}
    decision: dict = {}
    original = b""
    feedback = verification = ""
    final_outcome, final_answer, final_decision = "completed", "", None
    closed_revision = ""
    child_output: dict = {}
    duplicate_versions = {}

    def response(outcome="completed", answer="", disposition=None, records=(), **kwargs):
        result = run.response(outcome, answer, **kwargs)
        result["data"].update(issues=list(records), decision=disposition)
        return result

    def save():
        state = read_change(root, required=True)
        state.setdefault("issue_solutions", {})[identifier] = solution
        state["validated_tree"] = None
        save_change(root, state)
        # The journal rename must be durable before publishing a closing Issue file.
        descriptor = os.open(checked_path(root, ".concorde"), os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def current_inputs():
        repository = SpecRepository(root, run.host.package_root)
        target = repository.select(run.target.id)
        return digest({"spec": _target_revision(repository, target),
                       "code": _implementation_digest(repository, target)})

    def stop(outcome, answer, reason):
        nonlocal final_outcome, final_answer, final_decision
        final_outcome, final_answer, final_decision = outcome, answer, reason
        if solution:
            solution.update(status=reason, answer=answer)
            save()
        return {"route": "finish"}

    def select_operation(state):
        return {"route": {"list": "inspect", "show": "inspect", "report": "report",
                           "reopen": "reopen", "solve": "prepare"}[task["action"]]}

    def inspect(state):
        records = ([read_issue(root, identifier)[0]] if identifier else
                   [read_issue(root, row["id"])[0] for row in list_issues(root, target_id=task["_issue_filter"])])
        return {"output": response(answer="Branch-local Issues; no repair or disposition was performed.", records=records)}

    def report(state):
        from .reporting import IssueReporter
        context = run.repository.spec_context(run.target.id).value
        sources = context["sources"]
        archived = {item["path"] for item in task["report"]["evidence"]
                    if item["path"].startswith(".concorde/archive/reflections/")
                    and checked_path(root, item["path"]).is_file()}
        service = IssueReporter(root, {"invocation_id": run.host.invocation_id, "agent": "developer",
            "capability": run.capability, "phase": "report", "target_id": run.target.id,
            "context_id": digest(context), "change_id": run.change_id, "head": None},
            frozenset({run.target.id, *run.target.uses, *(item["owner"] for item in sources)}),
            frozenset({*(item["path"] for item in sources), *run.repository.implementation_files(run.target), *archived}),
            frozenset({task["report"]["issue_id"]}) if "issue_id" in task["report"] else frozenset())
        result = service(task["report"])
        return {"output": response(answer="Issue recorded without changing task execution.",
                                   records=[read_issue(root, result["receipt"]["issue_id"])[0]])}

    def reopen(state):
        dispose_issue(root, identifier, task["expected_revision"], reason="reopened", note=task["note"],
                      evidence=["Explicit developer request"], actor="developer")
        return {"output": response(answer="Issue reopened in this branch.", records=[read_issue(root, identifier)[0]])}

    def prepare(state):
        nonlocal selected, original, solution
        selected, revision = read_issue(root, identifier)
        if revision != task["expected_revision"]:
            raise SpecError("Issue changed before solving", "stale_issue")
        change = read_change(root)
        journal = pending_disposition(change, identifier)
        if journal is not None:
            if change is None:
                raise SpecError("pending disposition lost its owning change", "invalid_worktree_state")
            solution = change["issue_solutions"][identifier]
            # Invalidate any ready receipt BEFORE undoing bytes, including after a lost final ack.
            progress(root, phase="issue-recovery", status="active", invalidate=True)
            restore_issue(root, identifier, journal["before"].encode(), journal["after_digest"])
            selected, revision = read_issue(root, identifier)
            solution.pop("pending_disposition")
            solution.update(status="active", verified_inputs=None)
            solution.pop("verification", None)
            save()
        elif selected["status"] == "closed":
            return stop("completed", "Issue is already disposed in this branch; no work was replayed.", "already-closed")
        original = read_file(root, issue_path(identifier))
        change = read_change(root, required=True)
        solution = change.setdefault("issue_solutions", {}).get(identifier) or {}
        if solution and solution["revision"] != revision:
            raise SpecError("Issue changed since this solve attempt; start a fresh selected change", "stale_issue")
        inputs = current_inputs()
        if not solution:
            solution = {"revision": revision, "attempts": 0, "inputs": inputs, "intent": None,
                        "verified_inputs": None, "status": "active", "history": []}
        elif solution["inputs"] != inputs:
            solution.update(attempts=0, inputs=inputs, verified_inputs=None, status="active")
        if task.get("note") and task["note"] != solution.get("clarification"):
            solution.update(clarification=task["note"], attempts=0, verified_inputs=None, status="active")
        progress(root, phase="issue-solve", status="active", invalidate=True)
        save()
        return {"route": "decide"}

    def decide(state):
        nonlocal decision, feedback, verification, duplicate_versions
        if solution["attempts"] >= MAX_DECISIONS:
            return stop("conflicting", "Issue solving reached its bounded decision limit; progress is retained.", "limit-exhausted")
        if read_issue(root, identifier)[1] != solution["revision"]:
            raise SpecError("Issue changed during solving", "stale_issue")
        latest = selected["reports"][-1]["report"]
        candidates = []
        duplicate_versions = {}
        for row in list_issues(root, target_id=run.target.id, status="open"):
            if row["id"] != identifier and row["title"] == latest["title"] and row["type"] == latest["type"]:
                candidate, revision = read_issue(root, row["id"])
                candidates.append({"issue_id": row["id"], "revision": revision,
                                   "problem": candidate["reports"][-1]["report"]["description"]})
                duplicate_versions[row["id"]] = revision
                if len(candidates) == 5:
                    break
        selection = typed("concorde-issue-selection", {"issue_id": identifier, "revision": solution["revision"],
            "problem": latest["description"] + "\nImpact: " + latest["impact"], "type": latest["type"],
            "feedback": (("Developer clarification: " + solution["clarification"] + "\n")
                         if solution.get("clarification") else "") + feedback,
            "verification": verification, "duplicates": candidates})
        # Persist the attempt before launching: a cancelled worker cannot create an unbounded retry.
        solution["attempts"] += 1
        save()
        run.repository = SpecRepository(root, run.host.package_root)
        run.target = run.repository.select(run.target.id)
        result = run.stage("concorde-issues", inputs=(selection,))
        if result["outcome"] not in {"completed", "sufficient"}:
            return stop(result["outcome"], result["answer"], "blocked")
        decision = result.get("issue_decision") or {}
        if not decision:
            raise SpecError("Issue solver returned no decision", "invalid_completion")
        solution["history"].append({"context_id": result["context_id"], "decision": decision,
                                    "inputs": current_inputs()})
        save()
        action = decision["action"]
        if action == "needs-decision":
            return stop("conflicting", decision["rationale"], "needs-decision")
        if action == "resolved" and solution["verified_inputs"] != current_inputs():
            feedback = "Resolution requires fresh Issue-specific verification, not a workaround or a single non-reproduction."
            return {"route": "verify"}
        return {"route": DECISION_ROUTES[action]}

    def child(capability, payload, *, coordinated=True):
        child_host = replace(run.host, routed_target=run.target.id, coordinated=coordinated,
                             issue_intent=solution["intent"])
        return invoke_capability(run.capability, capability, run.configuration,
                                 typed(capability + "-request", payload), child_host)

    def base_task():
        return {"target_id": run.target.id, "task": task["task"], "constraints": task.get("constraints", []),
                "change_id": run.change_id, **({"focus_id": task["focus_id"]} if task.get("focus_id") else {})}

    def develop(state):
        nonlocal feedback, verification, child_output
        if solution["intent"] is None:
            solution["intent"] = decision["intent"]
        elif solution["intent"] != decision["intent"]:
            return stop("conflicting", "The proposed resolution changes the bound intent; a new decision is needed.", "needs-decision")
        solution["verified_inputs"] = None
        verification = ""
        save()
        result = child("concorde-dev-loop", {**base_task(), "specify": decision["specify"], "run_reviews": True})
        child_output = result.get("output") or {}
        if result["status"] == "failed" or result.get("errors"):
            return stop("failed", "Development failed; accepted Issues and partial changes are retained.", "failed")
        feedback = child_output["data"]["answer"] if child_output else "Development did not complete."
        if result["status"] == "succeeded":
            feedback = "Development and its required checks/reviews completed. Verify the selected Issue before resolving it."
        solution["inputs"] = current_inputs()
        save()
        return {"route": "decide"}

    def repair_spec(state):
        nonlocal feedback, verification
        # A fresh author receives only intended behavior, not code evidence or a previous transcript.
        intent = decision["intent"]
        previous = solution["intent"]
        solution["intent"] = intent
        result = child("concorde-specify", base_task())
        solution["intent"] = previous or intent
        solution["verified_inputs"] = None
        verification = ""
        solution["inputs"] = current_inputs()
        save()
        if result["status"] != "succeeded":
            return stop("failed" if result["status"] == "failed" else "conflicting",
                        "The authorized Spec repair could not complete; dependent work remains blocked.", "blocked")
        feedback = "The Spec author applied the intended contract repair. Resume ordinary development with fresh inputs."
        return {"route": "decide"}

    def verify(state):
        nonlocal feedback, verification, child_output
        before = current_inputs()
        modes = ("spec", "code") if run.target.files else ("spec",)
        from ..development.review import require_reviews
        require_reviews(run, True, modes=modes)
        evidence = []
        items = [(mode, True) for mode in modes] + [(mode, False) for mode in modes]

        def review_one(item):
            nonlocal child_output, feedback
            mode, specific = item
            verification_task = ("Verify that this Issue is resolved, not merely worked around. Reported problem: "
                                 + selected["reports"][-1]["report"]["description"] + "\nAdmitted goal: " + task["task"])
            payload = {**base_task(), "task": verification_task if specific else task["task"],
                       "review_mode": mode}
            result = child("concorde-review", payload)
            child_output = result.get("output") or {}
            if result["status"] != "succeeded":
                if result["status"] == "failed" or result.get("errors"):
                    return stop("failed", "Issue-specific verification failed to complete.", "failed")
                feedback = "Issue-specific verification still reports blocking Issues; repair the affected contract or code."
                solution["verified_inputs"] = None
                save()
                return {"route": "decide"}
            for reviewed in child_output["data"]["reviews"]:
                if review_blockers(reviewed["data"]["issues"]) or reviewed["data"]["status"] not in {"no_findings", "findings"}:
                    raise SpecError("incomplete Issue verification", "review_required")
                evidence.append(reviewed["data"]["input_digest"])
            return None

        def review_item(state):
            output = review_one(items[state["index"]])
            index = state["index"] + 1
            return {"index": index, "output": output, "stop": output is not None or index == len(items)}

        checked = build_issue_verification_flow(lambda name: review_item).invoke(
            {"index": 0, "stop": False, "output": None}, {"recursion_limit": len(items) + 2})
        if checked["output"] is not None:
            return checked["output"]
        if before != current_inputs():
            raise SpecError("Issue verification inputs changed", "stale_evidence")
        solution["verified_inputs"] = before
        solution["verification"] = evidence
        verification = "Independent Issue-specific verification completed for the current Spec and code: " + ", ".join(evidence)
        feedback = "Verification completed; decide the Issue's disposition from its contract and current evidence."
        save()
        return {"route": "decide"}

    def close(state):
        nonlocal closed_revision
        if digest(original) != solution["revision"]:
            raise SpecError("Issue before-image changed during selection", "stale_issue")
        reason = decision["action"]
        if reason == "resolved" and solution["verified_inputs"] != current_inputs():
            raise SpecError("resolution verification is stale", "stale_evidence")
        duplicate = decision["duplicate_of"]
        if reason == "duplicate":
            if duplicate not in duplicate_versions or read_issue(root, duplicate)[1] != duplicate_versions[duplicate]:
                raise SpecError("duplicate decision does not match an admitted current Issue", "stale_issue")
        elif duplicate is not None:
            raise SpecError("only duplicate disposition may name another Issue", "invalid_completion")
        evidence = [solution["history"][-1]["context_id"], *solution.get("verification", [])]
        prepared = disposition_record(selected, reason=reason, note=decision["rationale"], evidence=evidence,
                                      actor="concorde-issue-solver", duplicate_of=duplicate)
        after = render(prepared)
        if len(after.encode()) > MAX_RECORD_BYTES:
            raise SpecError("Issue disposition exceeds the admitted record size", "invalid_issue")
        solution["pending_disposition"] = {"schema_version": 1, "change_id": run.change_id, "issue_id": identifier,
            "before": original.decode(), "before_digest": solution["revision"],
            "after": after, "after_digest": digest(after.encode())}
        solution["status"] = "closing"
        save()  # Durable write-ahead evidence, including the exact timestamp, precedes the mutation.
        closed_revision = dispose_issue(root, identifier, solution["revision"], reason=reason,
            note=decision["rationale"], actor="concorde-issue-solver", duplicate_of=duplicate,
            duplicate_revision=duplicate_versions.get(duplicate), evidence=evidence,
            created_at=prepared["dispositions"][-1]["created_at"])
        if closed_revision != solution["pending_disposition"]["after_digest"]:
            raise SpecError("Issue disposition differs from its recovery journal", "stale_issue")
        solution["status"] = "verifying-candidate"
        save()
        return {}

    def ready(state):
        nonlocal final_outcome, final_answer, final_decision
        # Include the disposition bytes in the final checks/readiness identity, never edit after ready.
        result = child("concorde-validate", base_task(), coordinated=False)
        if result["status"] != "succeeded" or result["output"]["data"]["outcome"] != "ready":
            progress(root, status="blocked", invalidate=True)
            restore_issue(root, identifier, original, closed_revision)
            solution.pop("pending_disposition")
            solution["status"] = "verification-failed"
            save()
            return {"output": response("failed", "Final candidate verification failed; the Issue remains open.",
                                       "verification-failed", [read_issue(root, identifier)[0]])}
        # Host-local solution bookkeeping is excluded from the deliverable tree.
        change = read_change(root, required=True)
        solution.update(status="completed", disposition=decision["action"], closed_revision=closed_revision)
        solution.pop("pending_disposition")
        change["issue_solutions"][identifier] = solution
        save_change(root, change)
        return {"output": response("ready", "Issue disposed and candidate verified. Delivery remains a separate explicit request.",
            decision["action"], [read_issue(root, identifier)[0]], checks=result["output"]["data"]["checks"])}

    def finish(state):
        records = [read_issue(root, identifier)[0]] if identifier else []
        return {"output": response(final_outcome, final_answer, final_decision, records,
            blockers=child_output["data"].get("blockers", []) if child_output else [])}

    return dict(select_operation=select_operation, inspect=inspect, report=report, reopen=reopen,
                prepare=prepare, decide=decide, develop=develop, repair_spec=repair_spec, verify=verify,
                close=close, ready=ready, finish=finish)

"""Finite Issue solve services. Native workflow owns every model decision/verification branch.

The exact before/after write-ahead journal and recovery remain Host domain authority.
Instances live for one finite command; dump contains JSON, never callbacks or executors.
"""

from __future__ import annotations

import os
from dataclasses import replace

from ..harness.change_worktree import progress, read_change, save_change
from ..harness.revisions import implementation_digest, target_revision
from ..spec.repository import SpecError, SpecRepository, digest, read_file
from ..spec.typed_data import checked_path, typed
from .graph import DECISION_ROUTES, MAX_DECISIONS, pending_disposition
from .store import (
    MAX_RECORD_BYTES,
    dispose_issue,
    disposition_record,
    issue_path,
    list_issues,
    parse,
    read_issue,
    render,
    restore_issue,
)


class IssueSolve:
    def __init__(self, run, saved=None):
        self.run = run
        self.root = run.repository.root
        self.task = run.task
        self.identifier = run.task["issue_id"]
        self.selected = {}
        self.solution = {}
        self.decision = {}
        self.original = b""
        self.feedback = self.verification = self.final_answer = self.closed_revision = (
            ""
        )
        self.final_outcome = "completed"
        self.final_decision = None
        self.child_output = {}
        self.duplicate_versions = {}
        if saved:
            for key, value in saved.items():
                setattr(self, key, value.encode() if key == "original" else value)
            if self.original:
                self.selected = parse(self.original.decode(), self.identifier)

    def dump(self):
        names = (
            "selected",
            "solution",
            "decision",
            "original",
            "feedback",
            "verification",
            "final_outcome",
            "final_answer",
            "final_decision",
            "closed_revision",
            "child_output",
            "duplicate_versions",
        )
        return {
            name: (
                getattr(self, name).decode()
                if name == "original"
                else getattr(self, name)
            )
            for name in names
        }

    def response(
        self, outcome="completed", answer="", disposition=None, records=(), **kwargs
    ):
        result = self.run.response(outcome, answer, **kwargs)
        result["data"].update(issues=list(records), decision=disposition)
        return result

    def save(self):
        state = read_change(self.root, required=True)
        state.setdefault("issue_solutions", {})[self.identifier] = self.solution
        state["validated_tree"] = None
        save_change(self.root, state)
        descriptor = os.open(
            checked_path(self.root, ".concorde"), os.O_RDONLY | os.O_DIRECTORY
        )
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def current_inputs(self):
        repository = SpecRepository(self.root, self.run.host.package_root)
        target = repository.select(self.run.target.id)
        return digest(
            {
                "spec": target_revision(repository, target),
                "code": implementation_digest(repository, target),
            }
        )

    def stop(self, outcome, answer, reason):
        self.final_outcome, self.final_answer, self.final_decision = (
            outcome,
            answer,
            reason,
        )
        if self.solution:
            self.solution.update(status=reason, answer=answer)
            self.save()
        return {"route": "finish"}

    def prepare(self, state):
        self.selected, revision = read_issue(self.root, self.identifier)
        if revision != self.task["expected_revision"]:
            raise SpecError("Issue changed before solving", "stale_issue")
        change = read_change(self.root)
        journal = pending_disposition(change, self.identifier)
        if journal is not None:
            if change is None:
                raise SpecError(
                    "pending disposition lost its owning change",
                    "invalid_worktree_state",
                )
            self.solution = change["issue_solutions"][self.identifier]
            progress(
                self.root, phase="issue-recovery", status="active", invalidate=True
            )
            restore_issue(
                self.root,
                self.identifier,
                journal["before"].encode(),
                journal["after_digest"],
            )
            self.selected, revision = read_issue(self.root, self.identifier)
            self.solution.pop("pending_disposition")
            self.solution.update(status="active", verified_inputs=None)
            self.solution.pop("verification", None)
            self.save()
        elif self.selected["status"] == "closed":
            return self.stop(
                "completed",
                "Issue is already disposed in this branch; no work was replayed.",
                "already-closed",
            )
        self.original = read_file(self.root, issue_path(self.identifier))
        change = read_change(self.root, required=True)
        self.solution = (
            change.setdefault("issue_solutions", {}).get(self.identifier) or {}
        )
        if self.solution and self.solution["revision"] != revision:
            raise SpecError(
                "Issue changed since this solve attempt; start a fresh selected change",
                "stale_issue",
            )
        inputs = self.current_inputs()
        if not self.solution:
            self.solution = {
                "revision": revision,
                "attempts": 0,
                "inputs": inputs,
                "intent": None,
                "verified_inputs": None,
                "status": "active",
                "history": [],
            }
        elif self.solution["inputs"] != inputs:
            self.solution.update(
                attempts=0, inputs=inputs, verified_inputs=None, status="active"
            )
        if self.task.get("note") and self.task["note"] != self.solution.get(
            "clarification"
        ):
            self.solution.update(
                clarification=self.task["note"],
                attempts=0,
                verified_inputs=None,
                status="active",
            )
        progress(self.root, phase="issue-solve", status="active", invalidate=True)
        self.save()
        return {"route": "decide"}

    def base_task(self):
        return {
            "target_id": self.run.target.id,
            "task": self.task["task"],
            "constraints": self.task.get("constraints", []),
            "change_id": self.run.change_id,
            **(
                {"focus_id": self.task["focus_id"]} if self.task.get("focus_id") else {}
            ),
        }

    def child(self, operation, payload, *, coordinated=True):
        from ..harness.admission import invoke_operation

        child_host = replace(
            self.run.host, coordinated=coordinated, issue_intent=self.solution["intent"]
        )
        return invoke_operation(
            self.run.operation,
            operation,
            self.run.configuration,
            typed(operation + "-request", payload),
            child_host,
        )

    def close(self, state):
        if digest(self.original) != self.solution["revision"]:
            raise SpecError(
                "Issue before-image changed during selection", "stale_issue"
            )
        reason = self.decision["action"]
        if (
            reason == "resolved"
            and self.solution["verified_inputs"] != self.current_inputs()
        ):
            raise SpecError("resolution verification is stale", "stale_evidence")
        duplicate = self.decision["duplicate_of"]
        if reason == "duplicate":
            if (
                duplicate not in self.duplicate_versions
                or read_issue(self.root, duplicate)[1]
                != self.duplicate_versions[duplicate]
            ):
                raise SpecError(
                    "duplicate decision does not match an admitted current Issue",
                    "stale_issue",
                )
        elif duplicate is not None:
            raise SpecError(
                "only duplicate disposition may name another Issue",
                "invalid_completion",
            )
        evidence = [
            self.solution["history"][-1]["context_id"],
            *self.solution.get("verification", []),
        ]
        prepared = disposition_record(
            self.selected,
            reason=reason,
            note=self.decision["rationale"],
            evidence=evidence,
            actor="concorde-issue-solver",
            duplicate_of=duplicate,
        )
        after = render(prepared)
        if len(after.encode()) > MAX_RECORD_BYTES:
            raise SpecError(
                "Issue disposition exceeds the admitted record size", "invalid_issue"
            )
        self.solution["pending_disposition"] = {
            "schema_version": 1,
            "change_id": self.run.change_id,
            "issue_id": self.identifier,
            "before": self.original.decode(),
            "before_digest": self.solution["revision"],
            "after": after,
            "after_digest": digest(after.encode()),
        }
        self.solution["status"] = "closing"
        self.save()
        self.closed_revision = dispose_issue(
            self.root,
            self.identifier,
            self.solution["revision"],
            reason=reason,
            note=self.decision["rationale"],
            actor="concorde-issue-solver",
            duplicate_of=duplicate,
            duplicate_revision=self.duplicate_versions.get(duplicate),
            evidence=evidence,
            created_at=prepared["dispositions"][-1]["created_at"],
        )
        if self.closed_revision != self.solution["pending_disposition"]["after_digest"]:
            raise SpecError(
                "Issue disposition differs from its recovery journal", "stale_issue"
            )
        self.solution["status"] = "verifying-candidate"
        self.save()
        return {}

    def ready(self, state):
        result = self.child("concorde-validate", self.base_task(), coordinated=False)
        if (
            result["status"] != "succeeded"
            or result["output"]["data"]["outcome"] != "ready"
        ):
            progress(self.root, status="blocked", invalidate=True)
            restore_issue(
                self.root, self.identifier, self.original, self.closed_revision
            )
            self.solution.pop("pending_disposition")
            self.solution["status"] = "verification-failed"
            self.save()
            return {
                "output": self.response(
                    "failed",
                    "Final candidate verification failed; the Issue remains open.",
                    "verification-failed",
                    [read_issue(self.root, self.identifier)[0]],
                )
            }
        change = read_change(self.root, required=True)
        self.solution.update(
            status="completed",
            disposition=self.decision["action"],
            closed_revision=self.closed_revision,
        )
        self.solution.pop("pending_disposition")
        change["issue_solutions"][self.identifier] = self.solution
        save_change(self.root, change)
        return {
            "output": self.response(
                "ready",
                "Issue disposed and candidate verified. Delivery remains a separate explicit request.",
                self.decision["action"],
                [read_issue(self.root, self.identifier)[0]],
                checks=result["output"]["data"]["checks"],
            )
        }

    def finish(self, state):
        records = [read_issue(self.root, self.identifier)[0]] if self.identifier else []
        return {
            "output": self.response(
                self.final_outcome,
                self.final_answer,
                self.final_decision,
                records,
                blockers=self.child_output["data"].get("blockers", [])
                if self.child_output
                else [],
            )
        }

    def prepare_decision(self):
        if self.solution["attempts"] >= MAX_DECISIONS:
            return self.stop(
                "conflicting",
                "Issue solving reached its bounded decision limit; progress is retained.",
                "limit-exhausted",
            )
        if read_issue(self.root, self.identifier)[1] != self.solution["revision"]:
            raise SpecError("Issue changed during solving", "stale_issue")
        latest = self.selected["reports"][-1]["report"]
        candidates = []
        self.duplicate_versions = {}
        for row in list_issues(self.root, target_id=self.run.target.id, status="open"):
            if (
                row["id"] != self.identifier
                and row["title"] == latest["title"]
                and (row["type"] == latest["type"])
            ):
                candidate, revision = read_issue(self.root, row["id"])
                candidates.append(
                    {
                        "issue_id": row["id"],
                        "revision": revision,
                        "problem": candidate["reports"][-1]["report"]["description"],
                    }
                )
                self.duplicate_versions[row["id"]] = revision
                if len(candidates) == 5:
                    break
        selection = typed(
            "concorde-issue-selection",
            {
                "issue_id": self.identifier,
                "revision": self.solution["revision"],
                "problem": latest["description"] + "\nImpact: " + latest["impact"],
                "type": latest["type"],
                "feedback": (
                    "Developer clarification: " + self.solution["clarification"] + "\n"
                    if self.solution.get("clarification")
                    else ""
                )
                + self.feedback,
                "verification": self.verification,
                "duplicates": candidates,
            },
        )
        self.solution["attempts"] += 1
        self.save()
        self.run.repository = SpecRepository(self.root, self.run.host.package_root)
        self.run.target = self.run.repository.select(self.run.target.id)
        return {"selection": selection}

    def accept_decision(self, result):
        if result["outcome"] not in {"completed", "sufficient"}:
            return self.stop(result["outcome"], result["answer"], "blocked")
        self.decision = result.get("issue_decision") or {}
        if not self.decision:
            raise SpecError("Issue solver returned no decision", "invalid_completion")
        self.solution["history"].append(
            {
                "context_id": result["context_id"],
                "decision": self.decision,
                "inputs": self.current_inputs(),
            }
        )
        self.save()
        action = self.decision["action"]
        if action in {"develop", "spec-repair"}:
            self.solution["verified_inputs"] = None
            self.save()
            return self.stop(
                "unsupported",
                "Calling agent action required for "
                + self.run.target.id
                + ": "
                + self.decision["intent"]
                + "\n"
                + self.decision["rationale"]
                + "\nEdit the necessary Specs, paired metadata and registry directly, or select the retained planning/implementation Operations explicitly. Retry solving only with current inputs; no repair was executed.",
                action,
            )
        if action == "needs-decision":
            return self.stop(
                "conflicting", self.decision["rationale"], "needs-decision"
            )
        if (
            action == "resolved"
            and self.solution["verified_inputs"] != self.current_inputs()
        ):
            self.feedback = "Resolution requires fresh Issue-specific verification, not a workaround or a single non-reproduction."
            return {"route": "verify"}
        return {"route": DECISION_ROUTES[action]}

    def verification_requests(self):
        from ..review.review import require_reviews

        modes = ("spec", "code") if self.run.target.files else ("spec",)
        require_reviews(self.run, True, modes=modes)
        self.verification_before = self.current_inputs()
        requests = []
        for specific in (True, False):
            for mode in modes:
                task = self.base_task()
                if specific:
                    task["task"] = (
                        "Verify that this Issue is resolved, not merely worked around. Reported problem: "
                        + self.selected["reports"][-1]["report"]["description"]
                        + "\nAdmitted goal: "
                        + self.task["task"]
                    )
                requests.append((mode, task))
        return requests

    def accept_verification(self, outputs, before):
        from .references import review_blockers

        evidence = []
        for output in outputs:
            self.child_output = output
            data = output["data"]
            if data["outcome"] != "completed":
                if data["outcome"] == "failed":
                    return self.stop(
                        "failed",
                        "Issue-specific verification failed to complete.",
                        "failed",
                    )
                self.feedback = "Issue-specific verification still reports blocking Issues; repair the affected contract or code."
                self.solution["verified_inputs"] = None
                self.save()
                return {"route": "decide"}
            for reviewed in data["reviews"]:
                if review_blockers(reviewed["data"]["issues"]) or reviewed["data"][
                    "status"
                ] not in {"no_findings", "findings"}:
                    raise SpecError("incomplete Issue verification", "review_required")
                evidence.append(reviewed["data"]["input_digest"])
        if before != self.current_inputs():
            raise SpecError("Issue verification inputs changed", "stale_evidence")
        self.solution["verified_inputs"] = before
        self.solution["verification"] = evidence
        self.verification = (
            "Independent Issue-specific verification completed for the current Spec and code: "
            + ", ".join(evidence)
        )
        self.feedback = "Verification completed; decide the Issue disposition from its contract and current evidence."
        self.save()
        return {"route": "decide"}

    def assert_current(self):
        current = read_change(self.root, required=True)["issue_solutions"].get(
            self.identifier
        )
        if current != self.solution:
            raise SpecError(
                "Issue solve state changed outside this invocation", "stale_issue"
            )
        if read_issue(self.root, self.identifier)[1] != self.solution["revision"]:
            raise SpecError("selected Issue changed", "stale_issue")
        if self.current_inputs() != self.solution["inputs"]:
            raise SpecError(
                "Issue inputs changed during native solving", "stale_context"
            )

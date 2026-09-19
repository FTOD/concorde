"""Spec authoring: one Spec author's replacements, admitted after affected-consumer reviews."""

from __future__ import annotations

from ..harness.change_worktree import progress, read_change, save_change
from ..harness.revisions import target_revision
from ..review.review import review_candidate_contexts
from ..spec.changes import apply_files, file_change
from ..spec.repository import SpecError, SpecRepository, read_file
from ..spec.validation import document_context_findings, module_dependency_findings


def author(run, operation: str) -> dict:
    before_contexts = run.repository.context_identities()
    if not run.host.coordinated:
        progress(run.repository.root, phase="specify", status="active", invalidate=True)
    result = run.stage(operation, defer_gap_resolution=True)
    if result["outcome"] not in {"completed", "sufficient"}:
        return run.response(
            result["outcome"], result["answer"], blockers=result["blockers"]
        )
    if run.host.mode == "describe-policy":
        return run.response("described")
    if result["documents"]:
        if len({item["path"] for item in result["documents"]}) != len(
            result["documents"]
        ):
            raise SpecError("Spec author repeats a source member", "invalid_completion")
        if any(item["path"] not in run.target.sources for item in result["documents"]):
            raise SpecError(
                "Spec author returned a source outside its target",
                "permission_denied",
            )
        changes = [
            file_change(run.repository.root, item["path"], item["content"])
            for item in result["documents"]
            if item["content"].encode() != read_file(run.repository.root, item["path"])
        ]
        overlay = {item["path"]: item["content"].encode() for item in changes}
        candidate_repository = SpecRepository(
            run.repository.root,
            run.host.package_root,
            document_overrides=overlay,
            _defer_document_admission=True,
        )
        for path in run.target.documents:
            current_document = run.repository.document(path)
            candidate_document = candidate_repository.document(path)
            if (candidate_document.document_id, candidate_document.owner) != (
                current_document.document_id,
                current_document.owner,
            ):
                raise SpecError(
                    "document identity and ownership require a topology change",
                    "permission_denied",
                    path,
                )

        def verify():
            current = SpecRepository(run.repository.root, run.host.package_root)
            current.documents(current.select(run.target.id))
            current.contracts(current.select(run.target.id))
            document_findings = document_context_findings(current)
            if document_findings:
                raise SpecError(
                    "authored Spec document context is invalid: "
                    + "; ".join(finding.message for finding in document_findings),
                    "invalid_spec",
                )
            participant_findings = module_dependency_findings(current, run.target.id)
            if participant_findings:
                raise SpecError(
                    "authored Module dependency promises is invalid: "
                    + "; ".join(finding.message for finding in participant_findings),
                    "invalid_spec",
                )
            from ..spec.validation import definition_findings, module_findings

            source_findings = tuple(
                finding
                for finding in (
                    *module_findings(current, run.target.id),
                    *definition_findings(current, run.target.id),
                )
                if finding.severity == "error"
            )
            if source_findings:
                raise SpecError(
                    "authored Module sections, definitions or architecture are invalid: "
                    + "; ".join(f.message for f in source_findings),
                    "invalid_spec",
                )

        if changes:
            candidate = SpecRepository(
                run.repository.root,
                run.host.package_root,
                document_overrides={
                    item["path"]: item["content"].encode() for item in changes
                },
            )
            consumer_records: dict = {}
            if set(run.repository.affected_contexts(candidate)) - {run.target.id}:
                failure = review_candidate_contexts(
                    run.repository,
                    candidate,
                    run.configuration,
                    run.host,
                    run.task["task"],
                    run.task.get("constraints", []),
                    run.completed,
                    records=consumer_records,
                    change_id=run.change_id,
                    owner_id=run.target.id,
                    focus_id=run.task.get("focus_id"),
                )
                if failure is not None:
                    return run.response(
                        failure["outcome"],
                        failure["answer"],
                        blockers=failure["blockers"],
                        artifacts=failure["artifacts"],
                    )
            if (
                read_file(run.repository.root, run.repository.registry_path)
                != run.repository.registry_bytes
            ):
                raise SpecError(
                    "registry changed during canonical document review",
                    "stale_context",
                )
            apply_files(
                run.repository.root,
                changes,
                set(run.target.sources),
                verify=verify,
            )
            run.repository = SpecRepository(
                run.host.project_root, run.host.package_root
            )
            if consumer_records and run.host.mode == "execute":
                # The applied bytes equal the reviewed candidate bytes, so these reviews stay
                # revision-bound; the Spec-review stage rechecks each one before reuse.
                state = read_change(run.repository.root)
                if state is not None:
                    owner_record = consumer_records.pop(run.target.id, None)
                    intent = {
                        "task": run.task["task"],
                        "focus_id": run.task.get("focus_id"),
                        "constraints": run.task.get("constraints", []),
                    }
                    if (
                        owner_record is not None
                        and state.get("review_intents", {}).get(run.target.id) == intent
                    ):
                        state.setdefault("reviews", {}).setdefault(run.target.id, {})[
                            "spec"
                        ] = {
                            "artifact": owner_record["artifact"],
                            "input_digest": owner_record["input_digest"],
                            "status": owner_record["status"],
                            **intent,
                        }
                    shared = state.setdefault("shared_spec_reviews", {}).setdefault(
                        run.target.id, {}
                    )
                    shared.update(
                        {
                            key: {
                                "artifact": value["artifact"],
                                "task": value["task"],
                                "constraints": value["constraints"],
                            }
                            for key, value in consumer_records.items()
                        }
                    )
                    save_change(run.repository.root, state)
    run.record_gaps("specify", [])
    change = read_change(run.repository.root)
    if change is not None:
        after_contexts = run.repository.context_identities()
        affected = {
            key
            for key in before_contexts.keys() | after_contexts.keys()
            if before_contexts.get(key) != after_contexts.get(key)
        }
        impacts = change.setdefault("spec_context_impacts", {})
        impacts[run.target.id] = sorted(set(impacts.get(run.target.id, [])) | affected)
        if affected:
            change["validated_tree"] = None
            change["validation"] = None
        revision = target_revision(run.repository, run.target)
        change.setdefault("authored_specs", {})[run.target.id] = {
            "task": run.task["task"],
            "focus_id": run.task.get("focus_id"),
            "constraints": run.task.get("constraints", []),
            "context_id": run.last_context,
            "spec_digest": revision,
        }
        if run.target.id in change.get("graph", {}):
            # Keep the graph's own baseline in sync with every real (admitted) authoring, so
            # the next loop() invocation's reset check only fires for an out-of-band (human)
            # Spec edit, mirroring how implement() tracks last_implementation_digest. This
            # covers specify-loop's authoring, whether called by dev-loop or independently
            # for a target that already has a graph record from an earlier dev-loop run.
            change["graph"][run.target.id]["spec_digest"] = revision
        save_change(run.repository.root, change)
    return run.response(answer=result["answer"])

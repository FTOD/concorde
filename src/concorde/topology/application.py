"""Preparation and atomic application of an accepted topology design."""

from __future__ import annotations

import tempfile
from pathlib import Path

from ..distribution.build import load_model_instructions
from ..harness.change_worktree import (
    STATE_PATH,
    progress,
    read_change,
    refresh_registry,
)
from ..harness.configuration import load_configuration
from ..harness.context import (
    context_documents,
    materialize_documents,
    recheck_topology_author_context,
    resolve_topology_author_context,
)
from ..harness.host import (
    OperationHost,
    protocol_documents,
    run_worker,
    worker_description,
    worker_invocation,
)
from ..harness.permissions import PermissionPolicyError, PolicyBinding, compile_policy
from ..harness.worker_profile import worker_profile
from ..review.review import review_candidate_contexts
from ..spec.changes import apply_files, file_change
from ..spec.contracts import MAIN_OPERATION, TOPOLOGY_AUTHOR_NODE
from ..spec.repository import SpecError, SpecRepository, digest, read_file
from ..spec.typed_data import (
    artifact,
    canonical,
    checked_path,
    decode,
    typed,
    validate_typed,
    verify_artifacts,
)
from ..spec.validation import validate_repository
from .design import (
    inspect_topology_design,
    main_topology_response,
    validate_topology_proposal,
)


def topology_author(
    repository: SpecRepository,
    configuration: dict,
    host: OperationHost,
    target: dict,
    task: str,
    occurrence: int,
    candidate_document_references: tuple[dict, ...],
    candidate_repository: SpecRepository | None = None,
) -> dict:
    role = TOPOLOGY_AUTHOR_NODE
    prompt = load_model_instructions(host.package_root, role)
    agent = worker_profile(prompt.binding.agent)
    snapshot = resolve_topology_author_context(
        repository,
        target,
        task=task,
        instructions=prompt.body,
        candidate_document_references=candidate_document_references,
        candidate_repository=candidate_repository,
    )
    before_registry = repository.registry_bytes
    with tempfile.TemporaryDirectory(prefix="concorde-topology-author-") as directory:
        capsule = Path(directory)
        project_workspace = agent.workspace == "project"
        project = host.project_root if project_workspace else capsule
        context_file = capsule / "context.json"
        granted = context_documents(
            repository, snapshot.value, candidate_repository=candidate_repository
        )
        if host.mode != "describe-policy":
            context_file.write_text(snapshot.serialized + "\n")
            if not project_workspace:
                materialize_documents(capsule, granted)
        roles = {prompt.effects.reads[0]: ("context.json", *sorted(granted))}
        try:
            policy = compile_policy(
                prompt.effects,
                PolicyBinding(
                    MAIN_OPERATION,
                    "topology-author",
                    occurrence,
                    role,
                    role,
                    write_roles=(),
                ),
                roles,
            )
        except PermissionPolicyError as error:
            raise SpecError(str(error), "permission_denied") from error
        receipt = {
            "schema_version": 16,
            "target_id": target["id"],
            "phase": "topology-author",
            "context_id": snapshot.id,
            "source_digest": snapshot.id,
            "registry_digest": digest(before_registry),
            "role_paths": {k: list(v) for k, v in roles.items()},
        }
        runtime = typed("concorde-topology-author-context", snapshot.value)
        invocation = worker_invocation(
            configuration,
            operation=MAIN_OPERATION,
            stage="topology-author",
            prompt=prompt,
            workspace=project,
            context_value=runtime,
            receipt=receipt,
            policy=policy,
            protocol=protocol_documents(snapshot.value, granted),
        )
        host.descriptions.append(
            worker_description(
                prompt,
                invocation,
                policy,
                operation=MAIN_OPERATION,
                phase="topology-author",
                target_id=target["id"],
                context_id=snapshot.id,
                project_root=str(project),
            )
        )
        if host.mode == "describe-policy":
            return {
                "context_id": snapshot.id,
                "target_id": target["id"],
                "outcome": "completed",
                "answer": "",
                "blockers": [],
                "documents": [],
            }
        from ..harness.operation_node import OperationNode

        result = None

        def launch_author(context):
            nonlocal result
            result, data = run_worker(
                host,
                invocation,
                prompt,
                operation=MAIN_OPERATION,
                stage="topology-author",
                target_id=target["id"],
                result_type="concorde-topology-author-result",
            )
            return data

        data = OperationNode(agent.name).invoke(runtime, launch_author)
        if data["context_id"] != snapshot.id or data["target_id"] != target["id"]:
            raise SpecError(
                "topology author returned a different target/context",
                "incompatible_handoff",
            )
        if (data["outcome"] == "spec_incomplete" and not data["blockers"]) or (
            data["outcome"] == "completed" and data["blockers"]
        ):
            raise SpecError(
                "topology author blockers do not match its outcome",
                "invalid_completion",
            )
        paths = [item["path"] for item in data["documents"]]
        if data["outcome"] == "completed":
            if paths != [
                member
                for path in target["documents"]
                for member in (path, path + ".json")
            ]:
                raise SpecError(
                    "topology author must return every target document in order",
                    "invalid_completion",
                )
        elif data["documents"]:
            raise SpecError(
                "blocked topology author cannot return document replacements",
                "invalid_completion",
            )
        if read_file(repository.root, repository.registry_path) != before_registry:
            raise SpecError(
                "registry changed during topology authoring", "stale_context"
            )
        recheck_topology_author_context(
            repository, snapshot, candidate_repository=candidate_repository
        )
        if load_configuration(repository.root) != configuration:
            raise SpecError(
                "configuration changed during topology authoring",
                "configuration_mismatch",
            )
        if context_file.read_text() != snapshot.serialized + "\n":
            raise SpecError(
                "topology author changed its frozen context", "stale_context"
            )
        host.evidence.append(result)
        return data


def prepare_topology(configuration: dict, proposal: dict, host: OperationHost) -> dict:
    from .topology_graph import build_topology_graph

    author_count = len(
        proposal.get("data", {}).get("design", {}).get("data", {}).get("spec_tasks", [])
    )
    return build_topology_graph(
        topology_nodes(configuration, proposal, host).__getitem__
    ).invoke({}, {"recursion_limit": max(25, author_count + 8)})["output"]


def topology_nodes(configuration, proposal, host):
    from langgraph.graph import END

    repository = candidate_bytes = candidate_targets = candidate_repository = None
    proposals = completed = candidate_references = ordered_authors = authored = None

    def prepare_authors(state):
        nonlocal repository, proposal, candidate_bytes, candidate_targets
        nonlocal proposals, completed, candidate_references, ordered_authors
        if host.mode == "execute":
            progress(
                host.project_root,
                phase="topology_authoring",
                status="active",
                invalidate=True,
            )
        repository, proposal = validate_topology_proposal(host, proposal)
        (
            design,
            candidate,
            candidate_bytes,
            current_targets,
            candidate_targets,
            tasks,
        ) = inspect_topology_design(
            repository,
            proposal["data"]["design"],
            tuple(proposal["data"]["discovered_targets"]),
        )
        proposals = {}
        completed = ["concorde-topology-designer-design"]
        candidate_references = {}
        for candidate_target in candidate["targets"]:
            for path in candidate_target["documents"]:
                candidate_references.setdefault(path, []).append(candidate_target["id"])
                candidate_references.setdefault(path + ".json", []).append(
                    candidate_target["id"]
                )
        # Stage known provider authors before their consumers so candidate inventory additions
        # are available through explicit references. Cycles retain declared task order.
        pending_authors = dict(tasks)
        ordered_authors = []
        document_ids = repository._document_index()
        while pending_authors:

            def providers(target_id):
                assert (
                    candidate_references is not None and candidate_targets is not None
                ), "Graph node requires admitted predecessor state"
                selected = set()
                for reference in candidate_targets[target_id]["references"]:
                    if reference["kind"] == "module":
                        selected.add(reference["id"])
                    elif (
                        reference["kind"] == "document"
                        and reference["id"] in document_ids
                    ):
                        selected.update(
                            candidate_references.get(document_ids[reference["id"]], [])
                        )
                return selected

            ready = next(
                (
                    key
                    for key in pending_authors
                    if not providers(key) & pending_authors.keys()
                ),
                next(iter(pending_authors)),
            )
            ordered_authors.append((ready, pending_authors.pop(ready)))
        return {
            "occurrence": 0,
            "route": "author_module" if ordered_authors else "validate_candidate",
        }

    def author_module(state):
        assert (
            candidate_bytes is not None
            and candidate_references is not None
            and candidate_targets is not None
            and completed is not None
            and ordered_authors is not None
            and proposals is not None
            and repository is not None
        ), "Graph node requires admitted predecessor state"
        occurrence = state["occurrence"]
        target_id, task = ordered_authors[occurrence]
        target = candidate_targets[target_id]
        references = tuple(
            {"path": path, "owner": candidate_references[path][0]}
            for path in target["documents"]
        )
        author_repository = SpecRepository(
            repository.root,
            host.package_root,
            registry_bytes=candidate_bytes,
            document_overrides={
                path: items[0][1].encode() for path, items in proposals.items()
            },
            _defer_document_admission=True,
        )
        result = topology_author(
            repository,
            configuration,
            host,
            target,
            task,
            occurrence,
            references,
            candidate_repository=author_repository,
        )
        if result["outcome"] != "completed":
            return {
                "output": main_topology_response(
                    "accept-topology",
                    repository,
                    proposal,
                    outcome=result["outcome"],
                    answer=result["answer"],
                    blockers=result["blockers"],
                    completed=completed,
                ),
                "route": END,
            }
        for item in result["documents"]:
            path = item["path"]
            if (
                path not in repository.source_documents
                and checked_path(repository.root, path).exists()
            ):
                raise SpecError(
                    "topology author cannot replace an unregistered existing file",
                    "permission_denied",
                    path,
                )
            proposals.setdefault(path, []).append((target_id, item["content"]))
        completed.append("concorde-topology-author")
        occurrence += 1
        return {
            "occurrence": occurrence,
            "route": "author_module"
            if occurrence < len(ordered_authors)
            else "validate_candidate",
        }

    def validate_candidate(state):
        nonlocal authored, candidate_repository
        assert (
            candidate_bytes is not None
            and candidate_references is not None
            and completed is not None
            and proposals is not None
            and repository is not None
        ), "Graph node requires admitted predecessor state"
        if host.mode == "describe-policy":
            return {
                "output": main_topology_response(
                    "accept-topology",
                    repository,
                    proposal,
                    outcome="described",
                    answer="Topology author policies described.",
                    completed=completed,
                ),
                "route": END,
            }
        authored = {}
        for path, items in proposals.items():
            if len(items) != 1 or items[0][0] != candidate_references[path][0]:
                raise SpecError(
                    "only the unique candidate owner may propose document bytes",
                    "permission_denied",
                    path,
                )
            authored[path] = items[0][1]
        overrides = {path: content.encode() for path, content in authored.items()}
        report = validate_repository(
            repository.root,
            package_root=host.package_root,
            registry_bytes=candidate_bytes,
            document_overrides=overrides,
        )
        if report.status != "success":
            raise SpecError(
                "topology candidate validation failed: "
                + "; ".join(finding.message for finding in report.findings),
                "invalid_proposal",
            )
        candidate_repository = SpecRepository(
            repository.root,
            host.package_root,
            registry_bytes=candidate_bytes,
            document_overrides=overrides,
        )
        return {"route": "review_contexts"}

    def review_contexts(state):
        assert (
            candidate_repository is not None
            and completed is not None
            and repository is not None
        ), "Graph node requires admitted predecessor state"
        failure = review_candidate_contexts(
            repository,
            candidate_repository,
            configuration,
            host,
            proposal["data"]["task"],
            proposal["data"]["constraints"],
            completed,
        )
        if failure is not None:
            return {
                "output": main_topology_response(
                    "accept-topology",
                    repository,
                    proposal,
                    outcome=failure["outcome"],
                    answer=failure["answer"],
                    blockers=failure["blockers"],
                    completed=completed,
                ),
                "route": END,
            }
        return {"route": "persist_application"}

    def persist_application(state):
        assert (
            authored is not None
            and candidate_bytes is not None
            and completed is not None
            and repository is not None
        ), "Graph node requires admitted predecessor state"
        validate_topology_proposal(host, proposal)
        changes = [
            file_change(
                repository.root, repository.registry_path, candidate_bytes.decode()
            )
        ]
        changes.extend(
            file_change(repository.root, path, content)
            for path, content in authored.items()
        )
        application_payload = {
            "topology_proposal": proposal,
            "base_registry_digest": digest(repository.registry_bytes),
            "protocol_binding": repository.config["protocol"],
            "files": changes,
        }
        application = typed(
            "concorde-topology-application",
            {"application_id": digest(application_payload), **application_payload},
        )
        relative = (
            ".concorde/topology-proposals/"
            + application["data"]["application_id"][7:]
            + ".json"
        )
        stored = file_change(repository.root, relative, canonical(application) + "\n")
        apply_files(repository.root, [stored], {relative})
        application_ref = artifact(
            repository.root, application["data"]["application_id"], relative
        )
        completed.append("concorde-main-prepare-topology")
        return {
            "output": main_topology_response(
                "accept-topology",
                repository,
                proposal,
                outcome="topology_prepared",
                answer="Exact topology application prepared for developer review.",
                application=application_ref,
                completed=completed,
            ),
            "route": END,
        }

    nodes = {
        "prepare_authors": prepare_authors,
        "author_module": author_module,
        "validate_candidate": validate_candidate,
        "review_contexts": review_contexts,
        "persist_application": persist_application,
    }
    return nodes


def apply_topology(application_ref: dict, host: OperationHost) -> dict:
    from .topology_graph import build_topology_apply_graph

    return build_topology_apply_graph(
        topology_apply_nodes(application_ref, host).__getitem__
    ).invoke({})["output"]


def topology_apply_nodes(application_ref, host):
    from langgraph.graph import END

    repository = proposal = design = candidate_bytes = files = changed = None

    def admit_application(state):
        nonlocal repository, proposal, design, candidate_bytes, files
        if host.mode == "execute":
            progress(
                host.project_root,
                phase="topology_apply",
                status="active",
                invalidate=True,
            )
        repository = SpecRepository(host.project_root, host.package_root)
        verify_artifacts(repository.root, application_ref)
        raw = read_file(repository.root, application_ref["path"])
        application = validate_typed(
            decode(raw.decode()), "concorde-topology-application"
        )
        data = application["data"]
        identity = {key: item for key, item in data.items() if key != "application_id"}
        if (
            digest(identity) != data["application_id"]
            or application_ref["id"] != data["application_id"]
        ):
            raise SpecError(
                "topology application identity is invalid", "invalid_proposal"
            )
        expected_path = (
            ".concorde/topology-proposals/" + data["application_id"][7:] + ".json"
        )
        if application_ref["path"] != expected_path:
            raise SpecError(
                "topology application is outside the host proposal area",
                "invalid_proposal",
            )
        _, proposal = validate_topology_proposal(host, data["topology_proposal"])
        if data["base_registry_digest"] != digest(repository.registry_bytes):
            raise SpecError(
                "topology application registry base changed", "stale_proposal"
            )
        if data["protocol_binding"] != repository.config["protocol"]:
            raise SpecError(
                "topology application Protocol binding changed", "stale_proposal"
            )
        design, _, candidate_bytes, _, _, _ = inspect_topology_design(
            repository,
            proposal["data"]["design"],
            tuple(proposal["data"]["discovered_targets"]),
        )
        files = data["files"]
        registry_files = [
            item for item in files if item["path"] == repository.registry_path
        ]
        if (
            len(registry_files) != 1
            or registry_files[0]["content"].encode() != candidate_bytes
        ):
            raise SpecError(
                "topology application does not contain the exact candidate registry",
                "invalid_proposal",
            )
        task_ids = {item["target_id"] for item in design["spec_tasks"]}
        targets = {item["id"]: item for item in design["registry"]["targets"]}
        expected_documents = {
            member
            for target_id in task_ids
            for path in targets[target_id]["documents"]
            for member in (path, path + ".json")
        }
        actual_documents = {
            item["path"] for item in files if item["path"] != repository.registry_path
        }
        if actual_documents != expected_documents or len(
            {item["path"] for item in files}
        ) != len(files):
            raise SpecError(
                "topology application document set differs from accepted design",
                "invalid_proposal",
            )
        if host.mode == "describe-policy":
            return {
                "output": main_topology_response(
                    "apply-topology",
                    repository,
                    proposal,
                    outcome="described",
                    answer="Topology application is deterministic and launches no agent.",
                ),
                "route": END,
            }
        return {"route": "validate_application"}

    def validate_application(state):
        assert (
            candidate_bytes is not None and files is not None and repository is not None
        ), "Graph node requires admitted predecessor state"
        overrides = {
            item["path"]: item["content"].encode()
            for item in files
            if item["path"] != repository.registry_path
        }
        report = validate_repository(
            repository.root,
            package_root=host.package_root,
            registry_bytes=candidate_bytes,
            document_overrides=overrides,
        )
        if report.status != "success":
            raise SpecError(
                "topology application validation failed: "
                + "; ".join(finding.message for finding in report.findings),
                "invalid_proposal",
            )
        return {}

    def apply_atomically(state):
        nonlocal changed
        assert (
            candidate_bytes is not None
            and design is not None
            and files is not None
            and proposal is not None
            and repository is not None
        ), "Graph node requires admitted predecessor state"
        allowed = {item["path"] for item in files}

        def verify():
            assert repository is not None, (
                "Graph node requires admitted predecessor state"
            )
            current = validate_repository(
                repository.root, package_root=host.package_root
            )
            if current.status != "success":
                raise SpecError(
                    "applied topology failed validation: "
                    + "; ".join(finding.message for finding in current.findings),
                    "invalid_proposal",
                )

        change = read_change(repository.root)
        transaction = list(files)
        if change is not None:
            owner = design["registry"]["entry_target"]
            if change["target_id"] is not None and (
                change["target_id"] != owner
                or change["task"] != proposal["data"]["task"]
                or change["constraints"] != proposal["data"]["constraints"]
            ):
                raise SpecError(
                    "topology application differs from this worktree's owning task",
                    "incompatible_handoff",
                )
            change.update(
                target_id=owner,
                focus_id=None,
                task=proposal["data"]["task"],
                constraints=proposal["data"]["constraints"],
                phase="specified",
                status="active",
                outcome="topology_applied",
                blockers=[],
            )
            candidate_repository = SpecRepository(
                repository.root,
                host.package_root,
                registry_bytes=candidate_bytes,
                document_overrides={
                    item["path"]: item["content"].encode()
                    for item in files
                    if item["path"] != repository.registry_path
                },
            )
            impacts = change.setdefault("spec_context_impacts", {})
            impacts[owner] = sorted(
                set(impacts.get(owner, []))
                | set(repository.affected_contexts(candidate_repository))
            )
            change["validated_tree"] = None
            change["validation"] = None
            transaction.append(
                file_change(repository.root, STATE_PATH, canonical(change) + "\n")
            )
            allowed.add(STATE_PATH)
        changed = [
            path
            for path in apply_files(
                repository.root, transaction, allowed, verify=verify
            )
            if path != STATE_PATH
        ]
        if change is not None:
            refresh_registry(repository.root)
        return {}

    def cleanup(state):
        assert (
            changed is not None and proposal is not None and repository is not None
        ), "Graph node requires admitted predecessor state"
        try:
            checked_path(repository.root, application_ref["path"]).unlink()
            proposal_dir = checked_path(repository.root, ".concorde/topology-proposals")
            if proposal_dir.is_dir() and not any(proposal_dir.iterdir()):
                proposal_dir.rmdir()
        except OSError:
            # The application is already committed; stale host artifacts remain ignored and digest-bound.
            pass
        return {
            "output": main_topology_response(
                "apply-topology",
                SpecRepository(repository.root, host.package_root),
                proposal,
                outcome="topology_applied",
                answer="Accepted topology application applied atomically.",
                files=changed,
                completed=("concorde-main-apply-topology",),
            ),
            "route": END,
        }

    nodes = {
        "admit_application": admit_application,
        "validate_application": validate_application,
        "apply_atomically": apply_atomically,
        "cleanup": cleanup,
    }
    return nodes

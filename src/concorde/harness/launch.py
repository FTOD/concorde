"""One bounded worker launch: the safety sequence every model-backed stage shares.

Whichever provider asks for a worker, the launch is the same. The frozen context index is
written where the worker will find it, beside byte-identical copies of the granted documents
in a capsule or in place in a project workspace; the grant is compiled from the worker's
declared effects and this invocation's role paths; the launch is bound to its instructions,
receipt and model selection and recorded for policy preview; exactly one matching result is
admitted; and the registry, the frozen context, the project configuration and the index are
rechecked before that result counts. A provider supplies only what differs: the context it
froze, the value its worker receives, how the result is judged and what a preview answers.
"""

from __future__ import annotations

import tempfile
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..spec.repository import SpecError, SpecRepository, digest, read_file
from ..spec.typed_data import checked_path
from .checks import check_service
from .configuration import load_configuration
from .context import materialize_documents, materialize_references, reference_grants
from .host import (
    OperationHost,
    protocol_documents,
    run_worker,
    worker_description,
    worker_invocation,
)
from .permissions import PermissionPolicyError, PolicyBinding, compile_policy
from .worker_executor import WorkerOutcome
from .worker_profile import context_role, worker_profile


@dataclass(frozen=True)
class WorkerLaunch:
    """What one launch needs beyond the common sequence.

    ``snapshot`` is the frozen context record (its ``id``, ``value`` and ``serialized`` form),
    ``granted`` the documents it lists with their verified bytes, ``value`` the typed stage
    context the worker receives and ``index`` the text the worker finds at ``context.json``.
    ``receipt`` and ``labels`` add the kind-specific fields of the launch receipt and of its
    policy description. ``validate`` judges the admitted result and ``recheck`` proves the
    frozen context is still current; both raise on failure. ``described`` is what a policy
    preview returns instead of launching. ``implementation`` grants the selected Module's
    files to a project-workspace worker, writable only when ``writable``; ``target`` is that
    Module's descriptor, whose configured checks such a worker may run. ``admitted`` receives
    the executor's outcome as soon as it is accepted, before the result is judged, so a caller
    that records failures can keep the outcome of a launch whose result was then rejected.
    """

    operation: str
    stage: str
    role: str
    snapshot: Any
    granted: dict[str, bytes]
    value: dict
    index: str
    result_type: str
    receipt: dict
    described: Any
    validate: Callable[[dict], None]
    recheck: Callable[[], None]
    occurrence: int = 0
    target: Any = None
    target_id: str | None = None
    change_id: str | None = None
    implementation: tuple[str, ...] | None = None
    writable: bool = False
    labels: dict = field(default_factory=dict)
    admitted: Callable[[WorkerOutcome], None] | None = None
    prefix: str = "concorde-context-"


def launch_worker(
    host: OperationHost,
    configuration: dict,
    repository: SpecRepository,
    prompt,
    launch: WorkerLaunch,
) -> Any:
    """Run one bound worker through the common launch sequence and return its admitted result.

    In ``describe-policy`` mode the grant is compiled and recorded but nothing is launched, and
    ``launch.described`` is returned instead. ``repository`` may carry a candidate overlay; the
    registry guard compares the project's registry file before and after the launch.
    """
    agent = worker_profile(prompt.binding.agent)
    snapshot = launch.snapshot
    preview = host.mode == "describe-policy"
    before_registry = read_file(repository.root, repository.registry_path)
    with tempfile.TemporaryDirectory(prefix=launch.prefix) as directory:
        capsule = Path(directory)
        # A Spec-only worker sees a private capsule, not the repository or an inherited conversation.
        project_workspace = agent.workspace == "project"
        project = host.project_root if project_workspace else capsule
        if project_workspace:
            relative = (
                f".concorde/work/{host.invocation_id}/{uuid.uuid4()}/context.json"
            )
            context_file = checked_path(project, relative)
        else:
            relative, context_file = "context.json", capsule / "context.json"
        if not preview:
            context_file.parent.mkdir(parents=True, exist_ok=True)
            context_file.write_text(launch.index)
            # The index is written beside byte-identical copies of every document it lists; the
            # worker opens them on demand instead of receiving their bodies in its input.
            if not project_workspace:
                materialize_documents(capsule, launch.granted)
        roles: dict[str, tuple[str, ...]] = {
            context_role(agent): (relative, *sorted(launch.granted))
        }
        if launch.implementation is not None:
            roles["implementation"] = tuple(launch.implementation)
        if "references" in prompt.effects.reads:
            # Resource context: the Module's external references, read-only. A capsule receives
            # byte-identical copies of their readable files at the same paths.
            records = snapshot.value["external_references"]
            if not project_workspace and not preview:
                materialize_references(repository, capsule, records)
            roles["references"] = reference_grants(records)
        write_roles = ("implementation",) if launch.writable else ()
        try:
            policy = compile_policy(
                prompt.effects,
                PolicyBinding(
                    launch.operation,
                    launch.stage,
                    launch.occurrence,
                    launch.role,
                    launch.role,
                    write_roles=write_roles,
                ),
                roles,
            )
        except PermissionPolicyError as error:
            raise SpecError(str(error), "permission_denied") from error
        if not write_roles and policy.write_paths:
            raise SpecError(
                f"{launch.stage} worker must have no write authority",
                "permission_denied",
            )
        receipt = {
            "schema_version": 16,
            "phase": launch.stage,
            "context_id": snapshot.id,
            "source_digest": snapshot.id,
            "registry_digest": digest(before_registry),
            "role_paths": {key: list(paths) for key, paths in roles.items()},
            **launch.receipt,
        }
        invocation = worker_invocation(
            configuration,
            operation=launch.operation,
            stage=launch.stage,
            prompt=prompt,
            workspace=project,
            context_value=launch.value,
            receipt=receipt,
            policy=policy,
            protocol=protocol_documents(snapshot.value, launch.granted),
        )
        host.descriptions.append(
            worker_description(
                prompt,
                invocation,
                policy,
                operation=launch.operation,
                phase=launch.stage,
                context_id=snapshot.id,
                project_root=str(project),
                **launch.labels,
            )
        )
        if preview:
            return launch.described
        from .operation_node import OperationNode

        checks = (
            check_service(repository, launch.target, host.invocation_id)
            if project_workspace and launch.target is not None
            else None
        )
        result: WorkerOutcome | None = None

        def run(context):
            # The OperationNode's typed state carries the admitted context in and the validated
            # result out; the Pi worker launch and its admission checks stay host-private.
            nonlocal result
            result, data = run_worker(
                host,
                invocation,
                prompt,
                operation=launch.operation,
                stage=launch.stage,
                target_id=launch.target_id,
                result_type=launch.result_type,
                change_id=launch.change_id,
                checks=checks,
            )
            if launch.admitted is not None:
                launch.admitted(result)
            return data

        data = OperationNode(agent.name).invoke(launch.value, run)
        if result is None:
            raise SpecError(
                "worker returned without an execution result", "invalid_completion"
            )
        launch.validate(data)
        if read_file(repository.root, repository.registry_path) != before_registry:
            raise SpecError(f"registry changed during {launch.stage}", "stale_context")
        launch.recheck()
        if load_configuration(repository.root) != configuration:
            raise SpecError(
                f"configuration changed during {launch.stage}", "configuration_mismatch"
            )
        if context_file.read_text() != launch.index:
            raise SpecError(
                "frozen context index changed during the launch", "stale_context"
            )
        host.evidence.append(result)
        return data

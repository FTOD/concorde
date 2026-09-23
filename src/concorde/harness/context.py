"""Task context: the frozen context snapshot of one Agent call and its recheck.

A snapshot records the four context kinds of one call as Spec tooling computes them, with byte
digests: the Spec context of every bound Module, the Protocol files, the selected Module's
implementation names (and contents when the Agent definition reads implementation), its external
context, the Agent binding, the task and the admitted stage inputs, and the workspace facts. What the
bound Agent definition says decides the phase, the admitted stage inputs, whether implementation
contents are recorded and whether the call is bound to the Modules sharing its files.
"""

from __future__ import annotations

from .timing import timed

from dataclasses import dataclass
from pathlib import Path

from ..spec.repository import (
    SpecError,
    SpecRepository,
    digest,
    most_specific,
    read_file,
    is_directory_entry,
)
from ..spec.content_repository import LISTING_ENTRY, context_record_schema
from ..spec.typed_data import (
    ARTIFACT,
    DIGEST,
    PATH,
    STRING,
    array,
    canonical,
    obj,
    register,
    typed_schema,
    validate_typed,
)
from .status_store import WORKSPACE_CONTEXT
from .worker_profile import (
    AgentBinding,
    agent_definition,
    bind_agent,
    phase_agent,
    validate_stage_inputs,
)

RepositoryCore = SpecRepository

SNAPSHOT_VERSION = 8
# The Protocol copy the installer places in the project and the configuration binds.
PROTOCOL_PATHS = (
    ".concorde/protocol/principles.md",
    ".concorde/protocol/kinds/module.md",
)

NULLABLE_ID = {"anyOf": [STRING, {"type": "null"}]}
# A stage input is a typed value of a type its owner registered; the bound definition decides
# which types a snapshot admits, and freezing validates each against its registration.
STAGE_INPUT = obj(
    {
        "type_id": STRING,
        "schema_version": {"type": "integer", "minimum": 1},
        "data": {"type": "object", "additionalProperties": {}},
    }
)
IMPLEMENTATION_ENTRY = obj(
    {
        "path": LISTING_ENTRY,
        "entity_id": NULLABLE_ID,
        "pending": {"type": "boolean"},
        "directory": {"type": "boolean"},
    }
)
IMPLEMENTATION_FILE = obj(
    {"path": PATH, "entity_id": NULLABLE_ID, "pending": {"type": "boolean"}}
)
EXTERNAL_REFERENCE = obj(
    {"path": LISTING_ENTRY, "directory": {"type": "boolean"}, "digest": DIGEST}
)
AGENT_BINDING = obj(
    {
        "agent": STRING,
        "spec_path": PATH,
        "spec_digest": DIGEST,
        "instructions_path": PATH,
        "instructions_digest": DIGEST,
        "definition_digest": DIGEST,
        "build_manifest_digest": DIGEST,
        "tools": array(STRING, unique=True),
        "effects": obj(
            {
                "reads": array(STRING, unique=True),
                "writes": array(STRING, unique=True),
                "network": {"type": "boolean"},
                "credentials": STRING,
            }
        ),
        "workspace": {"enum": ["capsule", "project"]},
        "timeout_seconds": {"type": "integer", "minimum": 1},
        "digest": DIGEST,
    }
)
SHARED_BINDING = obj(
    {
        "module_id": STRING,
        "files": array(LISTING_ENTRY, unique=True),
        "spec_resolution": context_record_schema(),
    }
)
CONTEXT_SNAPSHOT = obj(
    {
        "context_id": DIGEST,
        "schema_version": {"const": SNAPSHOT_VERSION},
        "target_id": STRING,
        "kind": {"const": "module"},
        "focus_id": NULLABLE_ID,
        "phase": STRING,
        "task": STRING,
        "constraints": array(STRING),
        "agent_binding": AGENT_BINDING,
        "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
        "protocol": array(obj({"path": PATH, "digest": DIGEST})),
        "spec_resolution": context_record_schema(),
        "shared_bindings": array(SHARED_BINDING),
        "implementation_entries": array(IMPLEMENTATION_ENTRY),
        "implementation_files": array(IMPLEMENTATION_FILE),
        "implementation_artifacts": array(ARTIFACT),
        # The Module's external inclusions, one tree digest per entry.
        "external_references": array(EXTERNAL_REFERENCE),
        "stage_inputs": array(STAGE_INPUT),
        "workspace": WORKSPACE_CONTEXT,
    }
)
AGENT_STAGE_CONTEXT = obj(
    {
        "snapshot": typed_schema("concorde-context-snapshot"),
        "change_id": NULLABLE_ID,
        "expected_artifacts": array(PATH),
    }
)

register("concorde-context-snapshot", SNAPSHOT_VERSION, CONTEXT_SNAPSHOT)
register("concorde-agent-stage-context", 5, AGENT_STAGE_CONTEXT)


@dataclass(frozen=True)
class ContextSnapshot:
    serialized: str

    @property
    def value(self) -> dict:
        from ..spec.typed_data import decode

        return decode(self.serialized)

    @property
    def id(self) -> str:
        return self.value["context_id"]


def _protocol(repository: RepositoryCore) -> list[dict]:
    protocol = []
    for path in PROTOCOL_PATHS:
        raw = repository.protocol_assets[path]
        protocol.append({"path": path, "digest": digest(raw)})
    return protocol


def _implementation_entries(repository: SpecRepository, target) -> list[dict]:
    """The Module's realization entries (its ImplementationScope); declarations only, never contents.

    ``entity_id`` names the realization that lists the entry.
    """
    realizations = repository.realization_entries(target)
    result = []
    for entry in target.files:
        realization = realizations.get(entry)
        result.append(
            {
                "path": entry,
                "entity_id": realization.id if realization else None,
                "pending": bool(realization and entry in realization.pending),
                "directory": is_directory_entry(entry),
            }
        )
    return result


def _implementation_files(repository: SpecRepository, target) -> list[dict]:
    """The Module's ImplementationContext: names of existing bound files plus pending exact entries."""
    realizations = repository.realization_entries(target)
    names: list[dict] = []
    for path in repository.implementation_context(target):
        entry = most_specific(realizations, path)
        realization = realizations[entry] if entry else None
        names.append(
            {
                "path": path,
                "entity_id": realization.id if realization else None,
                "pending": bool(
                    realization
                    and path in realization.pending
                    and not (repository.root / path).is_file()
                ),
            }
        )
    return names


def _implementation_artifacts(repository: SpecRepository, target) -> list[dict]:
    return [
        {"id": path, "path": path, "digest": digest(read_file(repository.root, path))}
        for path in repository.bound_files(target)
    ]


def _external_references(repository: SpecRepository, target) -> list[dict]:
    """The Module's ExternalContext with one tree digest per entry; bytes are granted, never embedded."""
    entries = repository.external_context(target)
    missing = [entry.path for entry in entries if not entry.exists]
    if missing:
        raise SpecError(
            f"external reference is not checked out: {', '.join(missing)}",
            "invalid_reference",
            target.id,
        )
    return [entry.record() for entry in entries]


def _shared_bindings(repository: SpecRepository, target) -> list[dict]:
    """Every other Module binding a file of the selected Module's scope, with its Spec context."""
    return [
        {
            "module_id": module_id,
            "files": list(files),
            "spec_resolution": repository.spec_context(module_id).value,
        }
        for module_id, files in sorted(repository.shared_files(target).items())
    ]


def context_sources(value: dict) -> list[dict]:
    """The Spec document source records of every Module a snapshot is bound to."""
    return [
        *value["spec_resolution"]["sources"],
        *(
            source
            for shared in value["shared_bindings"]
            for source in shared["spec_resolution"]["sources"]
        ),
    ]


def context_documents(repository: RepositoryCore, value: dict) -> dict[str, bytes]:
    """The exact bytes of every Protocol and Spec context file a snapshot delivers, by path.

    Each file is verified against the digest the snapshot recorded; a changed one is
    ``stale_context``.
    """
    repository.validate_source_records(value["spec_resolution"]["sources"])
    for shared in value["shared_bindings"]:
        repository.validate_source_records(shared["spec_resolution"]["sources"])
    expected = {
        item["path"]: item["digest"]
        for item in (*value["protocol"], *context_sources(value))
    }
    result: dict[str, bytes] = {}
    for path, expected_digest in expected.items():
        raw = (
            repository.protocol_assets[path]
            if path in repository.protocol_assets
            else repository.source_bytes(path)
        )
        if digest(raw) != expected_digest:
            raise SpecError(f"granted context file changed: {path}", "stale_context")
        result[path] = raw
    return result


def _binding(repository: SpecRepository, agent, phase: str | None) -> AgentBinding:
    if isinstance(agent, AgentBinding):
        return agent
    if agent is None:
        name = phase_agent(phase).name if phase else "context_assessor"
    else:
        name = agent
    return bind_agent(repository.package_root, name)


@timed("context.resolve")
def resolve_context(
    repository: SpecRepository,
    target_id: str,
    *,
    agent: str | AgentBinding | None = None,
    phase: str | None = None,
    task: str = "Understand this Spec",
    focus_id: str | None = None,
    constraints: tuple[str, ...] = (),
    stage_inputs: tuple[dict, ...] = (),
    workspace: dict | None = None,
    require_inputs: bool = False,
) -> ContextSnapshot:
    """Freeze the context snapshot of one Agent call.

    ``agent`` names the Agent (or is its binding); without it the Agent whose definition names
    ``phase`` is bound. A given ``phase`` must be the bound definition's. ``require_inputs`` also
    requires every stage input the definition requires; a policy preview omits it.
    """
    if phase is not None and phase not in {d for d in _phases()}:
        raise SpecError("unsupported context phase", "invalid_phase")
    binding = _binding(repository, agent, phase)
    definition = agent_definition(binding.agent)
    if phase is not None and phase != definition.phase:
        raise SpecError(
            "the phase is not the bound Agent definition's phase", "invalid_phase"
        )
    if not isinstance(task, str) or not task.strip():
        raise SpecError("task intent is required", "invalid_input")
    validate_stage_inputs(definition, stage_inputs, require_all=require_inputs)
    for item in stage_inputs:
        validate_typed(item, item["type_id"])
    target = repository.module(target_id, focus_id)
    resolution = repository.spec_context(focus_id or target.id).value
    from .change_worktree import workspace_context

    manifest = {
        "schema_version": SNAPSHOT_VERSION,
        "target_id": target.id,
        "kind": target.kind,
        "focus_id": focus_id,
        "phase": definition.phase,
        "task": task,
        "constraints": list(constraints),
        "agent_binding": binding.record(),
        "protocol_binding": repository.config["protocol"],
        "protocol": _protocol(repository),
        "spec_resolution": resolution,
        "shared_bindings": _shared_bindings(repository, target)
        if definition.writes_implementation
        else [],
        "implementation_entries": _implementation_entries(repository, target),
        "implementation_files": _implementation_files(repository, target),
        "implementation_artifacts": _implementation_artifacts(repository, target)
        if definition.reads_implementation
        else [],
        "external_references": _external_references(repository, target),
        "stage_inputs": list(stage_inputs),
        "workspace": workspace
        if workspace is not None
        else workspace_context(repository.root),
    }
    return ContextSnapshot(canonical({**manifest, "context_id": digest(manifest)}))


def _phases() -> frozenset[str]:
    from .worker_profile import phases

    return phases()


def _stale_on_resolution_error(check):
    """A formerly admitted selection becoming invalid is stale evidence, never a new grant."""
    from functools import wraps

    @wraps(check)
    def checked(*args, **kwargs):
        try:
            return check(*args, **kwargs)
        except SpecError as error:
            if error.code == "stale_context":
                raise
            raise SpecError(
                f"admitted context selection changed: {error}", "stale_context"
            ) from error
        except (ValueError, OSError) as error:
            raise SpecError(
                f"admitted context selection changed: {error}", "stale_context"
            ) from error

    return checked


def writes_implementation(value: dict) -> bool:
    """Whether a snapshot's bound Agent writes implementation."""
    return "implementation" in value["agent_binding"]["effects"]["writes"]


@_stale_on_resolution_error
@timed("context.recheck")
def recheck_context(repository: SpecRepository, snapshot: ContextSnapshot) -> None:
    """Fail with ``stale_context`` when any rechecked input differs from the snapshot.

    For an Agent that writes implementation, its own bound file names and bytes are exempt,
    because changing them is the purpose of the call.
    """
    value = snapshot.value
    declared = value.pop("context_id")
    if digest(value) != declared:
        raise SpecError("context snapshot identity has changed", "stale_context")
    _recheck_workspace(repository.root, value["workspace"])
    current = SpecRepository(
        repository.root,
        repository.package_root,
        registry_bytes=repository.registry_bytes
        if repository.document_overrides
        else None,
        document_overrides=repository.document_overrides,
    )
    target = current.module(value["target_id"], value["focus_id"])
    if current.config["protocol"] != value["protocol_binding"]:
        raise SpecError("context Protocol binding has changed", "stale_context")
    if (
        current.spec_context(value["focus_id"] or target.id).value
        != value["spec_resolution"]
    ):
        raise SpecError(
            "context ownership, references, provenance or bytes changed",
            "stale_context",
        )
    writer = writes_implementation(value)
    if (_shared_bindings(current, target) if writer else []) != value[
        "shared_bindings"
    ]:
        raise SpecError("the Modules sharing the files changed", "stale_context")
    if _implementation_entries(current, target) != value["implementation_entries"]:
        raise SpecError(
            "listed implementation entries or their entities changed", "stale_context"
        )
    if not writer:
        if _implementation_files(current, target) != value["implementation_files"]:
            raise SpecError("implementation file names changed", "stale_context")
        if (
            "implementation" in value["agent_binding"]["effects"]["reads"]
            and _implementation_artifacts(current, target)
            != value["implementation_artifacts"]
        ):
            raise SpecError(
                "implementation input membership or bytes changed", "stale_context"
            )
    if _external_references(current, target) != value["external_references"]:
        raise SpecError("external references or their bytes changed", "stale_context")
    binding = value["agent_binding"]
    if bind_agent(repository.package_root, binding["agent"]).record() != binding:
        raise SpecError("the Agent binding changed", "stale_context")


def _recheck_workspace(root: Path, observed: dict) -> None:
    from .change_worktree import workspace_context

    current = workspace_context(root)
    # Other worktrees may advance while this stage runs. Their inventory is an
    # explicitly timestamp-free observation, never an authority grant. This
    # invocation's own identity and lifecycle boundary must remain unchanged.
    for key in observed.keys() - {"active_worktrees"}:
        if current[key] != observed[key]:
            raise SpecError(
                "current worktree identity or lifecycle changed", "stale_context"
            )

"""Versioned capability transport and native Agent contracts.

Legacy operation_* identifiers and concorde-* names remain wire compatibility spellings, not a
claim that native capabilities execute as LangGraph. KIND declares actual executable semantics.
"""

from __future__ import annotations

from .contract_shapes import (
    ARTIFACT,
    BLOCKER,
    DIGEST,
    NULLABLE_ID,
    PATH,
    STRING,
    WORKSPACE_CONTEXT,
    array,
    obj,
    typed_schema,
)
from .issue_shapes import RECEIPT as ISSUE_RECEIPT
from .issue_shapes import REPORT as ISSUE_REPORT
from .issue_shapes import REVIEW_ISSUE

DOCUMENT_CHANGE = obj({"path": PATH, "content": {"type": "string"}})
TASK_ITEM = obj(
    {
        "id": STRING,
        "target_id": STRING,
        "description": STRING,
        "acceptance": STRING,
        "complete": {"type": "boolean"},
    }
)
WORKER_OUTCOMES = {
    "enum": ["completed", "spec_incomplete", "unsupported", "conflicting", "failed"]
}
CHECK = obj(
    {
        "id": STRING,
        "target_id": STRING,
        "argv": {**array(STRING), "minItems": 1},
        "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
        "inputs": array(PATH, unique=True),
    },
    ("inputs",),
)
LISTING_ENTRY = {**STRING, "pattern": r"^[^/](?:[^/]*/)*[^/]*$"}
REFERENCE = {
    "anyOf": [
        obj({"kind": {"enum": ["module", "document"]}, "id": STRING}),
        obj({"kind": {"const": "external"}, "path": LISTING_ENTRY}),
    ]
}
EXTERNAL_REFERENCE = obj(
    {"path": LISTING_ENTRY, "directory": {"type": "boolean"}, "digest": DIGEST}
)
TARGET_DESCRIPTOR = obj(
    {
        "id": STRING,
        "kind": {"const": "module"},
        "title": STRING,
        "documents": {**array(PATH, unique=True), "minItems": 1},
        "references": array(REFERENCE, unique=True),
        "parent": NULLABLE_ID,
        "uses": array(STRING, unique=True),
        "files": array(LISTING_ENTRY, unique=True),
        "checks": array(STRING, unique=True),
    }
)
IMPLEMENTATION_FILE = obj(
    {"path": PATH, "entity_id": NULLABLE_ID, "pending": {"type": "boolean"}}
)
IMPLEMENTATION_ENTRY = obj(
    {
        "path": LISTING_ENTRY,
        "entity_id": NULLABLE_ID,
        "pending": {"type": "boolean"},
        "directory": {"type": "boolean"},
    }
)
REGISTRY = obj(
    {
        "schema_version": {"const": 5},
        "project_id": STRING,
        "entry_target": STRING,
        "targets": {**array(TARGET_DESCRIPTOR), "minItems": 1},
        "checks": array(CHECK),
    }
)
PROPOSAL_FILE = obj(
    {
        "path": PATH,
        "before_digest": {"anyOf": [DIGEST, {"type": "null"}]},
        "content": {"type": "string"},
    }
)


def load_operation_inventory():
    """Import the repository-root ``operations`` package normally.

    ``tests/concorde`` holds one flat package per Module and none of them is named
    ``operations``, so test collection (``pytest`` over ``tests/concorde``, imported as the
    ``tests.concorde.*`` packages) no longer risks registering an unrelated test package under
    the plain ``operations`` name. A plain import is therefore safe here.
    """

    import sys
    from pathlib import Path

    package_root = Path(__file__).resolve().parents[3]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    import operations

    return operations


# Each bound operation stage runs the one worker whose contract names that phase.
MODEL_STAGES = {
    "concorde-plan": ("plan", "concorde-planner"),
    "concorde-tasks": ("tasks", "concorde-task-author"),
    "concorde-implement": ("implementation", "concorde-programmer"),
    "concorde-context-solve": ("context-solve", "concorde-context-assessor"),
    "concorde-issues": ("issue-solve", "concorde-issue-solver"),
}
# The two public operations fix the review kind; callers cannot select it in task data.
REVIEW_OPERATIONS = {
    "concorde-spec-review": "spec",
    "concorde-code-review": "code",
}
REVIEW_STAGES = {
    "spec": ("spec-review", "concorde-spec-reviewer"),
    "code": ("code-review", "concorde-code-reviewer"),
}


def operation_modules() -> dict:
    """Compatibility wire lookup combines adapters and canonical domain roles, not ownership."""
    import importlib

    inventory = load_operation_inventory()
    import agents

    assert not set(inventory.OPERATIONS).intersection(agents.DOMAIN_AGENTS), (
        "capability and Agent identities must be disjoint"
    )
    return {
        **{
            inventory.external_name(name): importlib.import_module(
                f"{inventory.__name__}.{name}"
            )
            for name in inventory.OPERATIONS
        },
        **{
            agents.external_name(name): importlib.import_module(f"agents.{name}")
            for name in agents.DOMAIN_AGENTS
        },
    }


_MODULES = operation_modules()
OPERATION_NAMES = tuple(sorted(_MODULES))
PUBLIC_OPERATIONS = tuple(name for name in OPERATION_NAMES if _MODULES[name].PUBLIC)
INTERNAL_OPERATIONS = tuple(
    name for name in OPERATION_NAMES if not _MODULES[name].PUBLIC
)
DETERMINISTIC_OPERATIONS = frozenset(
    name for name in OPERATION_NAMES if _MODULES[name].DETERMINISTIC
)
COMPOSITE_OPERATIONS = tuple(name for name in OPERATION_NAMES if _MODULES[name].USES)
MODEL_OPERATIONS = tuple(
    name for name in OPERATION_NAMES if _MODULES[name].PROFILE is not None
)
INTERNAL_DATA_TYPES = (
    "concorde-issue-report",
    "concorde-issue-receipt",
    "concorde-agent-stage-context",
    "concorde-agent-stage-result",
    "concorde-review-input",
    "concorde-review-stage-context",
    "concorde-review-stage-result",
    "concorde-review-result",
    "concorde-context-snapshot",
)


def dependencies(operation: str) -> tuple[str, ...]:
    module = _MODULES[operation]
    return tuple("concorde-" + name.replace("_", "-") for name in module.USES)


def contracts() -> dict[str, tuple[str, str]]:
    # Only existing host adapters own request/response envelopes. Model nodes consume their
    # State contract directly; being private does not invent a new external wire interface.
    return {
        name: (f"{name}-request", f"{name}-response")
        for name in OPERATION_NAMES
        if hasattr(_MODULES[name], "REQUEST")
    }


def exported_types() -> tuple[str, ...]:
    return (
        tuple(
            f"{operation}-{suffix}"
            for operation in contracts()
            for suffix in ("request", "response")
        )
        + INTERNAL_DATA_TYPES
    )


def _operation_schemas() -> dict:
    """Collect every operation module's own REQUEST/RESPONSE (proposal section 6.2).

    Operation schema declarations use dependency-free contract shapes.
    """

    import importlib

    operation_inventory = load_operation_inventory()
    result = {}
    for name in operation_inventory.OPERATIONS:
        module = importlib.import_module(f"{operation_inventory.__name__}.{name}")
        if hasattr(module, "REQUEST"):
            result[f"{module.EXTERNAL_NAME}-request"] = module.REQUEST
            result[f"{module.EXTERNAL_NAME}-response"] = module.RESPONSE
    return result


def schemas() -> dict:
    result = {
        "concorde-issue-report": ISSUE_REPORT,
        "concorde-issue-receipt": ISSUE_RECEIPT,
    }
    document_ref = obj(
        {
            "document_id": STRING,
            "path": PATH,
            "digest": DIGEST,
            "owner": STRING,
            "role": {"enum": ["reading", "metadata"]},
        }
    )
    # Context index records (Framework profile P5, Spec context grant): a document is identified, owned
    # and digested, never embedded. Its bytes reach an WorkerProfile through the read-only grant of the path.
    reason = obj({"kind": {"enum": ["owned", "module", "document"]}, "id": STRING})
    source = obj({**document_ref["properties"], "reasons": array(reason, unique=True)})

    def resolution(source_shape):
        return obj(
            {
                "schema_version": {"const": 1},
                "registration": TARGET_DESCRIPTOR,
                "query_id": STRING,
                "query_kind": {"enum": ["module", "scenario"]},
                "module_id": STRING,
                "reading_entry": PATH,
                "documents": array(PATH, unique=True),
                "references": array(REFERENCE, unique=True),
                "sources": array(source_shape),
            }
        )

    protocol_document = obj({"path": PATH, "digest": DIGEST})
    result["concorde-project-proposal"] = obj(
        {
            "action": {"enum": ["initialize"]},
            "base_digest": {"anyOf": [DIGEST, {"type": "null"}]},
            "files": array(PROPOSAL_FILE),
        }
    )
    result["concorde-plan-artifact"] = obj({"plan": STRING})
    result["concorde-task-identity-constraints"] = obj(
        {"reserved_task_ids": array(STRING, unique=True)}
    )
    result["concorde-implementation-task"] = obj(
        {"plan": STRING, "tasks": array(TASK_ITEM)}
    )
    result["concorde-task-scope-feedback"] = obj(
        {"tasks_digest": DIGEST, "reason": {"const": "implementation_boundary"}}
    )
    result["concorde-issue-intent"] = obj({"intent": STRING})
    result["concorde-issue-selection"] = obj(
        {
            "issue_id": STRING,
            "revision": DIGEST,
            "problem": STRING,
            "type": {"enum": ["bug", "gap", "limitation"]},
            "feedback": {"type": "string"},
            "verification": {"type": "string"},
            "duplicates": array(
                obj({"issue_id": STRING, "revision": DIGEST, "problem": STRING})
            ),
        }
    )
    result["concorde-issue-context"] = obj(
        {
            "observations": array(
                obj(
                    {
                        "receipt": ISSUE_RECEIPT,
                        "description": STRING,
                        "impact": STRING,
                        "basis": STRING,
                    }
                )
            )
        }
    )
    stage_input = {
        "anyOf": [
            typed_schema(name)
            for name in (
                "concorde-plan-artifact",
                "concorde-task-identity-constraints",
                "concorde-implementation-task",
                "concorde-task-scope-feedback",
                "concorde-issue-selection",
                "concorde-issue-context",
                "concorde-issue-intent",
                "concorde-review-result",
            )
        ]
    }
    result["concorde-context-snapshot"] = obj(
        {
            "context_id": DIGEST,
            "schema_version": {"const": 6},
            "target_id": STRING,
            "kind": {"const": "module"},
            "focus_id": NULLABLE_ID,
            "phase": STRING,
            "task": STRING,
            "constraints": array(STRING),
            "protocol_binding": obj({"version": STRING, "digest": DIGEST}),
            "protocol": array(protocol_document),
            "spec_resolution": resolution(source),
            "instructions": {"type": "string"},
            "stage_inputs": array(stage_input),
            "implementation_entries": array(IMPLEMENTATION_ENTRY),
            "implementation_files": array(IMPLEMENTATION_FILE),
            "implementation_artifacts": array(ARTIFACT),
            # Resource context (Protocol 5.1): the Module's external references, vendored material it
            # reads but does not own, one tree digest per entry. Every phase sees the entries; modes
            # that declare the ``references`` effect are granted the directories read-only.
            "external_references": array(EXTERNAL_REFERENCE),
            "workspace": WORKSPACE_CONTEXT,
        }
    )
    result["concorde-agent-stage-context"] = obj(
        {
            "snapshot": typed_schema("concorde-context-snapshot"),
            "change_id": NULLABLE_ID,
            "expected_artifacts": array(PATH),
        }
    )
    revision = obj(
        {
            "spec_digest": DIGEST,
            "implementation_digest": {"anyOf": [DIGEST, {"type": "null"}]},
            "baseline": NULLABLE_ID,
            "head": NULLABLE_ID,
        }
    )
    result["concorde-review-input"] = obj(
        {
            "review_mode": {"enum": ["spec", "code"]},
            "input_digest": DIGEST,
            "revision": revision,
            "changes": array(obj({"path": PATH, "patch": {"type": "string"}})),
        }
    )
    result["concorde-review-stage-context"] = obj(
        {
            "snapshot": typed_schema("concorde-context-snapshot"),
            "review": typed_schema("concorde-review-input"),
        }
    )
    review_fields = {
        "context_id": DIGEST,
        "input_digest": DIGEST,
        "review_mode": {"enum": ["spec", "code"]},
        "status": {"enum": ["no_findings", "findings", "incomplete"]},
        "representative_tasks": array(STRING, unique=True),
        "issues": array(REVIEW_ISSUE),
        "answer": STRING,
    }
    result["concorde-review-stage-result"] = obj(review_fields)
    result["concorde-review-result"] = obj(
        {
            **review_fields,
            "context_id": {"anyOf": [DIGEST, {"type": "null"}]},
            "status": {
                "enum": ["no_findings", "findings", "incomplete", "skipped", "not_run"]
            },
            "target_id": STRING,
            "focus_id": NULLABLE_ID,
            "revision": revision,
            "semantic_completeness": {"const": "not_proven"},
        }
    )
    result["concorde-agent-stage-result"] = obj(
        {
            "context_id": DIGEST,
            "outcome": {
                "enum": [
                    "completed",
                    "sufficient",
                    "spec_incomplete",
                    "unsupported",
                    "conflicting",
                    "failed",
                ]
            },
            "answer": {"type": "string"},
            "blockers": array(BLOCKER),
            "documents": array(DOCUMENT_CHANGE),
            "plan": {"type": "string"},
            "tasks": array(TASK_ITEM),
            "issue_decision": obj(
                {
                    "action": {
                        "enum": [
                            "develop",
                            "spec-repair",
                            "verify",
                            "resolved",
                            "duplicate",
                            "not-actionable",
                            "needs-decision",
                        ]
                    },
                    "intent": STRING,
                    "rationale": STRING,
                    "duplicate_of": NULLABLE_ID,
                }
            ),
        },
        ("issue_decision",),
    )
    result.update(_operation_schemas())
    return result


EXECUTABLE_KINDS = {name: module.KIND for name, module in _MODULES.items()}

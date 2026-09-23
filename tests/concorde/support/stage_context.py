"""A typed planner stage context for tests that run a Terminal Agent Operation without a model."""

from concorde.spec.typed_data import typed


def stage_context():
    from concorde.harness.context import (
        PROTOCOL_PATHS,  # noqa: F401  (import keeps the fixture honest)
    )

    snapshot = {
        "context_id": "sha256:" + "3" * 64,
        "schema_version": 8,
        "target_id": "service.fixture",
        "kind": "module",
        "focus_id": None,
        "phase": "plan",
        "task": "Plan",
        "constraints": [],
        "agent_binding": {
            "agent": "planner",
            "spec_path": "agents/planner/spec.md",
            "spec_digest": "sha256:" + "5" * 64,
            "instructions_path": "generated/native/planner.md",
            "instructions_digest": "sha256:" + "6" * 64,
            "definition_digest": "sha256:" + "7" * 64,
            "build_manifest_digest": "sha256:" + "8" * 64,
            "tools": ["read", "grep", "find", "ls"],
            "effects": {
                "reads": ["spec-context", "references"],
                "writes": [],
                "network": False,
                "credentials": "none",
            },
            "workspace": "capsule",
            "timeout_seconds": 1800,
            "digest": "sha256:" + "9" * 64,
        },
        "protocol_binding": {"version": "7.0.0", "digest": "sha256:" + "4" * 64},
        "protocol": [],
        "spec_resolution": {
            "schema_version": 3,
            "registration": {
                "id": "service.fixture",
                "kind": "module",
                "title": "Fixture",
                "documents": ["specs/module.md"],
                "references": [],
                "parent": None,
                "uses": [],
                "files": [],
                "checks": [],
            },
            "query_id": "service.fixture",
            "query_kind": "module",
            "module_id": "service.fixture",
            "reading_entry": "specs/module.md",
            "documents": ["specs/module.md"],
            "references": [],
            "sources": [],
        },
        "shared_bindings": [],
        "stage_inputs": [],
        "implementation_entries": [],
        "implementation_files": [],
        "implementation_artifacts": [],
        "external_references": [],
        "workspace": {
            "kind": "unversioned",
            "current_worktree": "/fixture",
            "current_branch": None,
            "primary_worktree": None,
            "primary_branch": None,
            "change_id": None,
            "phase": None,
            "status": None,
            "outcome": None,
            "active_worktrees": [],
        },
    }
    return typed(
        "concorde-agent-stage-context",
        {
            "snapshot": typed("concorde-context-snapshot", snapshot),
            "change_id": None,
            "expected_artifacts": [],
        },
    )

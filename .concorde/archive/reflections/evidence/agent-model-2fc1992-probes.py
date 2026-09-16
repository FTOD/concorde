"""Reproduce design-review observations in temporary fixture projects.

Usage: <repo>/.venv/bin/python agent-model-probes.py <repo>
No model service is called and the source checkout is not modified.
"""
from dataclasses import fields, replace
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

root = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(root), str(root / "src")]

from concorde.host import capability_host, roles
from concorde.host.build import load_role_prompt
from concorde.host.capability_host import CapabilityHost, Invocation, run_capability
from concorde.host.permissions import LaunchSpecification
from concorde.host.typed_data import typed
from tests.concorde.specification.support import CONFIGURATION, ModelProcessDouble, project

results = {
    "scope": "Temporary fixtures; real host and policy code; substituted model subprocesses",
    "agent_bindings": {
        "role_fields": [item.name for item in fields(roles.Role)],
        "launch_fields": [item.name for item in fields(LaunchSpecification)],
        "role_count": len(roles.ROLES),
        "bound_spec_md_count": sum(Path(role.prompt).name == "spec.md" for role in roles.ROLES.values()),
        "role_sources": {name: role.prompt for name, role in roles.ROLES.items()},
    },
}

with tempfile.TemporaryDirectory(prefix="concorde-agent-policy-review-") as directory:
    project_root = Path(directory)
    project(project_root)
    host = CapabilityHost(project_root, root, mode="describe-policy", allow_primary_worktree=True)
    task = {"target_id": "service.transfer", "task": "Inspect a narrowed implementation Agent"}
    observed = []

    def narrowed_prompt(package_root, role_name):
        prompt = load_role_prompt(package_root, role_name)
        narrowed = replace(prompt, effects=replace(prompt.effects, writes=()))
        observed.append({"role": role_name, "declared_writes": list(narrowed.effects.writes)})
        return narrowed

    with patch.object(capability_host, "load_role_prompt", side_effect=narrowed_prompt):
        Invocation("concorde-implement", CONFIGURATION, task, host).stage("concorde-implement")
    policy = next(item for item in host.descriptions if item["phase"] == "implementation")
    results["narrowed_role_effects"] = {
        "injected_role_declarations": observed,
        "effective_write_paths": policy["write_paths"],
        "declaration_was_enforced": not policy["write_paths"],
        "model_calls": 0,
    }

with tempfile.TemporaryDirectory(prefix="concorde-agent-loop-review-") as directory:
    project_root = Path(directory)
    project(project_root)

    def blocking_review(stage, snapshot, data, cwd):
        if stage == "code-review":
            data.update(status="findings", findings=[{
                "id": "needs-repair", "severity": "blocking", "target_id": snapshot["target_id"],
                "document": "specs/send-money.md", "contract": "Pure transfer",
                "location": {"path": "app/transfer.py", "line": 1},
                "problem": "Probe feedback requires another implementation and review iteration.",
                "affected_task": "Implement the transfer contract",
            }])

    model = ModelProcessDouble(blocking_review)
    try:
        host = CapabilityHost(project_root, root, executor=model.executor,
                              allow_primary_worktree=True, routed_target="service.transfer")
        task = {"target_id": "service.transfer", "task": "Implement the pure transfer contract"}
        result = run_capability("concorde-dev-loop", CONFIGURATION,
                                typed("concorde-dev-loop-request", task), host_context=host)
        stages = [item["stage"] for item in model.calls]
        results["blocking_ai_feedback"] = {
            "status": result["status"],
            "outcome": result["output"]["data"]["outcome"] if result["output"] else None,
            "stages": stages,
            "implementation_invocations": stages.count("implementation"),
            "code_review_invocations": stages.count("code-review"),
            "has_automatic_repair_iteration": stages.count("implementation") > 1,
        }
    finally:
        model.runtime_directory.cleanup()

paths = ["src/concorde/host/roles.py", "src/concorde/host/build.py",
         "src/concorde/host/capability_host.py", "src/concorde/host/permissions.py",
         "src/concorde/host/agent_executor.py", "src/concorde/host/review.py"]
results["source_sha256"] = {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths}
print(json.dumps(results, indent=2))

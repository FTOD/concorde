"""Reproduce the design-review observations of `.concorde/reflections/evidence/agent-model-2fc1992-
probes.py` in temporary fixture projects, against the worktree that resolved R-066 - R-070 (branch
`agent-model`). Adapted, not run unchanged, because the host's behavior itself changed:

- Scenario (a) previously patched `capability_host.load_role_prompt` to narrow the implementation
  Agent's declared writes and observed the *widened* effective policy (R-066). The new host derives
  the compiled policy from the Agent's own declared effects through a narrowing `PolicyBinding`
  (`compile_policy`), so the same patch now makes the host ask for more writes than the (narrowed)
  Agent declares and `Invocation.stage` raises `SpecError(code="permission_denied")` before any
  model call. This script records that refusal instead of a widened `write_paths` list, and adds a
  read-only investigation variant (`readonly=True`) that narrows writes through the host's own
  built-in mechanism (no patch) and shows the resulting `write_paths` is empty.
- Scenario (b) is new: it resolves every entry in `agents.AGENTS` through `agent_model.resolve_agent`
  and records the Agent's `spec.md` path, bound Harness name, binding digest and effective loop
  timeout -- the per-Agent Harness bindings R-067/R-068 found absent.
- Scenario (c) replaces the single blocking-review probe (R-069, which observed the loop stop after
  one implementation and one code-review invocation with no repair) with the resolved
  blocking-then-clean development loop: the same blocking finding is repaired once and the loop
  reaches `ready`. The tasks callback pattern (detect `concorde-review-result` among a `tasks` stage's
  `stage_inputs` and author a new-id repair task) is copied from `RepairLoopTests` in
  `tests/concorde/specification/test_review.py`, which is the test that pins this behavior.
- Scenario (d) extends the recorded `source_sha256` block with `agent_model.py` and `harness.py`
  (new in this worktree) alongside the original six files, and records the worktree's actual HEAD
  commit as `verified_commit` (computed via `git rev-parse HEAD`, not hard-coded).

Usage: <worktree>/.venv/bin/python agent-model-probes-after.py <worktree>
No model service is called and the source checkout is not modified.
"""
from dataclasses import fields, replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

root = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(root), str(root / "src")]

from concorde.host import capability_host, agent_model  # noqa: E402

agents = agent_model.load_agent_inventory()  # top-level agents/ package, not under concorde.host
from concorde.host.build import load_role_prompt  # noqa: E402
from concorde.host.capability_host import CapabilityHost, Invocation, run_capability  # noqa: E402
from concorde.host.change_worktree import read_change  # noqa: E402
from concorde.host.permissions import LaunchSpecification  # noqa: E402
from concorde.host.typed_data import typed  # noqa: E402
from concorde.specification.repository import SpecError  # noqa: E402
from tests.concorde.specification.support import CONFIGURATION, ModelProcessDouble, project  # noqa: E402

results = {
    "scope": "Temporary fixtures; real host and policy code; substituted model subprocesses",
    "adapted_from": ".concorde/reflections/evidence/agent-model-2fc1992-probes.py",
}

# --- (b) agent_bindings: resolve every agents.AGENTS name against this build. ---------------------
results["agent_bindings"] = {
    "launch_fields": [item.name for item in fields(LaunchSpecification)],
    "agent_count": len(agents.AGENTS),
    "bound_spec_md_count": 0,
    "bindings": {},
}
for name in agents.AGENTS:
    binding = agent_model.resolve_agent(root, name)
    if Path(binding.spec_path).name == "spec.md":
        results["agent_bindings"]["bound_spec_md_count"] += 1
    results["agent_bindings"]["bindings"][name] = {
        "spec_path": binding.spec_path,
        "harness": binding.harness,
        "binding_digest": binding.digest,
        "effective_loop_timeout_seconds": binding.effective_loop.timeout_seconds,
        "effective_loop_max_turns": binding.effective_loop.max_turns,
    }

# --- (a) narrowed-writes scenario: the host now refuses instead of widening. -----------------------
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

    error_code = None
    try:
        with patch.object(capability_host, "load_role_prompt", side_effect=narrowed_prompt):
            Invocation("concorde-implement", CONFIGURATION, task, host).stage("concorde-implement")
    except SpecError as error:
        error_code = error.code
    results["narrowed_role_effects"] = {
        "injected_role_declarations": observed,
        "error_code": error_code,
        "declaration_was_enforced": error_code == "permission_denied",
        "model_calls": 0,
    }

# --- (a, continued) read-only investigation variant: the host's own narrowing, unpatched. ----------
with tempfile.TemporaryDirectory(prefix="concorde-agent-readonly-review-") as directory:
    project_root = Path(directory)
    project(project_root)
    host = CapabilityHost(project_root, root, mode="describe-policy", allow_primary_worktree=True)
    task = {"target_id": "service.transfer", "task": "Investigate the transfer contract read-only"}
    Invocation("concorde-implement", CONFIGURATION, task, host).stage("concorde-implement", readonly=True)
    policy = next(item for item in host.descriptions if item["phase"] == "implementation")
    results["readonly_investigation"] = {
        "write_paths": policy["write_paths"],
        "agent": policy["agent"],
        "harness": policy["harness"],
        "model_calls": 0,
    }

# --- (c) blocking-then-clean development loop: one repair iteration, then ready. -------------------
with tempfile.TemporaryDirectory(prefix="concorde-agent-loop-review-") as directory:
    project_root = Path(directory)
    project(project_root)
    task = {"target_id": "service.transfer", "task": "Implement the pure transfer contract"}

    def finding():
        return {"id": "daily-limit-check", "severity": "blocking", "target_id": "service.transfer",
                "document": "specs/send-money.md", "contract": "Pure transfer",
                "location": {"path": "app/transfer.py", "line": 1},
                "problem": "Probe feedback requires another implementation and review iteration.",
                "affected_task": "Reject invalid amounts"}

    counter = [0]
    reviews = {"count": 0}

    def repair_tasks(snapshot, data):
        """Give the repair round a task id that never repeats an earlier (historical) id --
        copied from RepairLoopTests.repair_tasks in tests/concorde/specification/test_review.py."""
        if any(item["type_id"] == "concorde-review-result" for item in snapshot["stage_inputs"]):
            counter[0] += 1
            data["tasks"] = [{"id": f"task.transfer.repair.{counter[0]}", "target_id": snapshot["target_id"],
                "description": "Repair the reported daily-limit defect.",
                "acceptance": "Valid transfer subtracts; invalid amount or insufficient funds raises ValueError.",
                "complete": False}]

    def blocking_then_clean(stage, snapshot, data, cwd):
        if stage == "code-review":
            reviews["count"] += 1
            if reviews["count"] == 1:
                data.update(status="findings", findings=[finding()], gaps=[])
        if stage == "tasks":
            repair_tasks(snapshot, data)

    model = ModelProcessDouble(blocking_then_clean)
    try:
        host = CapabilityHost(project_root, root, executor=model.executor,
                              allow_primary_worktree=True, routed_target="service.transfer")
        result = run_capability("concorde-dev-loop", CONFIGURATION,
                                typed("concorde-dev-loop-request", task), host_context=host)
        stages = [item["stage"] for item in model.calls]
        change = read_change(project_root)
        transitions = change["graph"]["service.transfer"]["transitions"]
        results["blocking_ai_feedback"] = {
            "status": result["status"],
            "outcome": result["output"]["data"]["outcome"] if result["output"] else None,
            "stages": stages,
            "implementation_invocations": stages.count("implementation"),
            "code_review_invocations": stages.count("code-review"),
            "has_automatic_repair_iteration": stages.count("implementation") > 1,
            "graph_transitions": transitions,
        }
    finally:
        model.runtime_directory.cleanup()

# --- (d) source hashes for the same six files plus the two new Agent-model modules. ----------------
paths = ["src/concorde/host/roles.py", "src/concorde/host/build.py",
         "src/concorde/host/capability_host.py", "src/concorde/host/permissions.py",
         "src/concorde/host/agent_executor.py", "src/concorde/host/review.py",
         "src/concorde/host/agent_model.py", "src/concorde/host/harness.py"]
results["source_sha256"] = {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths}
results["verified_commit"] = subprocess.run(
    ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True,
).stdout.strip()
print(json.dumps(results, indent=2))

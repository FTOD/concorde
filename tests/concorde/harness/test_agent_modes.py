"""Mode contracts are enforced independently of model obedience and Agent ceilings."""
import json
import re
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

from concorde.development.capability_host import CapabilityHost, Invocation
from concorde.development.capability_service import run_capability
from concorde.distribution.build import BuildError, load_agent, render_agent
from concorde.harness.agent_executor import AgentProcessExecutor, CapabilityExecutionError, _completion_schema
from concorde.harness.agent_model import (agent_definition, binding_digest, binding_from_json, binding_json,
    effective_mode_loop, load_agents, mode_definition, validate_mode_input, validate_mode_output)
from concorde.harness.context import PHASES, resolve_context, resolve_discovery_context, resolve_topology_author_context
from concorde.harness.harness import LoopPolicy
from concorde.harness.permissions import (PolicyBinding,
    build_launch_specification, compile_policy, render_claude_configuration)
from concorde.spec.repository import SpecError, SpecRepository
from concorde.spec.typed_data import canonical, typed
from concorde.spec.verification import verifies
from tests.concorde.spec.support import PACKAGE, CONFIGURATION, ModelProcessDouble, project


class AgentModeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = project(self.root)
        self.repository = SpecRepository(self.root, PACKAGE)
        self.target = "service.transfer"

    def input(self, agent_name, mode_name):
        agent = agent_definition(agent_name)
        mode = mode_definition(agent, mode_name)
        prompt = load_agent(PACKAGE, agent_name, mode_name)
        artifacts = []
        if mode_name == "tasks":
            artifacts = [typed("concorde-plan-artifact", {"plan": "Accepted plan"}),
                         typed("concorde-task-identity-constraints", {"reserved_task_ids": []})]
        elif mode_name == "implementation":
            artifacts = [typed("concorde-implementation-task", {"plan": "Accepted plan", "tasks": []})]
        elif mode_name == "investigation":
            artifacts = [typed("concorde-reflection-selection", {"head": "abc", "records": []})]
        if agent_name == "coordinator":
            snapshot = resolve_discovery_context(self.repository, (self.target,),
                capability="concorde-main", phase=mode.phase, action=mode.action,
                task="Understand the contract", instructions=prompt.body)
            return typed(mode.constraints.contexts[0], {"snapshot": typed("concorde-discovery-context", snapshot.value)})
        if mode_name == "topology-author":
            target = next(item for item in self.registry["targets"] if item["id"] == self.target)
            references = tuple({"path": path, "targets": [self.target]} for path in target["documents"])
            snapshot = resolve_topology_author_context(self.repository, target,
                task="Accepted target-local task", instructions=prompt.body,
                candidate_document_references=references)
            return typed(mode.constraints.contexts[0], snapshot.value)
        snapshot = resolve_context(self.repository, self.target, phase=mode.phase,
            task="Implement the transfer contract", instructions=prompt.body, stage_inputs=tuple(artifacts))
        data = {"snapshot": typed("concorde-context-snapshot", snapshot.value)}
        if mode_name.endswith("-review"):
            data["review"] = typed("concorde-review-input", {
                "review_mode": mode_name.split("-")[0], "input_digest": snapshot.id,
                "revision": {"spec_digest": snapshot.id, "implementation_digest": None,
                             "baseline": None, "head": None}, "changes": []})
        else:
            data.update(change_id=None, expected_artifacts=[])
        return typed(mode.constraints.contexts[0], data)

    def launch(self, agent_name, mode_name):
        prompt = load_agent(PACKAGE, agent_name, mode_name)
        mode = mode_definition(agent_definition(agent_name), mode_name)
        value = self.input(agent_name, mode_name)
        snapshot = value["data"].get("snapshot", {}).get("data", value["data"])
        role = prompt.name
        roles = {"discovery-context" if agent_name == "coordinator" else "spec-context": ("context.json",)}
        if agent_name == "programmer":
            roles["implementation"] = ("app/transfer.py", "checks/transfer_check.py")
        policy = compile_policy(prompt.effects,
            PolicyBinding("concorde-test", mode.phase, 0, role, role), roles)
        return build_launch_specification(capability="concorde-test", stage=mode.phase, occurrence=0,
            role=role, integration="claude", agent=role, project_root=str(self.root),
            request=snapshot["task"], prompt=prompt.body, prior_results=(),
            workspace_receipt_json=canonical({"source_digest": snapshot["context_id"], "role_paths": roles}),
            workspace_digest=snapshot["context_id"], policy=policy,
            native_configuration=render_claude_configuration(policy, native_enforcement=True),
            runtime_input_json=canonical(value), capability_configuration_json=canonical(CONFIGURATION),
            invocation_id=str(uuid4()), agent_binding_json=binding_json(prompt.binding))

    @verifies("scenario.harness.mode-boundary")
    def test_all_modes_project_only_common_and_selected_instructions_and_empty_capabilities(self):
        self.assertEqual({"coordinator", "spec_engineer", "programmer"}, set(load_agents()))
        self.assertEqual(12, sum(len(agent.modes) for agent in load_agents().values()))
        for agent in load_agents().values():
            self.assertFalse(agent.constraints.capabilities)
            for mode in agent.modes:
                with self.subTest(agent=agent.name, mode=mode.name):
                    output = render_agent(PACKAGE, agent.name.replace("_", "-"), mode.name)
                    self.assertIn(agent.spec, output.sources)
                    self.assertIn(mode.instructions, output.sources)
                    self.assertFalse(mode.constraints.capabilities)
                    text = output.content.decode()
                    self.assertEqual(1, text.count("# Mode:"))
                    self.assertIn(f"# Mode: {mode.name}\n", text)
                    self.assertTrue(all(other.instructions not in output.sources
                                        for other in agent.modes if other != mode))

    @verifies("scenario.harness.mode-boundary")
    def test_all_modes_bind_exact_context_pair_and_phase(self):
        for agent in load_agents().values():
            for mode in agent.modes:
                with self.subTest(agent=agent.name, mode=mode.name):
                    launch = self.launch(agent.name, mode.name)
                    binding = AgentProcessExecutor._preflight_agent_binding(launch)
                    self.assertEqual(mode.name, binding.mode)
                    with self.assertRaises(ValueError):
                        validate_mode_input(agent, mode.name, json.loads(launch.runtime_input_json), phase="wrong-phase")
        topology = self.input("spec_engineer", "topology-author")["data"]
        self.assertEqual(self.target, topology["target"]["id"])
        self.assertEqual("Accepted target-local task", topology["task"])
        self.assertTrue(topology["candidate_document_references"])

    @verifies("scenario.harness.mode-boundary")
    def test_same_agent_rejects_wrong_context_output_pair_and_unknown_mode(self):
        agent = agent_definition("spec_engineer")
        for mode, wrong in (("specify", "spec-review"), ("spec-review", "topology-author"),
                            ("topology-author", "plan")):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                validate_mode_input(agent, mode, self.input(agent.name, wrong),
                    phase=mode_definition(agent, mode).phase)
        with self.assertRaises(BuildError):
            mode_definition(agent, "unregistered")
        with self.assertRaises(ValueError):
            validate_mode_output(agent, "specify", typed("concorde-topology-author-result", {
                "target_id": self.target, "context_id": "sha256:" + "1" * 64,
                "outcome": "completed", "answer": "wrong paired result", "gaps": [], "documents": []}))

    @verifies("scenario.harness.mode-boundary")
    def test_resolver_admits_task_control_artifacts_only_in_tasks_with_or_without_mode(self):
        controls = (
            typed("concorde-task-identity-constraints", {"reserved_task_ids": ["task.retained"]}),
            typed("concorde-task-scope-feedback", {
                "tasks_digest": "sha256:" + "1" * 64, "reason": "implementation_boundary"}),
        )
        modes = [mode for agent in load_agents().values() for mode in agent.modes]
        for control in controls:
            for phase in sorted(PHASES - {"tasks"}):
                for mode in [None, *(mode for mode in modes if mode.phase == phase)]:
                    with self.subTest(type_id=control["type_id"], phase=phase,
                                      mode=mode.name if mode else None):
                        with self.assertRaises(SpecError) as caught:
                            resolve_context(self.repository, self.target, phase=phase,
                                            mode=mode, stage_inputs=(control,))
                        self.assertEqual("incompatible_handoff", caught.exception.code)
        for mode in (None, mode_definition(agent_definition("spec_engineer"), "tasks")):
            artifacts = (typed("concorde-plan-artifact", {"plan": "Accepted plan"}),
                         typed("concorde-implementation-task", {"plan": "Accepted plan", "tasks": []}),
                         *controls)
            snapshot = resolve_context(self.repository, self.target, phase="tasks",
                                       mode=mode, stage_inputs=artifacts)
            self.assertEqual(list(artifacts), snapshot.value["stage_inputs"])
            preview = resolve_context(self.repository, self.target, phase="tasks", mode=mode)
            self.assertEqual([], preview.value["stage_inputs"])
        with self.assertRaises(SpecError) as caught:
            resolve_context(self.repository, self.target, phase="plan",
                            mode=mode_definition(agent_definition("spec_engineer"), "tasks"))
        self.assertEqual("permission_denied", caught.exception.code)

    @verifies("scenario.harness.mode-boundary")
    def test_task_identity_constraints_are_required_frozen_and_tasks_only(self):
        agent = agent_definition("spec_engineer")
        value = self.input("spec_engineer", "tasks")
        validate_mode_input(agent, "tasks", value, phase="tasks")
        snapshot = value["data"]["snapshot"]["data"]
        snapshot["stage_inputs"].pop()
        with self.assertRaisesRegex(ValueError, "stage inputs"):
            validate_mode_input(agent, "tasks", value, phase="tasks")

        contexts = []
        for reserved in ([], ["task.retained"]):
            contexts.append(resolve_context(self.repository, self.target, phase="tasks",
                task="Implement the transfer contract", mode=mode_definition(agent, "tasks"),
                stage_inputs=(typed("concorde-plan-artifact", {"plan": "Accepted plan"}),
                    typed("concorde-task-identity-constraints", {"reserved_task_ids": reserved}))))
        self.assertNotEqual(contexts[0].id, contexts[1].id)
        for owner, name in (("spec_engineer", "plan"), ("programmer", "implementation"),
                            ("spec_engineer", "spec-review"), ("programmer", "code-review")):
            value = self.input(owner, name)
            value["data"]["snapshot"]["data"]["stage_inputs"].append(
                typed("concorde-task-identity-constraints", {"reserved_task_ids": ["task.retained"]}))
            with self.subTest(mode=name), self.assertRaisesRegex(ValueError, "stage inputs"):
                validate_mode_input(agent_definition(owner), name, value, phase=name)

    @verifies("scenario.harness.mode-boundary")
    def test_artifact_channels_do_not_cross_modes_or_enter_reviews(self):
        agent = agent_definition("programmer")
        value = self.input(agent.name, "investigation")
        with self.assertRaisesRegex(ValueError, "stage inputs"):
            validate_mode_input(agent, "implementation", value, phase="implementation")
        for owner, name in (("spec_engineer", "spec-review"), ("programmer", "code-review")):
            value = self.input(owner, name)
            value["data"]["snapshot"]["data"]["stage_inputs"] = [
                typed("concorde-plan-artifact", {"plan": "PRIVATE_AUTHOR_ARTIFACT"})]
            with self.assertRaisesRegex(ValueError, "stage inputs"):
                validate_mode_input(agent_definition(owner), name, value, phase=name)
        value = self.input("spec_engineer", "plan")
        value["data"]["snapshot"]["data"]["implementation_artifacts"] = [
            {"id": "app/transfer.py", "path": "app/transfer.py", "digest": "sha256:" + "1" * 64}]
        with self.assertRaisesRegex(ValueError, "implementation contents"):
            validate_mode_input(agent_definition("spec_engineer"), "plan", value, phase="plan")

    @verifies("scenario.harness.mode-boundary")
    def test_result_fields_cannot_exploit_the_shared_stage_schema(self):
        base = {"context_id": "sha256:" + "1" * 64, "outcome": "completed", "answer": "result",
                "gaps": [], "documents": [], "plan": "", "tasks": []}
        for owner, mode in (("spec_engineer", "tasks"), ("programmer", "implementation"),
                            ("programmer", "investigation")):
            value = typed("concorde-agent-stage-result", {**base, "plan": "Unadmitted plan"})
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "cannot return plan"):
                validate_mode_output(agent_definition(owner), mode, value)

    @verifies("scenario.harness.mode-boundary")
    def test_modes_cannot_widen_agent_ceiling(self):
        agent = agent_definition("spec_engineer")
        mode = mode_definition(agent, "plan")
        for constraints in (
            replace(mode.constraints, effects=replace(mode.constraints.effects, writes=("implementation",))),
            replace(mode.constraints, effects=replace(mode.constraints.effects, reads=("implementation",))),
            replace(mode.constraints, effects=replace(mode.constraints.effects, network=True)),
            replace(mode.constraints, effects=replace(mode.constraints.effects, credentials="declared")),
            replace(mode.constraints, capabilities=("concorde-deliver",)),
            replace(mode.constraints, allow_delegation=True),
            replace(mode.constraints, limits=LoopPolicy(9999)),
        ):
            with self.subTest(constraints=constraints), self.assertRaises(BuildError):
                mode_definition(replace(agent, modes=(replace(mode, constraints=constraints),)), "plan")

    @verifies("scenario.harness.mode-boundary")
    def test_mode_limits_preserve_a_harness_turn_cap_inherited_through_agent_limits(self):
        agent = agent_definition("spec_engineer")
        agent = replace(agent, harness=replace(agent.harness, loop=LoopPolicy(60, 3)),
                        constraints=replace(agent.constraints, limits=LoopPolicy(30)))
        mode = mode_definition(agent, "plan")
        inherited = replace(mode, constraints=replace(mode.constraints, limits=LoopPolicy(20)))
        narrowed = replace(agent, modes=(inherited,))
        self.assertEqual(LoopPolicy(20, 3), effective_mode_loop(narrowed, mode_definition(narrowed, "plan")))
        widened = replace(mode, constraints=replace(mode.constraints, limits=LoopPolicy(20, 4)))
        with self.assertRaises(BuildError):
            mode_definition(replace(agent, modes=(widened,)), "plan")

    @verifies("scenario.harness.mode-boundary")
    def test_forged_writable_review_and_investigation_fail_before_process_start(self):
        for name in ("code-review", "investigation"):
            with self.subTest(mode=name):
                launch = self.launch("programmer", name)
                # Bypass Host construction deliberately; the native config agrees with the forged policy.
                forged = replace(launch.policy, write_paths=("app/transfer.py",))
                launch = replace(launch, policy=forged,
                    native_configuration=render_claude_configuration(forged, native_enforcement=True))
                runner, probe = Mock(), Mock()
                with self.assertRaisesRegex(CapabilityExecutionError, "mode preflight.*writable"):
                    AgentProcessExecutor(runner=runner, version_probe=probe)(launch)
                runner.assert_not_called()
                probe.assert_not_called()

    @verifies("scenario.harness.mode-boundary")
    def test_readonly_modes_cannot_expand_file_grants_to_a_listed_directory(self):
        for name in ("code-review", "investigation"):
            with self.subTest(mode=name):
                launch = self.launch("programmer", name)
                value = json.loads(launch.runtime_input_json)
                snapshot = value["data"]["snapshot"]["data"]
                snapshot["implementation_entries"].append({"path": "app/", "entity_id": None,
                                                           "pending": False, "directory": True})
                receipt = json.loads(launch.workspace_receipt_json)
                receipt["role_paths"]["implementation"] = ["app"]
                mode = mode_definition(agent_definition("programmer"), name)
                policy = compile_policy(mode.constraints.effects,
                    PolicyBinding(launch.capability, launch.stage, 0, launch.role, launch.agent),
                    {key: tuple(paths) for key, paths in receipt["role_paths"].items()})
                forged = replace(launch, runtime_input_json=canonical(value),
                    workspace_receipt_json=canonical(receipt), policy=policy,
                    native_configuration=render_claude_configuration(policy, native_enforcement=True))
                runner, probe = Mock(), Mock()
                with self.assertRaisesRegex(CapabilityExecutionError, "frozen implementation files"):
                    AgentProcessExecutor(runner=runner, version_probe=probe)(forged)
                runner.assert_not_called()
                probe.assert_not_called()

    @verifies("scenario.harness.mode-boundary")
    def test_investigation_host_expands_directory_entries_into_exact_readonly_files(self):
        target = next(item for item in self.registry["targets"] if item["id"] == self.target)
        target["files"] = ["app/", "checks/"]
        (self.root / ".concorde/specs.json").write_text(json.dumps(self.registry))
        path = self.root / "specs/transfer/module.md"
        path.write_text(path.read_text().replace('"app/transfer.py"', '"app/"')
                        .replace('"checks/transfer_check.py"', '"checks/"'))
        (self.root / "app/.hidden.py").write_text("Not in the resolved implementation context")
        host = CapabilityHost(self.root, PACKAGE, allow_primary_worktree=True, mode="describe-policy")
        run = Invocation("concorde-implement", CONFIGURATION,
                         {"target_id": self.target, "task": "Investigate the report"}, host)
        run.stage("concorde-implement", mode="investigation")
        reads = host.descriptions[0]["read_paths"]
        self.assertIn("app/transfer.py", reads)
        self.assertNotIn("app", reads)
        self.assertNotIn("checks", reads)
        self.assertNotIn("app/.hidden.py", reads)
        self.assertEqual([], host.descriptions[0]["write_paths"])

    @verifies("scenario.harness.context-freeze", "scenario.harness.mode-boundary")
    def test_implementation_search_recipe_uses_frozen_files_without_directory_walks(self):
        target = next(item for item in self.registry["targets"] if item["id"] == self.target)
        target["files"] = ["app/", "checks/transfer_check.py"]
        (self.root / ".concorde/specs.json").write_text(json.dumps(self.registry))
        document = self.root / "specs/transfer/module.md"
        document.write_text(document.read_text().replace('"app/transfer.py"', '"app/"'))
        # Spaces and shell syntax must remain path data, even across multiple batches.
        admitted = [f"app/match {index}.txt" for index in range(101)]
        admitted.append("app/$(touch leaked); 'quoted'.txt")
        excluded = [f"app/{directory}/decoy.txt" for directory in
                    ("node_modules", "__pycache__", ".venv", "build", "dist", ".hidden")]
        excluded += ["app/.secret", "app/cache.pyc", "app/output.log", "outside.txt"]
        for name in admitted + excluded:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("BOUNDARY_NEEDLE\n")
        self.repository = SpecRepository(self.root, PACKAGE)
        value = self.input("programmer", "implementation")
        snapshot = value["data"]["snapshot"]["data"]
        capsule = self.root / "context.json"
        capsule.write_text(json.dumps(snapshot))
        prompt = load_agent(PACKAGE, "programmer", "implementation").body
        recipe, = re.findall(r"```sh\n(.*?)\n```", prompt, re.S)

        def search(pattern):
            return subprocess.run(["sh", "-c", recipe, "bounded-search", str(capsule), pattern],
                                  cwd=self.root, capture_output=True, text=True, timeout=20)

        result = search("BOUNDARY_NEEDLE")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({f"{path}:1:BOUNDARY_NEEDLE" for path in admitted},
                         set(result.stdout.splitlines()))
        self.assertFalse((self.root / "leaked").exists())
        self.assertEqual(1, search("NO_SUCH_MATCH").returncode)
        # An empty admitted set must not fall back to rg's current-directory search.
        snapshot["implementation_artifacts"] = []
        capsule.write_text(json.dumps(snapshot))
        result = search("BOUNDARY_NEEDLE")
        self.assertEqual((1, "", ""), (result.returncode, result.stdout, result.stderr))
        snapshot["implementation_artifacts"] = [{"path": "app/missing.txt"}]
        capsule.write_text(json.dumps(snapshot))
        self.assertEqual(2, search("BOUNDARY_NEEDLE").returncode)

    @verifies("scenario.harness.mode-boundary")
    def test_snapshot_cannot_inject_another_modes_instructions(self):
        launch = self.launch("spec_engineer", "spec-review")
        value = json.loads(launch.runtime_input_json)
        value["data"]["snapshot"]["data"]["instructions"] = load_agent(PACKAGE, "spec_engineer", "specify").body
        with self.assertRaisesRegex(CapabilityExecutionError, "snapshot instructions"):
            AgentProcessExecutor._preflight_agent_binding(replace(launch, runtime_input_json=canonical(value)))

    @verifies("scenario.harness.mode-boundary")
    def test_output_schema_narrows_the_shared_stage_result_to_investigation(self):
        schema = _completion_schema(self.launch("programmer", "investigation"))
        fields = schema["$defs"]["concorde-agent-stage-result"]["properties"]
        self.assertEqual(0, fields["tasks"]["maxItems"])
        self.assertEqual(0, fields["documents"]["maxItems"])
        self.assertEqual("", fields["plan"]["const"])
        self.assertNotEqual(0, fields["reflection_findings"].get("maxItems"))

    @verifies("scenario.harness.mode-boundary")
    def test_catalog_cannot_launch_without_a_mode_or_through_legacy_untyped_input(self):
        launch = self.launch("programmer", "implementation")
        binding = replace(binding_from_json(launch.agent_binding_json), mode=None, mode_digest=None)
        binding = replace(binding, digest=binding_digest(binding))
        runner, probe = Mock(), Mock()
        for forged in (replace(launch, agent_binding_json=binding_json(binding)),
                       replace(launch, runtime_input_json=None, agent_binding_json=None)):
            with self.assertRaises(CapabilityExecutionError):
                AgentProcessExecutor(runner=runner, version_probe=probe)(forged)
        runner.assert_not_called()
        probe.assert_not_called()

    @verifies("scenario.harness.mode-boundary")
    def test_host_revalidates_mode_output_from_an_injected_executor(self):
        model = ModelProcessDouble()
        self.addCleanup(model.runtime_directory.cleanup)
        def executor(launch):
            result = model.executor(launch)
            output = result.completion.domain_output
            output["data"]["plan"] = "A Spec author cannot return this plan."
            return replace(result, completion=replace(result.completion, domain_output=output))
        host = CapabilityHost(self.root, PACKAGE, executor=executor, allow_primary_worktree=True,
                              routed_target=self.target)
        result = run_capability("concorde-specify", CONFIGURATION,
            typed("concorde-specify-request", {"target_id": self.target, "task": "Clarify the contract"}),
            host_context=host)
        self.assertNotEqual("succeeded", result["status"])
        self.assertIn("cannot return plan", result["errors"][0]["message"])

    @verifies("scenario.harness.mode-boundary")
    def test_mode_binding_changes_invalidate_review_identity_even_with_same_prompt(self):
        from concorde.development import review
        host = CapabilityHost(self.root, PACKAGE, allow_primary_worktree=True)
        run = Invocation("concorde-review", CONFIGURATION,
                         {"target_id": self.target, "task": "Review the contract"}, host)
        before, prompt = review.inputs(run, "spec")
        binding = replace(prompt.binding, mode_digest="sha256:" + "a" * 64)
        binding = replace(binding, digest=binding_digest(binding))
        with patch.object(review, "load_role_prompt", return_value=replace(prompt, binding=binding)):
            after, _ = review.inputs(run, "spec")
        self.assertNotEqual(before["input_digest"], after["input_digest"])

    @verifies("scenario.harness.mode-boundary")
    def test_original_workflow_uses_fresh_author_and_review_invocations(self):
        model = ModelProcessDouble()
        self.addCleanup(model.runtime_directory.cleanup)
        launches = []
        def executor(launch):
            launches.append(launch)
            return model.executor(launch)
        host = CapabilityHost(self.root, PACKAGE, executor=executor, allow_primary_worktree=True)
        result = run_capability("concorde-dev-loop", CONFIGURATION,
            typed("concorde-dev-loop-request", {"target_id": self.target,
                "task": "Implement the pure transfer contract"}), host_context=host)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(len(launches), len({launch.invocation_id for launch in launches}))
        by_mode = {binding_from_json(launch.agent_binding_json).mode: launch for launch in launches}
        for author, reviewer in (("specify", "spec-review"), ("implementation", "code-review")):
            left, right = by_mode[author], by_mode[reviewer]
            self.assertEqual(left.agent, right.agent)
            self.assertNotEqual(left.invocation_id, right.invocation_id)
            self.assertNotEqual(left.workspace_digest, right.workspace_digest)
            self.assertFalse(right.prior_results)
            self.assertFalse(right.policy.write_paths)
            snapshot = json.loads(right.runtime_input_json)["data"]["snapshot"]["data"]
            self.assertEqual([], snapshot["stage_inputs"])
            self.assertNotEqual(left.prompt, right.prompt)
        self.assertTrue(by_mode["implementation"].policy.write_paths)

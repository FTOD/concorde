from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

from dataclasses import replace as dataclass_replace

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.harness.agent_executor import (  # noqa: E402
    AgentProcessExecutor,
    CapabilityExecutionError,
    resolve_runtime_bootstrap,
    verify_runtime_bootstrap,
    _completion_schema,
    _prompt,
)
from concorde.harness.agent_model import (  # noqa: E402
    binding_digest,
    binding_json,
    resolve_agent,
)
from concorde.harness.permissions import (  # noqa: E402
    LaunchSpecification,
    PolicyBinding,
    build_launch_specification,
    compile_policy,
    render_claude_configuration,
    render_codex_configuration,
    runtime_bootstrap_file,
)
from concorde.harness.effects import EffectDeclaration  # noqa: E402
from concorde.spec.repository import PROTOCOL_VERSION  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402


class AgentExecutorTests(unittest.TestCase):
    def setUp(self):
        self.runtime_directory = tempfile.TemporaryDirectory()
        self.runtime_executable = Path(self.runtime_directory.name) / "codex"
        self.runtime_executable.write_bytes(b"\x7fELFfixture-codex-runtime")
        self.runtime_executable.chmod(0o755)

    def tearDown(self):
        self.runtime_directory.cleanup()

    def runtime_bootstrap(self, integration, executable, project_root, environment):
        if integration != "codex":
            return ()
        return (
            runtime_bootstrap_file(
                path=str(self.runtime_executable),
                sha256="sha256:" + hashlib.sha256(self.runtime_executable.read_bytes()).hexdigest(),
                size=self.runtime_executable.stat().st_size,
                mode=0o755,
                owner=self.runtime_executable.stat().st_uid,
            ),
        )

    def completion(self, argv, *, status="success", output="codex-result", limitations="none"):
        if "--output-schema" in argv:
            schema_path = argv[argv.index("--output-schema") + 1]
            schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        else:
            schema = json.loads(argv[argv.index("--json-schema") + 1])
        properties = schema["properties"]
        gate_status = "passed" if status == "success" else "failed"
        return {
            "schema_version": properties["schema_version"]["const"],
            "capability": properties["capability"]["const"],
            "stage": properties["stage"]["const"],
            "occurrence": properties["occurrence"]["const"],
            "role": properties["role"]["const"],
            "launch_digest": properties["launch_digest"]["const"],
            "workspace_digest": properties["workspace_digest"]["const"],
            "runtime_bootstrap_digest": properties["runtime_bootstrap_digest"]["const"],
            "status": status,
            "output": output,
            "limitations": limitations,
            "gates": [{"name": "workspace", "status": gate_status, "evidence": "fixture evidence"}],
        }

    def codex_stdout(self, argv, **completion):
        envelope = self.completion(argv, **completion)
        return "\n".join(
            (
                json.dumps({"type": "thread.started", "thread_id": "fixture"}),
                json.dumps({"type": "turn.started"}),
                json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(envelope)}}),
                json.dumps({"type": "turn.completed", "usage": {}}),
            )
        )

    def test_runtime_bootstrap_attests_one_external_real_executable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            runtime = root / "runtime"
            project.mkdir()
            runtime.mkdir()
            executable = runtime / "codex"
            executable.write_bytes(b"\x7fELFfixture-codex")
            executable.chmod(0o755)

            files = resolve_runtime_bootstrap("codex", "codex", str(project), {"PATH": str(runtime)})
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].path, str(executable.resolve()))
            self.assertEqual(files[0].size, len(b"\x7fELFfixture-codex"))
            self.assertRegex(files[0].sha256, r"^sha256:[0-9a-f]{64}$")
            verify_runtime_bootstrap(files)
            self.assertEqual(resolve_runtime_bootstrap("claude", "claude", str(project), {}), ())

            executable.write_bytes(b"\x7fELFsubstituted-codex")
            with self.assertRaisesRegex(CapabilityExecutionError, "changed after attestation"):
                verify_runtime_bootstrap(files)
            executable.write_bytes(b"\x7fELFfixture-codex")

            executable.chmod(0o775)
            with self.assertRaisesRegex(CapabilityExecutionError, "group- or world-writable"):
                resolve_runtime_bootstrap("codex", "codex", str(project), {"PATH": str(runtime)})

            executable.write_text("#!/bin/sh\nexec node codex.js\n", encoding="utf-8")
            executable.chmod(0o755)
            with self.assertRaisesRegex(CapabilityExecutionError, "native executable"):
                resolve_runtime_bootstrap("codex", "codex", str(project), {"PATH": str(runtime)})

            inside = project / "codex"
            inside.write_bytes(b"\x7fELFinside")
            inside.chmod(0o755)
            with self.assertRaisesRegex(CapabilityExecutionError, "outside project authority"):
                resolve_runtime_bootstrap("codex", "codex", str(project), {"PATH": str(project)})

    def policy(self):
        return compile_policy(
            EffectDeclaration(
                reads=("selected-feature", "attempt"),
                writes=("attempt",),
                network=False,
                credentials="none",
            ),
            PolicyBinding(
                capability="concorde-plan",
                stage="author",
                occurrence=0,
                role="concorde-plan-author",
                agent="plan-author",
            ),
            {
                "selected-feature": ("specs/example/features/001-change.md",),
                "attempt": (".concorde/attempts/feature.example.change",),
            },
        )

    def specification(self, integration: str):
        policy = self.policy()
        native = (
            render_codex_configuration(policy, native_enforcement=True)
            if integration == "codex"
            else render_claude_configuration(policy, native_enforcement=True)
        )
        return build_launch_specification(
            capability="concorde-plan",
            stage="author",
            occurrence=0,
            role="concorde-plan-author",
            integration=integration,
            agent="plan-author",
            project_root="/fixture/project",
            request="Plan the selected change",
            prompt="# Plan Author\n\nUse bounded context.",
            prior_results=("context:ready",),
            workspace_receipt_json=json.dumps(
                {
                    "schema_version": 13,
                    "feature_id": "feature.example.change",
                    "feature_path": "specs/example/features/001-change.md",
                    "module_architecture": "specs/example/architecture.md",
                    "attempt_dir": ".concorde/attempts/feature.example.change",
                    "attempt_state": "active",
                    "role_paths": {},
                    "denied_paths": [],
                    "source_digest": "sha256:" + "1" * 64,
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            workspace_digest="sha256:" + "1" * 64,
            policy=policy,
            native_configuration=native,
        )

    @verifies("scenario.harness.execute-success")
    def test_codex_process_handoff_is_injectable_scrubbed_and_receipted(self):
        calls = []

        def runner(argv, *, cwd, env, input_text, timeout=None):
            calls.append((argv, cwd, env, input_text))
            return subprocess.CompletedProcess(argv, 0, stdout=self.codex_stdout(argv), stderr="")

        executor = AgentProcessExecutor(
            runner=runner,
            version_probe=lambda integration, executable: "codex-cli 9.1",
            runtime_bootstrap_resolver=self.runtime_bootstrap,
            environment={
                "PATH": "/bin",
                "LANG": "C.UTF-8",
                "OPENAI_API_KEY": "must-not-leak",
                "ANTHROPIC_API_KEY": "must-not-leak",
            },
        )
        spec = self.specification("codex")
        result = executor(spec)

        self.assertEqual(len(calls), 1)
        argv, cwd, env, input_text = calls[0]
        self.assertEqual(
            argv[:4],
            (str(self.runtime_executable), "--ask-for-approval", "never", "exec"),
        )
        self.assertNotIn("--sandbox", argv)
        self.assertEqual(cwd, "/fixture/project")
        self.assertEqual(env, {"LANG": "C.UTF-8", "PATH": "/bin"})
        self.assertIn("Plan the selected change", input_text)
        self.assertIn("context:ready", input_text)
        self.assertEqual(result.output, "codex-result")
        self.assertEqual(result.receipt.policy_digest, spec.policy.digest)
        self.assertNotEqual(result.receipt.config_digest, spec.native_configuration.digest)
        self.assertEqual(result.receipt.requested_launch_digest, spec.digest)
        self.assertEqual(result.receipt.launch_digest, result.completion.launch_digest)
        self.assertEqual(result.receipt.client_version, "codex-cli 9.1")
        self.assertEqual(result.receipt.enforcement, "native")
        self.assertEqual(result.receipt.completion_status, "success")
        self.assertEqual(result.completion.gates[0].name, "workspace")
        self.assertIn(str(self.runtime_executable), " ".join(argv))
        self.assertIn("--output-schema", argv)
        self.assertIn("--json", argv)
        with self.assertRaises(FrozenInstanceError):
            result.output = "changed"  # type: ignore[misc]

    @verifies("scenario.harness.execute-success")
    def test_claude_process_handoff_uses_inline_strict_settings_and_no_retry(self):
        calls = []

        def runner(argv, *, cwd, env, input_text, timeout=None):
            calls.append((argv, input_text))
            envelope = self.completion(argv, output="claude-result")
            stdout = json.dumps({"type": "result", "subtype": "success", "is_error": False, "structured_output": envelope})
            return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")

        spec = self.specification("claude")
        result = AgentProcessExecutor(
            runner=runner,
            version_probe=lambda integration, executable: "claude-code 4.2",
            environment={"PATH": "/bin"},
        )(spec)
        argv, input_text = calls[0]
        self.assertEqual(argv[:2], ("claude", "-p"))
        self.assertIn("--settings", argv)
        self.assertIn('"failIfUnavailable":true', "".join(argv))
        self.assertIn('"allowUnsandboxedCommands":false', "".join(argv))
        self.assertIn("--json-schema", argv)
        self.assertNotIn("$schema", json.loads(argv[argv.index("--json-schema") + 1]))
        self.assertIn("--output-format", argv)
        self.assertIn("Use bounded context", input_text)
        self.assertEqual(result.output, "claude-result")

    def test_every_role_receives_the_envelope_success_and_failure_contract(self):
        base = self.specification("codex")
        for context_type in (
            None,
            "concorde-main-stage-context",
            "concorde-agent-stage-context",
            "concorde-review-stage-context",
            "concorde-topology-author-context",
        ):
            with self.subTest(context_type=context_type):
                spec = replace(base, runtime_input_json=(
                    json.dumps({"type_id": context_type}) if context_type else None
                ))
                prompt = _prompt(spec)
                self.assertIn("limitations is exactly 'none'", prompt)
                self.assertIn("never an empty string", prompt)
                self.assertIn("at least one failed gate", prompt)
                if context_type:
                    self.assertIn("Set domain_output to null for status=failed", prompt)
                    self.assertIn("does not by itself make the envelope fail", prompt)
                else:
                    self.assertNotIn("domain_output", prompt)
                if context_type == "concorde-agent-stage-context":
                    self.assertIn("unused domain_output fields", prompt)

    def test_generation_schema_excludes_empty_limitations(self):
        from jsonschema import Draft202012Validator

        for integration in ("codex", "claude"):
            with self.subTest(integration=integration):
                schema = _completion_schema(self.specification(integration))
                field = schema["properties"]["limitations"]
                validator = Draft202012Validator(field)
                self.assertFalse(validator.is_valid(""))
                self.assertTrue(validator.is_valid("none"))
                self.assertTrue(validator.is_valid("required tool unavailable"))
                self.assertIn("exactly the lowercase string 'none'", field["description"])

    @verifies("scenario.harness.execute-success", "scenario.harness.execute-failure")
    def test_success_completion_rejects_wrong_limitations_and_failed_gates(self):
        spec = self.specification("codex")
        for limitation, failed_gate, expected_error in (
            ("", False, "received an empty string"),
            ("None", False, "received a different string"),
            (" none ", False, "received a different string"),
            ("required tool unavailable", False, "received a different string"),
            ("none", True, "contains failed gates"),
            ("none", False, None),
        ):
            with self.subTest(limitation=limitation, failed_gate=failed_gate):
                def runner(argv, **kwargs):
                    envelope = self.completion(argv, limitations=limitation)
                    if failed_gate:
                        envelope["gates"][0]["status"] = "failed"
                    stdout = "\n".join((
                        json.dumps({"type": "item.completed", "item": {
                            "type": "agent_message", "text": json.dumps(envelope),
                        }}),
                        json.dumps({"type": "turn.completed"}),
                    ))
                    return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")

                executor = AgentProcessExecutor(
                    runner=runner,
                    version_probe=lambda integration, executable: "codex-cli 9.1",
                    runtime_bootstrap_resolver=self.runtime_bootstrap,
                    environment={"PATH": "/bin"},
                )
                if expected_error:
                    with self.assertRaisesRegex(CapabilityExecutionError, expected_error) as raised:
                        executor(spec)
                    self.assertEqual(raised.exception.receipt.status, "failed")
                else:
                    self.assertEqual(executor(spec).completion.limitations, "none")

    @verifies("scenario.harness.execute-failure")
    def test_zero_exit_semantic_failure_and_malformed_completion_fail_closed(self):
        spec = self.specification("codex")

        def failed(argv, **kwargs):
            stdout = self.codex_stdout(
                argv,
                status="failed",
                output="",
                limitations="mandatory workspace gate did not run",
            )
            return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")

        executor = AgentProcessExecutor(
            runner=failed,
            version_probe=lambda integration, executable: "codex-cli 9.1",
            runtime_bootstrap_resolver=self.runtime_bootstrap,
            environment={"PATH": "/bin"},
        )
        with self.assertRaisesRegex(CapabilityExecutionError, "reported failed completion") as raised:
            executor(spec)
        self.assertEqual(raised.exception.receipt.status, "failed")
        self.assertEqual(raised.exception.receipt.exit_code, 0)
        self.assertEqual(raised.exception.receipt.completion_status, "failed")
        self.assertIn("workspace gate", raised.exception.receipt.limitations)

        malformed = AgentProcessExecutor(
            runner=lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, stdout="not-json", stderr=""),
            version_probe=lambda integration, executable: "codex-cli 9.1",
            runtime_bootstrap_resolver=self.runtime_bootstrap,
            environment={"PATH": "/bin"},
        )
        with self.assertRaisesRegex(CapabilityExecutionError, "invalid capability completion") as malformed_error:
            malformed(spec)
        self.assertEqual(malformed_error.exception.receipt.status, "failed")

    @verifies("scenario.harness.execute-success")
    def test_recoverable_failed_tool_event_can_end_in_valid_success(self):
        spec = self.specification("codex")

        def runner(argv, **kwargs):
            envelope = self.completion(argv, output="recovered")
            stdout = "\n".join(
                (
                    json.dumps({"type": "thread.started", "thread_id": "fixture"}),
                    json.dumps({"type": "turn.started"}),
                    json.dumps({
                        "type": "item.completed",
                        "item": {"type": "command_execution", "status": "failed", "exit_code": 1},
                    }),
                    json.dumps({
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": json.dumps(envelope)},
                    }),
                    json.dumps({"type": "turn.completed", "usage": {}}),
                )
            )
            return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")

        result = AgentProcessExecutor(
            runner=runner,
            version_probe=lambda integration, executable: "codex-cli 9.1",
            runtime_bootstrap_resolver=self.runtime_bootstrap,
            environment={"PATH": "/bin"},
        )(spec)
        self.assertEqual(result.output, "recovered")
        self.assertEqual(result.receipt.status, "success")

    @verifies("scenario.harness.execute-failure")
    def test_native_lifecycle_failure_and_stale_completion_identity_fail_closed(self):
        spec = self.specification("codex")

        lifecycle = AgentProcessExecutor(
            runner=lambda argv, **kwargs: subprocess.CompletedProcess(
                argv,
                0,
                stdout="\n".join((
                    json.dumps({"type": "thread.started", "thread_id": "fixture"}),
                    json.dumps({"type": "turn.failed", "error": {"message": "native failure"}}),
                )),
                stderr="",
            ),
            version_probe=lambda integration, executable: "codex-cli 9.1",
            runtime_bootstrap_resolver=self.runtime_bootstrap,
            environment={"PATH": "/bin"},
        )
        with self.assertRaisesRegex(CapabilityExecutionError, "lifecycle reported turn.failed"):
            lifecycle(spec)

        def stale(argv, **kwargs):
            envelope = self.completion(argv)
            envelope["launch_digest"] = "sha256:" + "0" * 64
            stdout = "\n".join((
                json.dumps({"type": "thread.started", "thread_id": "fixture"}),
                json.dumps({"type": "turn.started"}),
                json.dumps({
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": json.dumps(envelope)},
                }),
                json.dumps({"type": "turn.completed", "usage": {}}),
            ))
            return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")

        with self.assertRaisesRegex(CapabilityExecutionError, "launch_digest does not match"):
            AgentProcessExecutor(
                runner=stale,
                version_probe=lambda integration, executable: "codex-cli 9.1",
                runtime_bootstrap_resolver=self.runtime_bootstrap,
                environment={"PATH": "/bin"},
            )(spec)

    @verifies("scenario.harness.execute-success")
    def test_stale_or_unenforced_configuration_prevents_process_start(self):
        calls = []
        executor = AgentProcessExecutor(
            runner=lambda *args, **kwargs: calls.append((args, kwargs)),
            version_probe=lambda integration, executable: "supported",
            environment={},
        )
        spec = self.specification("codex")
        stale_native = replace(spec.native_configuration, policy_digest="sha256:" + "0" * 64)
        with self.assertRaisesRegex(CapabilityExecutionError, "policy digest"):
            executor(replace(spec, native_configuration=stale_native))
        self.assertEqual(calls, [])

        unenforced = replace(spec.native_configuration, enforcement="unverified")
        with self.assertRaisesRegex(CapabilityExecutionError, "enforcement"):
            executor(replace(spec, native_configuration=unenforced))
        self.assertEqual(calls, [])

    @verifies("scenario.harness.execute-success", "scenario.harness.execute-failure")
    def test_version_and_process_failures_are_structured_and_do_not_retry(self):
        calls = []
        spec = self.specification("claude")
        with self.assertRaisesRegex(CapabilityExecutionError, "version preflight"):
            AgentProcessExecutor(
                runner=lambda *args, **kwargs: calls.append((args, kwargs)),
                version_probe=lambda integration, executable: "",
                environment={},
            )(spec)
        self.assertEqual(calls, [])

        def fail(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 7, stdout="", stderr="sandbox unavailable")

        with self.assertRaisesRegex(CapabilityExecutionError, "exit 7") as raised:
            AgentProcessExecutor(
                runner=fail,
                version_probe=lambda integration, executable: "claude-code 4.2",
                environment={},
            )(spec)
        self.assertEqual(len(calls), 1)
        self.assertEqual(raised.exception.receipt.exit_code, 7)
        self.assertIn("sandbox unavailable", raised.exception.receipt.limitations)


class AgentBindingPreflightTests(unittest.TestCase):
    """P2: the executor independently reverifies a structured launch's declared Agent binding,
    the harness loop timeout it receives, and the distinct cancelled/limit_exhausted/
    invalid_completion outcomes (A1, A4)."""

    def binding_and_prompt(self, agent_name):
        binding = resolve_agent(REPOSITORY_ROOT, agent_name)
        prompt_body = (REPOSITORY_ROOT / binding.instructions_path).read_text(encoding="utf-8")
        return binding, prompt_body

    def structured_specification(self, *, agent_name="planner", role=None,
                                  context_type="concorde-agent-stage-context",
                                  prompt_override=None, binding_override=None,
                                  write_roles=(), policy_effect=None):
        binding, prompt_body = self.binding_and_prompt(agent_name)
        role = role or f"concorde-{agent_name.replace('_', '-')}"
        effect = policy_effect or EffectDeclaration(
            reads=("spec-context",), writes=(), network=False, credentials="none")
        policy = compile_policy(
            effect,
            PolicyBinding(capability="concorde-plan", stage="plan", occurrence=0,
                          role=role, agent=role, write_roles=write_roles),
            {"spec-context": ("context.json",)},
        )
        native = render_claude_configuration(policy, native_enforcement=True)
        agent_binding_json = binding_override if binding_override is not None else binding_json(binding)
        if context_type == "concorde-agent-stage-context":
            runtime_input_json = self._valid_agent_stage_context_json()
        else:
            # Only used by the wrong-context-type check, which raises inside the Agent-binding
            # preflight before the launch's own full typed-data revalidation is ever reached.
            runtime_input_json = json.dumps({"type_id": context_type}, sort_keys=True, separators=(",", ":"))
        capability_configuration_json = json.dumps(
            {"type_id": "concorde-capability-configuration", "schema_version": 1,
             "data": {"integration": "claude", "enforcement": "native"}},
            sort_keys=True, separators=(",", ":"),
        )
        receipt_json = json.dumps({"source_digest": "sha256:" + "1" * 64}, sort_keys=True, separators=(",", ":"))
        return LaunchSpecification(
            capability="concorde-plan", stage="plan", occurrence=0, role=role,
            integration="claude", agent=role, project_root="/fixture/project",
            request="Plan the selected change",
            prompt=prompt_override if prompt_override is not None else prompt_body,
            prior_results=(), workspace_receipt_json=receipt_json,
            workspace_digest="sha256:" + "1" * 64, policy=policy, native_configuration=native,
            digest="sha256:" + "9" * 64,
            runtime_input_json=runtime_input_json,
            capability_configuration_json=capability_configuration_json,
            invocation_id="fixture-invocation",
            agent_binding_json=agent_binding_json,
        )

    @staticmethod
    def _unreachable_runner(test_case):
        def runner(*args, **kwargs):
            test_case.fail("runner must not be called when Agent-binding preflight fails")
        return runner

    @staticmethod
    def _valid_agent_stage_context_json():
        """A structurally complete, schema-valid ``concorde-agent-stage-context`` fixture, so a
        test can reach the launch's own full typed-data revalidation (inside
        ``finalize_launch_specification``) rather than stopping at Agent-binding preflight."""

        snapshot_data = {
            "context_id": "sha256:" + "3" * 64,
            "schema_version": 3,
            "target_id": "service.fixture",
            "kind": "module",
            "focus_id": None,
            "phase": "plan",
            "task": "Plan the selected change",
            "constraints": [],
            "protocol_binding": {"version": PROTOCOL_VERSION, "digest": "sha256:" + "4" * 64},
            "protocol": [],
            "document_order": ["specs/fixture.md"],
            "target_spec": [{
                "document_id": "document.fixture", "path": "specs/fixture.md",
                "digest": "sha256:" + "5" * 64, "targets": ["service.fixture"],
                "main_visible": True, "content": "# Fixture\n",
            }],
            "shared_specs": [],
            "instructions": "Fixture role instructions.",
            "stage_inputs": [],
            "implementation_entries": [{"path": "app/fixture.py", "entity_id": "entity.fixture.code",
                                        "pending": False, "directory": False},
                                       {"path": "app/generated/", "entity_id": "entity.fixture.code",
                                        "pending": True, "directory": True}],
            "implementation_files": [{"path": "app/fixture.py", "entity_id": "entity.fixture.code",
                                      "pending": False}],
            "implementation_artifacts": [],
            "workspace": {
                "kind": "unversioned", "current_worktree": "/fixture/project", "current_branch": None,
                "primary_worktree": None, "primary_branch": None, "change_id": None, "phase": None,
                "status": None, "outcome": None, "gaps": [], "components": [], "active_worktrees": [],
            },
        }
        runtime_value = {
            "type_id": "concorde-agent-stage-context", "schema_version": 1,
            "data": {
                "snapshot": {"type_id": "concorde-context-snapshot", "schema_version": 1, "data": snapshot_data},
                "change_id": None, "expected_artifacts": [],
            },
        }
        return json.dumps(runtime_value, sort_keys=True, separators=(",", ":"))

    @verifies("scenario.harness.execute-success")
    def test_tampered_prompt_fails_instructions_digest_check(self):
        spec = self.structured_specification(prompt_override="tampered instructions text")
        executor = AgentProcessExecutor(runner=self._unreachable_runner(self),
            version_probe=lambda *a: "claude-code 4.2", environment={"PATH": "/bin"})
        with self.assertRaisesRegex(CapabilityExecutionError, "rendered instructions"):
            executor(spec)

    @verifies("scenario.harness.execute-success")
    def test_wrong_context_and_result_type_is_refused(self):
        spec = self.structured_specification(agent_name="planner", role="concorde-planner",
            context_type="concorde-topology-author-context")
        executor = AgentProcessExecutor(runner=self._unreachable_runner(self),
            version_probe=lambda *a: "claude-code 4.2", environment={"PATH": "/bin"})
        with self.assertRaisesRegex(CapabilityExecutionError, "not declared by the bound Agent"):
            executor(spec)

    @verifies("scenario.harness.execute-success")
    def test_policy_writes_beyond_a_no_write_agent_are_refused(self):
        spec = self.structured_specification(agent_name="planner", role="concorde-planner",
            write_roles=("spec-context",),
            policy_effect=EffectDeclaration(reads=("spec-context",), writes=("spec-context",),
                                            network=False, credentials="none"))
        executor = AgentProcessExecutor(runner=self._unreachable_runner(self),
            version_probe=lambda *a: "claude-code 4.2", environment={"PATH": "/bin"})
        with self.assertRaisesRegex(CapabilityExecutionError, "writes the bound Agent does not declare"):
            executor(spec)

    @verifies("scenario.harness.execute-success")
    def test_unknown_agent_is_refused(self):
        binding, _ = self.binding_and_prompt("planner")
        tampered = dataclass_replace(binding, agent="not-a-real-agent")
        tampered = dataclass_replace(tampered, digest=binding_digest(tampered))
        spec = self.structured_specification(binding_override=binding_json(tampered))
        executor = AgentProcessExecutor(runner=self._unreachable_runner(self),
            version_probe=lambda *a: "claude-code 4.2", environment={"PATH": "/bin"})
        with self.assertRaisesRegex(CapabilityExecutionError, "unknown Agent"):
            executor(spec)

    @verifies("scenario.harness.execute-success")
    def test_wrong_harness_digest_is_refused(self):
        binding, _ = self.binding_and_prompt("planner")
        tampered = dataclass_replace(binding, harness_digest="sha256:" + "0" * 64)
        tampered = dataclass_replace(tampered, digest=binding_digest(tampered))
        spec = self.structured_specification(binding_override=binding_json(tampered))
        executor = AgentProcessExecutor(runner=self._unreachable_runner(self),
            version_probe=lambda *a: "claude-code 4.2", environment={"PATH": "/bin"})
        with self.assertRaisesRegex(CapabilityExecutionError, "Harness identity"):
            executor(spec)

    @verifies("scenario.harness.execute-success")
    def test_tampered_binding_digest_is_refused(self):
        binding, _ = self.binding_and_prompt("planner")
        payload = json.loads(binding_json(binding))
        payload["digest"] = "sha256:" + "f" * 64
        tampered_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        spec = self.structured_specification(binding_override=tampered_json)
        executor = AgentProcessExecutor(runner=self._unreachable_runner(self),
            version_probe=lambda *a: "claude-code 4.2", environment={"PATH": "/bin"})
        with self.assertRaisesRegex(CapabilityExecutionError, "digest does not match"):
            executor(spec)

    @verifies("scenario.harness.execute-failure")
    def test_runner_timeout_yields_limit_exhausted_outcome_with_binding_digest_and_no_retry(self):
        binding, _ = self.binding_and_prompt("planner")
        spec = self.structured_specification()
        calls = []

        def runner(argv, *, cwd, env, input_text, timeout):
            calls.append(timeout)
            raise subprocess.TimeoutExpired(cmd=argv, timeout=timeout)

        executor = AgentProcessExecutor(runner=runner, version_probe=lambda *a: "claude-code 4.2",
            environment={"PATH": "/bin"})
        with self.assertRaisesRegex(CapabilityExecutionError, "loop limit") as raised:
            executor(spec)
        self.assertEqual("limit_exhausted", raised.exception.outcome)
        self.assertEqual("failed", raised.exception.receipt.status)
        self.assertEqual(-1, raised.exception.receipt.exit_code)
        self.assertEqual(binding.digest, raised.exception.receipt.agent_binding_digest)
        self.assertEqual([binding.effective_loop.timeout_seconds], calls)

    @verifies("scenario.harness.execute-failure")
    def test_runner_keyboard_interrupt_yields_cancelled_outcome(self):
        spec = self.structured_specification()

        def runner(argv, *, cwd, env, input_text, timeout):
            raise KeyboardInterrupt()

        executor = AgentProcessExecutor(runner=runner, version_probe=lambda *a: "claude-code 4.2",
            environment={"PATH": "/bin"})
        with self.assertRaisesRegex(CapabilityExecutionError, "cancelled") as raised:
            executor(spec)
        self.assertEqual("cancelled", raised.exception.outcome)
        self.assertIsNone(raised.exception.receipt)

    @verifies("scenario.harness.execute-success")
    def test_successful_structured_run_carries_agent_binding_digest(self):
        binding, _ = self.binding_and_prompt("planner")
        spec = self.structured_specification()
        result_data = {"context_id": "sha256:" + "2" * 64, "outcome": "completed",
            "answer": "fixture answer", "gaps": [], "documents": [], "plan": "", "tasks": []}
        domain_output = {"type_id": "concorde-agent-stage-result", "schema_version": 1, "data": result_data}

        def runner(argv, *, cwd, env, input_text, timeout):
            self.assertEqual(binding.effective_loop.timeout_seconds, timeout)
            schema = json.loads(argv[argv.index("--json-schema") + 1])
            payload = {key: item["const"] for key, item in schema["properties"].items() if "const" in item}
            payload.update(status="success", output="fixture output", limitations="none",
                gates=[{"name": "workspace", "status": "passed", "evidence": "fixture evidence"}],
                domain_output=domain_output)
            stdout = json.dumps({"type": "result", "subtype": "success", "is_error": False,
                                 "structured_output": payload})
            return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")

        executor = AgentProcessExecutor(runner=runner, version_probe=lambda *a: "claude-code 4.2",
            environment={"PATH": "/bin"})
        result = executor(spec)
        self.assertEqual(binding.digest, result.receipt.agent_binding_digest)
        self.assertEqual(domain_output, result.completion.domain_output)


if __name__ == "__main__":
    unittest.main()

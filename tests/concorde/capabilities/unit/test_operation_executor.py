from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities.operation_executor import (  # noqa: E402
    AgentProcessExecutor,
    OperationExecutionError,
    resolve_runtime_bootstrap,
    verify_runtime_bootstrap,
)
from concorde.capabilities.operation_permissions import (  # noqa: E402
    PolicyBinding,
    build_launch_specification,
    compile_policy,
    render_claude_configuration,
    render_codex_configuration,
    runtime_bootstrap_file,
)
from concorde.capabilities.skill_assets import EffectDeclaration  # noqa: E402


class OperationExecutorTests(unittest.TestCase):
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
            "operation": properties["operation"]["const"],
            "stage": properties["stage"]["const"],
            "occurrence": properties["occurrence"]["const"],
            "capability": properties["capability"]["const"],
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
            with self.assertRaisesRegex(OperationExecutionError, "changed after attestation"):
                verify_runtime_bootstrap(files)
            executable.write_bytes(b"\x7fELFfixture-codex")

            executable.chmod(0o775)
            with self.assertRaisesRegex(OperationExecutionError, "group- or world-writable"):
                resolve_runtime_bootstrap("codex", "codex", str(project), {"PATH": str(runtime)})

            executable.write_text("#!/bin/sh\nexec node codex.js\n", encoding="utf-8")
            executable.chmod(0o755)
            with self.assertRaisesRegex(OperationExecutionError, "native executable"):
                resolve_runtime_bootstrap("codex", "codex", str(project), {"PATH": str(runtime)})

            inside = project / "codex"
            inside.write_bytes(b"\x7fELFinside")
            inside.chmod(0o755)
            with self.assertRaisesRegex(OperationExecutionError, "outside project authority"):
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
                operation="concorde-plan",
                stage="author",
                occurrence=0,
                capability="concorde-plan-author",
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
            operation="concorde-plan",
            stage="author",
            occurrence=0,
            capability="concorde-plan-author",
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

    def test_codex_process_handoff_is_injectable_scrubbed_and_receipted(self):
        calls = []

        def runner(argv, *, cwd, env, input_text):
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

    def test_claude_process_handoff_uses_inline_strict_settings_and_no_retry(self):
        calls = []

        def runner(argv, *, cwd, env, input_text):
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
        self.assertIn("--output-format", argv)
        self.assertIn("Use bounded context", input_text)
        self.assertEqual(result.output, "claude-result")

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
        with self.assertRaisesRegex(OperationExecutionError, "reported failed completion") as raised:
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
        with self.assertRaisesRegex(OperationExecutionError, "invalid capability completion") as malformed_error:
            malformed(spec)
        self.assertEqual(malformed_error.exception.receipt.status, "failed")

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
        with self.assertRaisesRegex(OperationExecutionError, "lifecycle reported turn.failed"):
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

        with self.assertRaisesRegex(OperationExecutionError, "launch_digest does not match"):
            AgentProcessExecutor(
                runner=stale,
                version_probe=lambda integration, executable: "codex-cli 9.1",
                runtime_bootstrap_resolver=self.runtime_bootstrap,
                environment={"PATH": "/bin"},
            )(spec)

    def test_stale_or_unenforced_configuration_prevents_process_start(self):
        calls = []
        executor = AgentProcessExecutor(
            runner=lambda *args, **kwargs: calls.append((args, kwargs)),
            version_probe=lambda integration, executable: "supported",
            environment={},
        )
        spec = self.specification("codex")
        stale_native = replace(spec.native_configuration, policy_digest="sha256:" + "0" * 64)
        with self.assertRaisesRegex(OperationExecutionError, "policy digest"):
            executor(replace(spec, native_configuration=stale_native))
        self.assertEqual(calls, [])

        unenforced = replace(spec.native_configuration, enforcement="unverified")
        with self.assertRaisesRegex(OperationExecutionError, "enforcement"):
            executor(replace(spec, native_configuration=unenforced))
        self.assertEqual(calls, [])

    def test_version_and_process_failures_are_structured_and_do_not_retry(self):
        calls = []
        spec = self.specification("claude")
        with self.assertRaisesRegex(OperationExecutionError, "version preflight"):
            AgentProcessExecutor(
                runner=lambda *args, **kwargs: calls.append((args, kwargs)),
                version_probe=lambda integration, executable: "",
                environment={},
            )(spec)
        self.assertEqual(calls, [])

        def fail(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 7, stdout="", stderr="sandbox unavailable")

        with self.assertRaisesRegex(OperationExecutionError, "exit 7") as raised:
            AgentProcessExecutor(
                runner=fail,
                version_probe=lambda integration, executable: "claude-code 4.2",
                environment={},
            )(spec)
        self.assertEqual(len(calls), 1)
        self.assertEqual(raised.exception.receipt.exit_code, 7)
        self.assertIn("sandbox unavailable", raised.exception.receipt.limitations)


if __name__ == "__main__":
    unittest.main()

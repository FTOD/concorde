from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError, replace

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities.operation_executor import (  # noqa: E402
    AgentProcessExecutor,
    OperationExecutionError,
)
from concorde.capabilities.operation_permissions import (  # noqa: E402
    PolicyBinding,
    build_launch_specification,
    compile_policy,
    render_claude_configuration,
    render_codex_configuration,
)
from concorde.capabilities.skill_assets import EffectDeclaration  # noqa: E402


class OperationExecutorTests(unittest.TestCase):
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
            workspace_digest="sha256:" + "1" * 64,
            policy=policy,
            native_configuration=native,
        )

    def test_codex_process_handoff_is_injectable_scrubbed_and_receipted(self):
        calls = []

        def runner(argv, *, cwd, env, input_text):
            calls.append((argv, cwd, env, input_text))
            return subprocess.CompletedProcess(argv, 0, stdout="codex-result\n", stderr="")

        executor = AgentProcessExecutor(
            runner=runner,
            version_probe=lambda integration, executable: "codex-cli 9.1",
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
        self.assertEqual(argv[:2], ("codex", "exec"))
        self.assertNotIn("--sandbox", argv)
        self.assertEqual(cwd, "/fixture/project")
        self.assertEqual(env, {"LANG": "C.UTF-8", "PATH": "/bin"})
        self.assertIn("Plan the selected change", input_text)
        self.assertIn("context:ready", input_text)
        self.assertEqual(result.output, "codex-result")
        self.assertEqual(result.receipt.policy_digest, spec.policy.digest)
        self.assertEqual(result.receipt.config_digest, spec.native_configuration.digest)
        self.assertEqual(result.receipt.launch_digest, spec.digest)
        self.assertEqual(result.receipt.client_version, "codex-cli 9.1")
        self.assertEqual(result.receipt.enforcement, "native")
        with self.assertRaises(FrozenInstanceError):
            result.output = "changed"  # type: ignore[misc]

    def test_claude_process_handoff_uses_inline_strict_settings_and_no_retry(self):
        calls = []

        def runner(argv, *, cwd, env, input_text):
            calls.append((argv, input_text))
            return subprocess.CompletedProcess(argv, 0, stdout="claude-result", stderr="")

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
        self.assertIn("Use bounded context", input_text)
        self.assertEqual(result.output, "claude-result")

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

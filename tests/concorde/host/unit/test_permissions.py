from __future__ import annotations

import json
import errno
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.host.permissions import (  # noqa: E402
    PermissionPolicyError,
    PolicyBinding,
    build_launch_specification,
    compare_effective_boundaries,
    compile_policy,
    finalize_codex_configuration,
    finalize_launch_specification,
    render_claude_configuration,
    render_codex_configuration,
    runtime_bootstrap_file,
    verify_effective_subset,
)
from concorde.host.agent_model import binding_json, resolve_agent  # noqa: E402
from concorde.host.effects import EffectDeclaration  # noqa: E402
from concorde.host.typed_data import canonical, typed  # noqa: E402


class PermissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.effect = EffectDeclaration(
            reads=("selected-feature", "module-architecture", "required-feature-specs", "attempt"),
            writes=("attempt",),
            network=False,
            credentials="none",
        )
        self.roles = {
            "attempt": (".concorde/attempts/feature.example.change",),
            "required-feature-specs": ("specs/provider/features/001-api.md",),
            "module-architecture": ("specs/consumer/architecture.md",),
            "selected-feature": ("specs/consumer/features/001-change.md",),
        }
        self.binding = PolicyBinding(
            capability="concorde-plan",
            stage="author",
            occurrence=0,
            role="concorde-plan-author",
            agent="plan-author",
        )

    def test_normalized_policy_is_frozen_canonical_and_deny_by_default(self):
        policy = compile_policy(self.effect, self.binding, self.roles)
        self.assertEqual(
            policy.read_paths,
            (
                ".concorde/attempts/feature.example.change",
                "specs/consumer/architecture.md",
                "specs/consumer/features/001-change.md",
                "specs/provider/features/001-api.md",
            ),
        )
        self.assertEqual(policy.write_paths, (".concorde/attempts/feature.example.change",))
        self.assertTrue(policy.default_deny)
        self.assertFalse(policy.network_enabled)
        self.assertEqual(policy.credentials, "none")
        self.assertRegex(policy.digest, r"^sha256:[0-9a-f]{64}$")
        reordered = compile_policy(self.effect, self.binding, dict(reversed(tuple(self.roles.items()))))
        self.assertEqual(reordered.digest, policy.digest)
        with self.assertRaises(FrozenInstanceError):
            policy.network_enabled = True  # type: ignore[misc]

    def test_binding_can_narrow_but_never_widen_leaf_effects(self):
        narrowed = replace(
            self.binding,
            read_roles=("selected-feature", "attempt"),
            write_roles=(),
        )
        policy = compile_policy(self.effect, narrowed, self.roles)
        self.assertEqual(
            policy.read_paths,
            (".concorde/attempts/feature.example.change", "specs/consumer/features/001-change.md"),
        )
        self.assertEqual(policy.write_paths, ())

        with self.assertRaisesRegex(PermissionPolicyError, "widens read roles"):
            compile_policy(
                self.effect,
                replace(self.binding, read_roles=("selected-feature", "owned-implementation")),
                {**self.roles, "owned-implementation": ("src/consumer.py",)},
            )
        with self.assertRaisesRegex(PermissionPolicyError, "write roles"):
            compile_policy(
                self.effect,
                replace(self.binding, write_roles=("selected-feature",)),
                self.roles,
            )
        with self.assertRaisesRegex(PermissionPolicyError, "unknown path role"):
            compile_policy(self.effect, self.binding, {"selected-feature": self.roles["selected-feature"]})
        with self.assertRaisesRegex(PermissionPolicyError, "network"):
            compile_policy(self.effect, replace(self.binding, network=True), self.roles)

    def test_codex_and_claude_render_equivalent_effective_boundaries(self):
        policy = compile_policy(self.effect, self.binding, self.roles)
        codex = render_codex_configuration(policy, native_enforcement=True)
        claude = render_claude_configuration(policy, native_enforcement=True)

        self.assertTrue(codex.permission_profile.startswith("concorde-"))
        self.assertEqual(codex.approval_policy, "never")
        self.assertEqual(
            codex.argv[:4],
            ("codex", "--ask-for-approval", "never", "exec"),
        )
        self.assertNotIn("--sandbox", codex.argv)
        self.assertIn("default_permissions", " ".join(codex.argv))
        self.assertTrue(codex.strict_config)

        overrides = tuple(
            codex.argv[index + 1]
            for index, value in enumerate(codex.argv)
            if value == "-c"
        )
        override_keys = tuple(value.split("=", 1)[0] for value in overrides)
        self.assertEqual(
            override_keys,
            (
                "project_doc_max_bytes",
                "default_permissions",
                "approval_policy",
                f"permissions.{codex.permission_profile}",
                "features.network_proxy",
                "features.multi_agent",
                "features.multi_agent_v2",
            ),
        )
        self.assertEqual(codex.configuration["project_doc_max_bytes"], 0)
        self.assertIn("project_doc_max_bytes=0", overrides)
        profile_override = overrides[3].split("=", 1)[1]
        parsed_profile = tomllib.loads(f"profile={profile_override}")["profile"]
        expected_profile = codex.configuration["permissions"][codex.permission_profile]
        self.assertEqual(parsed_profile, expected_profile)
        self.assertEqual(expected_profile["workspace_roots"], {".": True})
        filesystem = expected_profile["filesystem"]
        self.assertEqual(
            {key: filesystem[key] for key in (":root", ":minimal")},
            {":root": "deny", ":minimal": "read"},
        )
        self.assertNotIn(":tmpdir", filesystem)
        self.assertNotIn(":slash_tmp", filesystem)
        workspace_rules = filesystem[":workspace_roots"]
        self.assertEqual(workspace_rules[".concorde/attempts/feature.example.change"], "write")
        self.assertEqual(workspace_rules["specs/consumer/architecture.md"], "read")
        self.assertNotIn(":root", workspace_rules)
        for path in (*policy.read_paths, *policy.write_paths, *policy.deny_paths):
            self.assertTrue(all(path not in key for key in override_keys), path)
        self.assertEqual(
            render_codex_configuration(policy, native_enforcement=True).argv,
            codex.argv,
        )

        bootstrap = runtime_bootstrap_file(
            path="/opt/codex/bin/codex",
            sha256="sha256:" + "b" * 64,
            size=8192,
            mode=0o755,
            owner=0,
        )
        finalized = finalize_codex_configuration(codex, (bootstrap,))
        finalized_profile = finalized.configuration["permissions"][finalized.permission_profile]
        self.assertEqual(finalized_profile["filesystem"][bootstrap.path], "read")
        self.assertNotIn(bootstrap.path, finalized_profile["filesystem"][":workspace_roots"])
        self.assertEqual(finalized.runtime_bootstrap, (bootstrap,))
        self.assertEqual(finalized.argv[0], bootstrap.path)
        self.assertNotEqual(finalized.digest, codex.digest)
        self.assertTrue(compare_effective_boundaries(finalized, claude))
        with self.assertRaisesRegex(PermissionPolicyError, "exactly one"):
            finalize_codex_configuration(codex, ())
        with self.assertRaisesRegex(PermissionPolicyError, "exactly one"):
            finalize_codex_configuration(codex, (bootstrap, bootstrap))
        with self.assertRaisesRegex(PermissionPolicyError, "sha256 must be canonical"):
            runtime_bootstrap_file(
                path=bootstrap.path,
                sha256="sha256:" + "B" * 64,
                size=bootstrap.size,
                mode=bootstrap.mode,
                owner=bootstrap.owner,
            )

        settings = json.loads(claude.settings_json)
        self.assertEqual(settings["permissions"]["defaultMode"], "dontAsk")
        self.assertTrue(settings["sandbox"]["enabled"])
        self.assertTrue(settings["sandbox"]["failIfUnavailable"])
        self.assertFalse(settings["sandbox"]["allowUnsandboxedCommands"])
        self.assertEqual(settings["sandbox"]["network"]["allowedDomains"], [])
        self.assertTrue(compare_effective_boundaries(codex, claude))

    @unittest.skipUnless(shutil.which("codex"), "Codex CLI is not installed")
    def test_codex_launch_argv_loads_configuration_in_installed_cli_without_a_model(self):
        policy = compile_policy(self.effect, self.binding, self.roles)
        codex = render_codex_configuration(policy, native_enforcement=True)

        result = subprocess.run(
            codex.argv,
            input="",
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )

        diagnostic = result.stderr or result.stdout
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No prompt provided via stdin", diagnostic)
        self.assertNotIn("Error loading config.toml", diagnostic)
        self.assertNotIn("invalid type", diagnostic)

    @unittest.skipUnless(sys.platform == "linux" and shutil.which("codex") and Path("/usr/bin/python3").exists(),
                         "Native Linux Codex sandbox is not installed")
    def test_native_review_grants_allow_owned_reads_and_protect_host_files(self):
        from concorde.host.agent_executor import resolve_runtime_bootstrap
        probe = '''import json, os, socket, sys
from pathlib import Path
root = Path(sys.argv[1]); result = {"cwd": os.getcwd()}
for relative in ("context.json", "app/allowed.py", "app/sibling.py", "specs/provider.md", "../foreign.py"):
    try:
        (root / relative).read_bytes(); result["read:" + relative] = True
    except OSError as error:
        result["read:" + relative] = error.errno
for relative in ("context.json", "app/allowed.py", "specs/provider.md", "app/new.py"):
    try:
        (root / relative).write_text("attempted write"); result["write:" + relative] = True
    except OSError as error:
        result["write:" + relative] = error.errno
try:
    connection = socket.socket(); connection.connect(("127.0.0.1", 9)); result["network"] = True
except OSError as error:
    result["network"] = error.errno
print(json.dumps(result))
'''
        with tempfile.TemporaryDirectory(prefix="concorde-native-review-") as directory:
            root = Path(directory) / "project"
            root.mkdir()
            (root.parent / "foreign.py").write_text("foreign fixture")
            files = ("context.json", "app/allowed.py", "app/sibling.py", "specs/provider.md")
            for relative in files:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("original fixture")
            for mode in ("spec", "code"):
                with self.subTest(mode=mode):
                    reads = ("spec-context",) if mode == "spec" else ("spec-context", "implementation")
                    policy = compile_policy(EffectDeclaration(reads, (), False, "none"),
                        PolicyBinding("concorde-review", mode + "-review", 0, "reviewer", "reviewer"),
                        {"spec-context": ("context.json",), "implementation": ("app/allowed.py",)})
                    native = finalize_codex_configuration(render_codex_configuration(policy, native_enforcement=True),
                        resolve_runtime_bootstrap("codex", "codex", str(root), os.environ))
                    options = [part for index, argument in enumerate(native.argv) if argument == "-c"
                               for part in ("-c", native.argv[index + 1])]
                    process = subprocess.run((native.argv[0], "sandbox", "-P", native.permission_profile,
                        "-C", str(root), *options, "--", "/usr/bin/python3", "-c", probe, str(root)),
                        cwd=root, capture_output=True, text=True, timeout=30)
                    self.assertEqual(0, process.returncode, process.stderr)
                    result = json.loads(process.stdout)
                    self.assertEqual(str(root), result["cwd"])
                    self.assertIs(result["read:context.json"], True)
                    if mode == "code":
                        self.assertIs(result["read:app/allowed.py"], True)
                    else:
                        self.assertIsNot(result["read:app/allowed.py"], True)
                    for relative in ("app/sibling.py", "specs/provider.md", "../foreign.py"):
                        self.assertIsNot(result["read:" + relative], True)
                    for relative in ("context.json", "app/allowed.py", "specs/provider.md"):
                        self.assertIsNot(result["write:" + relative], True)
                    self.assertIsNot(result["network"], True)
                    self.assertIn(result["network"], (errno.EPERM, errno.EACCES))
                    for relative in files:
                        self.assertEqual("original fixture", (root / relative).read_text())
                    # A native private directory scaffold can host disposable scratch;
                    # it must never create a file in the actual project filesystem.
                    self.assertFalse((root / "app/new.py").exists())
                    self.assertEqual("foreign fixture", (root.parent / "foreign.py").read_text())

    def test_unavailable_native_enforcement_requires_verified_outer_boundary(self):
        policy = compile_policy(self.effect, self.binding, self.roles)
        with self.assertRaisesRegex(PermissionPolicyError, "Codex.*enforcement"):
            render_codex_configuration(policy, native_enforcement=False)
        with self.assertRaisesRegex(PermissionPolicyError, "Claude.*sandbox"):
            render_claude_configuration(policy, native_enforcement=False)

        codex = render_codex_configuration(
            policy,
            native_enforcement=False,
            outer_sandbox="test-outer",
        )
        claude = render_claude_configuration(
            policy,
            native_enforcement=False,
            outer_sandbox="test-outer",
        )
        self.assertEqual((codex.enforcement, claude.enforcement), ("outer", "outer"))
        self.assertTrue(compare_effective_boundaries(codex, claude))

    def test_managed_or_user_configuration_may_only_narrow(self):
        declared = compile_policy(self.effect, self.binding, self.roles)
        narrower = replace(
            declared,
            read_paths=("specs/consumer/features/001-change.md",),
            write_paths=(),
        )
        verify_effective_subset(declared, narrower)
        with self.assertRaisesRegex(PermissionPolicyError, "widens"):
            verify_effective_subset(
                declared,
                replace(declared, read_paths=(*declared.read_paths, "src/provider/private.py")),
            )


class AgentBindingLaunchTests(unittest.TestCase):
    """A structured launch must carry the resolved Agent binding that authorized it (P2)."""

    def setUp(self) -> None:
        self.binding = resolve_agent(REPOSITORY_ROOT, "spec_author")
        self.effect = EffectDeclaration(reads=("spec-context",), writes=(), network=False, credentials="none")
        self.roles = {"spec-context": ("context.json",)}
        self.policy = compile_policy(
            self.effect,
            PolicyBinding(
                capability="concorde-specify", stage="specify", occurrence=0,
                role="concorde-spec-author", agent="concorde-spec-author", write_roles=(),
            ),
            self.roles,
        )
        self.native = render_claude_configuration(self.policy, native_enforcement=True)
        self.configuration = typed("concorde-capability-configuration", {"integration": "claude", "enforcement": "native"})

    def build(self, **overrides):
        kwargs = dict(
            capability="concorde-specify",
            stage="specify",
            occurrence=0,
            role="concorde-spec-author",
            integration="claude",
            agent="concorde-spec-author",
            project_root="/fixture/project",
            request="Author the Spec",
            prompt="# fixture spec-author instructions",
            prior_results=(),
            workspace_receipt_json=json.dumps(
                {"source_digest": "sha256:" + "1" * 64}, sort_keys=True, separators=(",", ":")
            ),
            workspace_digest="sha256:" + "1" * 64,
            policy=self.policy,
            native_configuration=self.native,
            runtime_input_json=canonical(self.configuration),
            capability_configuration_json=canonical(self.configuration),
            invocation_id="fixture-invocation",
        )
        kwargs.update(overrides)
        return build_launch_specification(**kwargs)

    def test_structured_launch_without_agent_binding_is_refused(self):
        with self.assertRaisesRegex(PermissionPolicyError, "resolved Agent binding"):
            self.build()

    def test_narrative_launch_cannot_carry_an_agent_binding(self):
        with self.assertRaises(PermissionPolicyError):
            self.build(
                agent_binding_json=binding_json(self.binding),
                runtime_input_json=None,
                capability_configuration_json=None,
                invocation_id=None,
            )

    def test_agent_binding_field_set_and_canonical_serialization_are_enforced(self):
        with self.assertRaisesRegex(PermissionPolicyError, "AgentBinding fields"):
            self.build(agent_binding_json=json.dumps({"agent": "spec_author"}, sort_keys=True, separators=(",", ":")))
        with self.assertRaisesRegex(PermissionPolicyError, "canonical serialization"):
            self.build(agent_binding_json=binding_json(self.binding) + " ")

    def test_agent_binding_participates_in_the_launch_digest(self):
        with_binding = self.build(agent_binding_json=binding_json(self.binding))
        other_binding = resolve_agent(REPOSITORY_ROOT, "reader")
        different_binding = self.build(agent_binding_json=binding_json(other_binding))
        self.assertNotEqual(with_binding.digest, different_binding.digest)
        self.assertEqual(with_binding.agent_binding_json, binding_json(self.binding))

    def test_finalize_launch_specification_preserves_the_agent_binding(self):
        spec = self.build(agent_binding_json=binding_json(self.binding))
        finalized = finalize_launch_specification(spec, ())
        self.assertEqual(spec.agent_binding_json, finalized.agent_binding_json)
        self.assertEqual(spec.digest, finalized.digest)


if __name__ == "__main__":
    unittest.main()

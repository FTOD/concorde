from __future__ import annotations

import json
import sys
import unittest
from dataclasses import FrozenInstanceError, replace

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities.operation_permissions import (  # noqa: E402
    PermissionPolicyError,
    PolicyBinding,
    compare_effective_boundaries,
    compile_policy,
    render_claude_configuration,
    render_codex_configuration,
    verify_effective_subset,
)
from concorde.capabilities.skill_assets import EffectDeclaration  # noqa: E402


class OperationPermissionTests(unittest.TestCase):
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
            operation="concorde-plan",
            stage="author",
            occurrence=0,
            capability="concorde-plan-author",
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
        self.assertNotIn("--sandbox", codex.argv)
        self.assertIn("default_permissions", " ".join(codex.argv))
        self.assertTrue(codex.strict_config)

        settings = json.loads(claude.settings_json)
        self.assertEqual(settings["permissions"]["defaultMode"], "dontAsk")
        self.assertTrue(settings["sandbox"]["enabled"])
        self.assertTrue(settings["sandbox"]["failIfUnavailable"])
        self.assertFalse(settings["sandbox"]["allowUnsandboxedCommands"])
        self.assertEqual(settings["sandbox"]["network"]["allowedDomains"], [])
        self.assertTrue(compare_effective_boundaries(codex, claude))

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


if __name__ == "__main__":
    unittest.main()

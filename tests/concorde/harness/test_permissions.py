from __future__ import annotations

import sys
import unittest
from dataclasses import FrozenInstanceError, replace

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.harness.effects import EffectDeclaration  # noqa: E402
from concorde.harness.permissions import (  # noqa: E402
    PermissionPolicyError,
    PolicyBinding,
    compile_policy,
    verify_effective_subset,
)
from concorde.spec.verification import verifies  # noqa: E402


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

    @verifies("scenario.harness.permission-compile")
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

    @verifies("scenario.harness.permission-compile", "scenario.harness.permission-reject")
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

    @verifies("scenario.harness.permission-reject")
    def test_unsafe_paths_and_widened_effective_policies_are_rejected(self):
        for path in ("/etc/passwd", "../outside", "specs/../../outside"):
            with self.subTest(path=path), self.assertRaises(PermissionPolicyError):
                compile_policy(self.effect, self.binding, {**self.roles, "selected-feature": (path,)})
        declared = compile_policy(self.effect, self.binding, self.roles)
        narrowed = compile_policy(self.effect, replace(self.binding, write_roles=()), self.roles)
        verify_effective_subset(declared, narrowed)
        with self.assertRaises(PermissionPolicyError):
            verify_effective_subset(narrowed, declared)
        with self.assertRaises(PermissionPolicyError):
            verify_effective_subset(declared, replace(declared, read_paths=(*declared.read_paths, "secret.py")))


if __name__ == "__main__":
    unittest.main()

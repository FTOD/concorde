"""The build renders the Pi session entry: its catalog, guidance and launcher paths."""

from __future__ import annotations

import sys
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution.build import build  # noqa: E402
from concorde.distribution.build import (  # noqa: E402
    PI_SESSION_SHIM as INSTALLED_PI_SESSION_SHIM,
)
from concorde.distribution.build import (  # noqa: E402
    PRIVATE_PI_SESSION_SHIM as PI_SESSION_SHIM,
)
from concorde.operations.catalog import PUBLIC_OPERATIONS  # noqa: E402
from concorde.spec.typed_data import json_schema  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402
from tests.concorde.support.session_catalog import shim_catalog  # noqa: E402

GOLDEN = REPOSITORY_ROOT / "tests/concorde/fixtures/build/golden/pi/concorde-session.ts"


class ShimRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checkout = {o.path: o for o in build(REPOSITORY_ROOT).outputs}
        cls.installed = {
            o.path: o
            for o in build(
                REPOSITORY_ROOT, framework_prefix=".concorde/framework"
            ).outputs
        }

    @verifies("scenario.distribution.build-pi-session")
    def test_the_pi_integration_renders_one_shim_and_no_skills(self):
        projected = [
            path for path in self.checkout if path.startswith("generated/session/")
        ]
        self.assertEqual([PI_SESSION_SHIM], projected)

    @verifies(
        "scenario.distribution.build-pi-session",
        "scenario.distribution.private-session-entry",
    )
    def test_checkout_shim_binds_the_tracked_extension_and_waits_for_explicit_requests(
        self,
    ):
        content = self.checkout[PI_SESSION_SHIM].content
        text = content.decode("utf-8")
        self.assertIn('from "../../../pi/extensions/concorde-session.ts"', text)
        self.assertIn('new URL("../../../", import.meta.url)', text)
        catalog = shim_catalog(content)
        self.assertEqual(3, catalog["schema_version"])
        self.assertTrue(catalog["explicit_request_only"])
        self.assertEqual("scripts/run-operation.py", catalog["launcher"])
        self.assertEqual(
            [".venv/bin/python", ".venv/Scripts/python.exe"], catalog["interpreters"]
        )
        self.assertEqual(
            list(PUBLIC_OPERATIONS), [o["name"] for o in catalog["operations"]]
        )
        for operation in catalog["operations"]:
            with self.subTest(operation=operation["name"]):
                schema = json_schema(f"{operation['name']}-request")
                self.assertEqual(schema, operation["request_schema"])
                self.assertEqual(
                    schema["properties"]["schema_version"]["const"],
                    operation["request_version"],
                )
                self.assertTrue(operation["description"].strip())
                self.assertTrue(
                    operation["guidance"].startswith(f"# {operation['name']}\n")
                )
                self.assertNotIn("stdin", operation["guidance"])
                self.assertNotIn("{OPERATION}", operation["guidance"])
                self.assertNotIn("\n\n\n", operation["guidance"])
        # The session path of every capability comes from the Operation catalog and hooks.
        self.assertEqual(
            {
                "concorde-context-solve": ("agent-entry", []),
                "concorde-plan": ("workflow", []),
                "concorde-tasks": ("agent-entry", []),
                "concorde-implement": ("agent-entry", []),
                "concorde-spec-review": ("workflow", []),
                "concorde-code-review": ("workflow", []),
                "concorde-issues": ("host", ["solve"]),
                "concorde-validate": ("host", []),
                "concorde-deliver": ("host", []),
                "concorde-init": ("host", []),
                "concorde-configure": ("host", []),
            },
            {
                o["name"]: (o["kind"], o["native_actions"])
                for o in catalog["operations"]
            },
        )

    @verifies("scenario.distribution.build-pi-session")
    def test_public_descriptions_name_execution_kinds_not_generic_operations(self):
        prefixes = {
            "concorde-context-solve": "Agent entry:",
            "concorde-tasks": "Agent entry:",
            "concorde-implement": "Agent entry:",
            "concorde-plan": "Workflow:",
            "concorde-spec-review": "Workflow:",
            "concorde-code-review": "Workflow:",
            "concorde-init": "Host service:",
            "concorde-configure": "Host service:",
            "concorde-validate": "Host service:",
            "concorde-deliver": "Host service:",
            "concorde-issues": "Host bookkeeping or native solve workflow:",
        }
        for content in (
            self.checkout[PI_SESSION_SHIM].content,
            self.installed[INSTALLED_PI_SESSION_SHIM].content,
        ):
            catalog = shim_catalog(content)
            self.assertEqual(set(prefixes), {o["name"] for o in catalog["operations"]})
            for entry in catalog["operations"]:
                with self.subTest(entry=entry["name"]):
                    self.assertTrue(
                        entry["description"].startswith(prefixes[entry["name"]])
                    )
                    self.assertNotIn("other Operations", entry["guidance"])
                    self.assertNotIn("poll this same operation", entry["guidance"])
                    for obsolete in (
                        "Invoke this operation",
                        "deterministic lifecycle operation",
                        "public Operations",
                        "Operation workers",
                        "scheduled by the Graph/host",
                        "Non-implementation workers never receive",
                    ):
                        self.assertNotIn(obsolete, entry["guidance"])
                    self.assertEqual(
                        json_schema(f"{entry['name']}-request"), entry["request_schema"]
                    )

    @verifies(
        "scenario.distribution.build-pi-session",
        "scenario.distribution.private-session-entry",
    )
    def test_installed_shim_points_below_the_framework_prefix(self):
        content = self.installed[INSTALLED_PI_SESSION_SHIM].content
        self.assertIn(
            'from "../../.concorde/framework/pi/extensions/concorde-session.ts"',
            content.decode("utf-8"),
        )
        catalog = shim_catalog(content)
        self.assertFalse(catalog["explicit_request_only"])
        self.assertEqual(
            ".concorde/framework/scripts/run-operation.py", catalog["launcher"]
        )
        self.assertEqual(
            [".concorde/.venv/bin/python", ".concorde/.venv/Scripts/python.exe"],
            catalog["interpreters"],
        )

    @verifies("scenario.distribution.build-render")
    def test_shim_matches_golden_bytes_exactly(self):
        self.assertEqual(GOLDEN.read_bytes(), self.checkout[PI_SESSION_SHIM].content)

    @verifies("scenario.distribution.build-pi-session")
    def test_guidance_sources_have_no_standalone_invocation_mechanics(self):
        sources = self.checkout[PI_SESSION_SHIM].sources
        self.assertEqual(
            11, sum(s.startswith("prompts/operation-guidance/") for s in sources)
        )
        self.assertFalse(
            any("stdin-invocation" in s or "prompts/skills/" in s for s in sources)
        )
        catalog = shim_catalog(self.checkout[PI_SESSION_SHIM].content)
        issues = next(
            o for o in catalog["operations"] if o["name"] == "concorde-issues"
        )
        self.assertIn(
            "Solve returns needed implementation or Spec repair to the calling agent",
            issues["guidance"],
        )
        self.assertIn(
            "A return-to-caller result preserves the open Issue", issues["guidance"]
        )


if __name__ == "__main__":
    unittest.main()

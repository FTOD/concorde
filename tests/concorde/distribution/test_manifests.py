from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.spec.verification import verifies
from tests.concorde.support.managed_runtime import (
    create_langgraph_index,
    runtime_install_environment,
)
from tests.concorde.support.paths import REPOSITORY_ROOT


class ManifestContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())

    def test_one_manifest_declares_native_identity_profile_and_install_layout(self):
        manifest = self.manifest
        self.assertEqual(manifest["schema_version"], 5)
        self.assertEqual((manifest["name"], manifest["version"]), ("concorde", "8.0.0"))
        self.assertEqual(
            (manifest["architecture_profile"], manifest["workspace_protocol"]), (15, 16)
        )
        self.assertEqual(manifest["client"], "pi")
        self.assertNotIn("integrations", manifest)
        self.assertNotIn("skill_namespace", manifest)
        self.assertNotIn("skills", manifest["package_roots"])
        self.assertEqual(
            manifest["install"],
            {
                "framework_root": ".concorde/framework",
                "receipt": ".concorde/install.json",
            },
        )
        self.assertEqual(
            manifest["runtime"],
            {
                "launcher": "scripts/run-operation.py",
                "python": ">=3.11",
                "requirements": "scripts/requirements.lock",
                "venv": ".concorde/.venv",
            },
        )
        self.assertNotIn("viewer", manifest)

    @verifies("scenario.distribution.template-ownership")
    def test_templates_live_only_in_their_owning_packages(self):
        self.assertNotIn("templates", self.manifest)
        self.assertNotIn("templates", self.manifest["package_roots"])
        self.assertFalse((REPOSITORY_ROOT / "templates").exists())
        for relative in (
            "protocol/templates/module.md",
            "protocol/templates/scenario.md",
            "operations/planner/plan-template.md",
            "operations/task_author/tasks-template.md",
        ):
            self.assertTrue((REPOSITORY_ROOT / relative).is_file(), relative)
        for owner, template in (
            ("planner", "plan-template.md"),
            ("task_author", "tasks-template.md"),
        ):
            readme = (REPOSITORY_ROOT / "operations" / owner / "README.md").read_text()
            self.assertIn(f"]({template})", readme)

    def test_runtime_reads_version_from_the_single_manifest(self):
        sys.path.insert(0, str(REPOSITORY_ROOT / "src"))
        try:
            import concorde

            self.assertEqual(concorde.__version__, self.manifest["version"])
        finally:
            sys.path.pop(0)

    def test_manifest_inventory_equals_root_operations(self):
        sys.path.insert(0, str(REPOSITORY_ROOT / "src"))
        sys.path.insert(0, str(REPOSITORY_ROOT))
        try:
            from concorde.distribution.build import PUBLIC_OPERATIONS
            from concorde.harness.worker_profile import load_worker_profiles
            from concorde.spec.contracts import load_operation_inventory
        finally:
            sys.path.pop(0)
            sys.path.pop(0)
        operations = load_operation_inventory()
        launcher = ast.parse((REPOSITORY_ROOT / "scripts/run-operation.py").read_text())
        launcher_operations = next(
            ast.literal_eval(node.value)
            for node in launcher.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "PUBLIC_OPERATIONS"
                for target in node.targets
            )
        )
        self.assertEqual(set(PUBLIC_OPERATIONS), set(launcher_operations))
        self.assertEqual(
            (
                len(load_worker_profiles()),
                len(operations.OPERATIONS),
                len(PUBLIC_OPERATIONS),
            ),
            (7, 18, 11),
        )
        self.assertEqual(
            (REPOSITORY_ROOT / "scripts/requirements.lock").read_text(),
            "langgraph==1.2.11\n",
        )
        self.assertTrue((REPOSITORY_ROOT / "scripts/run-operation.py").is_file())

    def test_issue_reporting_replaces_the_reflection_template_and_triage(self):
        from concorde.spec.contracts import OPERATION_NAMES
        from concorde.spec.issue_shapes import REPORT

        self.assertEqual(
            ["bug", "gap", "limitation"], REPORT["properties"]["type"]["enum"]
        )
        self.assertFalse(
            {"source", "status", "human_intervention", "action"}
            & REPORT["properties"].keys()
        )
        self.assertIn("concorde-issues", OPERATION_NAMES)
        self.assertNotIn("concorde-reflections-triage", OPERATION_NAMES)
        self.assertFalse(
            (REPOSITORY_ROOT / "templates/reflections-template.md").exists()
        )
        self.assertFalse((REPOSITORY_ROOT / "scripts/reflections_queue.py").exists())

    def test_removed_host_package_layout_is_absent(self):
        for relative in (".specify", "presets", "extensions", "bundles", "catalogs"):
            self.assertFalse((REPOSITORY_ROOT / relative).exists(), relative)
        self.assertFalse((REPOSITORY_ROOT / "docsite/sidebars.docs.ts").exists())
        serialized = json.dumps(self.manifest).lower()
        for key in ("speckit_version", "bundle_id", "install_policy"):
            self.assertNotIn(key, serialized)

    @verifies("scenario.distribution.install-apply")
    def test_native_source_install_materializes_framework_and_operations(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            environment = runtime_install_environment(
                create_langgraph_index(target.parent)
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPOSITORY_ROOT / "scripts/install-concorde.py"),
                    "--target",
                    str(target),
                    "--apply",
                    "--format",
                    "json",
                ],
                text=True,
                capture_output=True,
                env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "installed")
            self.assertTrue((target / ".concorde/framework/concorde.json").is_file())
            self.assertTrue(
                (
                    target / ".concorde/framework/src/concorde/harness/admission.py"
                ).is_file()
            )
            self.assertTrue(
                (target / ".concorde/framework/scripts/run-operation.py").is_file()
            )
            self.assertTrue(
                (target / ".concorde/framework/generated/build-manifest.json").is_file()
            )
            self.assertTrue((target / ".concorde/framework/operations").is_dir())
            self.assertFalse((target / ".concorde/framework/capabilities").exists())
            self.assertTrue((target / ".pi/extensions/concorde-session.ts").is_file())
            self.assertFalse((target / ".agents").exists())
            self.assertFalse((target / ".claude").exists())
            self.assertFalse((target / "skills-lock.json").exists())
            self.assertFalse(
                (target / ".concorde/framework/docsite/sidebars.docs.ts").exists()
            )
            self.assertFalse((target / ".specify").exists())

            # The host in the consumer must pass the freshness check without ever building itself.
            check = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.path.insert(0, '.concorde/framework/src'); "
                    "from concorde.distribution.build import verify_fresh; "
                    "verify_fresh('.concorde/framework'); print('fresh')",
                ],
                cwd=target,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, check.returncode, check.stdout + check.stderr)
            self.assertEqual("fresh", check.stdout.strip())


if __name__ == "__main__":
    unittest.main()

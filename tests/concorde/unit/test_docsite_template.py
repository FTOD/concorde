from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.docsite_template import (  # noqa: E402
    DocsiteTemplateError,
    SCAFFOLD_ONLY_DIRECTORIES,
    TEMPLATE_ROOT,
    WORKFLOW_TEMPLATE,
    adapter_files,
    template_digest,
    template_files,
    verify_package_root,
)


PACKAGE_ROOTS = ["agent-assets", "docsite", "operations", "scripts", "skills", "src", "templates"]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_fake_package(root: Path) -> None:
    (root / "concorde.json").write_text(
        json.dumps({"schema_version": 2, "name": "concorde", "package_roots": PACKAGE_ROOTS}),
        encoding="utf-8",
    )
    _write(root / "docsite/docusaurus.config.ts", "export default {};\n")
    _write(root / "docsite/package.json", "{}\n")
    _write(root / "docsite/README.md", "# Docsite\n")
    _write(root / "docsite/node_modules/x.js", "module.exports = {};\n")
    _write(root / "docsite/build/index.html", "<html></html>\n")
    _write(root / "docsite/.generated/a.json", "{}\n")
    _write(root / "docsite/coverage/a.json", "{}\n")
    _write(root / "docsite/tests/repository/r.test.ts", "test('x', () => {});\n")
    _write(root / "docsite/tests/unit/registry.test.ts", "test('y', () => {});\n")
    _write(root / "docsite/site.json", json.dumps({"schema_version": 1, "title": "X"}))
    _write(root / "docsite/logo.png", "not-a-real-png")
    _write(root / "docsite/scaffold/deploy-docsite.yml", "name: Deploy\n")


class DocsiteTemplateFakePackageTests(unittest.TestCase):
    def test_template_files_applies_exact_inventory_rule(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fake_package(root)
            files = template_files(root)
            self.assertEqual(
                set(files),
                {
                    "docsite/docusaurus.config.ts",
                    "docsite/package.json",
                    "docsite/README.md",
                    "docsite/tests/unit/registry.test.ts",
                    "docsite/scaffold/deploy-docsite.yml",
                },
            )
            self.assertEqual(files["docsite/docusaurus.config.ts"], b"export default {};\n")
            # sorted output
            self.assertEqual(list(files), sorted(files))

    def test_adapter_files_excludes_scaffold_only_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fake_package(root)
            adapter = adapter_files(root)
            self.assertNotIn("docsite/scaffold/deploy-docsite.yml", adapter)
            self.assertTrue(all(not path.startswith(f"{TEMPLATE_ROOT}/{name}/") for name in SCAFFOLD_ONLY_DIRECTORIES for path in adapter))
            self.assertEqual(set(adapter), set(template_files(root)) - {"docsite/scaffold/deploy-docsite.yml"})

    def test_workflow_template_returns_scaffold_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fake_package(root)
            from concorde.docsite_template import workflow_template

            self.assertEqual(workflow_template(root), b"name: Deploy\n")
            self.assertEqual(WORKFLOW_TEMPLATE, "scaffold/deploy-docsite.yml")

    def test_workflow_template_missing_raises(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fake_package(root)
            (root / "docsite/scaffold/deploy-docsite.yml").unlink()
            from concorde.docsite_template import workflow_template

            with self.assertRaises(DocsiteTemplateError):
                workflow_template(root)

    def test_digest_is_deterministic_and_sensitive_to_content(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            write_fake_package(Path(first))
            write_fake_package(Path(second))
            digest_one = template_digest(template_files(Path(first)))
            digest_two = template_digest(template_files(Path(second)))
            self.assertEqual(digest_one, digest_two)
            self.assertTrue(digest_one.startswith("sha256:"))
            (Path(second) / "docsite/docusaurus.config.ts").write_text("export default {changed: true};\n", encoding="utf-8")
            digest_three = template_digest(template_files(Path(second)))
            self.assertNotEqual(digest_one, digest_three)

    def test_symlink_anywhere_in_the_traversed_tree_raises(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fake_package(root)
            target = root / "docsite/docusaurus.config.ts"
            link = root / "docsite/linked.ts"
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("symlinks are not supported in this environment")
            with self.assertRaises(DocsiteTemplateError):
                template_files(root)

    def test_symlinked_directory_raises(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fake_package(root)
            real_dir = root / "elsewhere"
            real_dir.mkdir()
            (real_dir / "a.md").write_text("# A\n", encoding="utf-8")
            link = root / "docsite/linked-dir"
            try:
                link.symlink_to(real_dir, target_is_directory=True)
            except OSError:
                self.skipTest("symlinks are not supported in this environment")
            with self.assertRaises(DocsiteTemplateError):
                template_files(root)

    def test_symlinked_excluded_directory_is_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fake_package(root)
            shutil.rmtree(root / "docsite/node_modules")
            elsewhere = root / "shared-node-modules"
            elsewhere.mkdir()
            (elsewhere / "x.js").write_text("module.exports = {};\n", encoding="utf-8")
            try:
                (root / "docsite/node_modules").symlink_to(elsewhere, target_is_directory=True)
            except OSError:
                self.skipTest("symlinks are not supported in this environment")
            files = template_files(root)
            self.assertNotIn("docsite/node_modules/x.js", files)
            self.assertIn("docsite/docusaurus.config.ts", files)

    def test_missing_docsite_root_raises(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "concorde.json").write_text(json.dumps({"package_roots": PACKAGE_ROOTS}), encoding="utf-8")
            with self.assertRaises(DocsiteTemplateError):
                template_files(root)
            with self.assertRaises(DocsiteTemplateError):
                adapter_files(root)

    def test_verify_package_root_requires_manifest_entry_and_real_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fake_package(root)
            verify_package_root(root)  # does not raise

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fake_package(root)
            (root / "concorde.json").write_text(
                json.dumps({"package_roots": [name for name in PACKAGE_ROOTS if name != "docsite"]}),
                encoding="utf-8",
            )
            with self.assertRaises(DocsiteTemplateError):
                verify_package_root(root)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fake_package(root)
            import shutil

            shutil.rmtree(root / "docsite")
            with self.assertRaises(DocsiteTemplateError):
                verify_package_root(root)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fake_package(root)
            import shutil

            real_docsite = root / "docsite"
            elsewhere = root / "elsewhere-docsite"
            shutil.move(str(real_docsite), str(elsewhere))
            try:
                real_docsite.symlink_to(elsewhere, target_is_directory=True)
            except OSError:
                self.skipTest("symlinks are not supported in this environment")
            with self.assertRaises(DocsiteTemplateError):
                verify_package_root(root)

    def test_verify_package_root_missing_manifest_raises(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(DocsiteTemplateError):
                verify_package_root(root)


class DocsiteTemplateRealRepositoryTests(unittest.TestCase):
    def test_real_docsite_includes_expected_stable_files(self):
        verify_package_root(REPOSITORY_ROOT)
        files = template_files(REPOSITORY_ROOT)
        self.assertIn("docsite/docusaurus.config.ts", files)
        self.assertIn("docsite/package-lock.json", files)
        self.assertIn("docsite/scaffold/deploy-docsite.yml", files)
        self.assertNotIn("docsite/sidebars.docs.ts", files)

    def test_real_docsite_excludes_disposable_and_project_owned_paths(self):
        files = template_files(REPOSITORY_ROOT)
        self.assertNotIn("docsite/site.json", files)
        for path in files:
            self.assertNotIn("node_modules", path)
            self.assertNotIn("/build/", "/" + path)
            self.assertFalse(path.startswith("docsite/build/"))
            self.assertNotIn(".generated", path)
            self.assertFalse(path.startswith("docsite/tests/repository/"))

    def test_adapter_files_excludes_scaffold_from_real_repository(self):
        adapter = adapter_files(REPOSITORY_ROOT)
        self.assertTrue(all(not path.startswith("docsite/scaffold/") for path in adapter))
        files = template_files(REPOSITORY_ROOT)
        self.assertIn("docsite/scaffold/deploy-docsite.yml", files)

    def test_digest_over_real_package_is_stable_across_calls(self):
        first = template_digest(adapter_files(REPOSITORY_ROOT))
        second = template_digest(adapter_files(REPOSITORY_ROOT))
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()

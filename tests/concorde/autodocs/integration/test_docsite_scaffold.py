from __future__ import annotations

import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities.cli import main  # noqa: E402
from concorde.autodocs.docsite_scaffold import apply_docsite, propose_docsite  # noqa: E402
from concorde.autodocs.docsite_template import TEMPLATE_ROOT, adapter_files, workflow_template  # noqa: E402
from concorde.understanding.initialize import apply_proposal, propose_initialization  # noqa: E402


from tests.concorde.support.operation_json import CONFIGURATION


IGNORED_PACKAGE_DIRS = {"node_modules", "build", ".generated", ".docusaurus", "coverage"}


def _init_project(root: Path, module_id: str = "module.atlas", name: str = "Atlas") -> None:
    proposed = propose_initialization(root, module_id, name, operation_configuration=CONFIGURATION)
    (root / ".concorde").mkdir(parents=True, exist_ok=True)
    (root / ".concorde/init-proposal.json").write_text(json.dumps(proposed.result["proposal"]), encoding="utf-8")
    applied = apply_proposal(root, ".concorde/init-proposal.json")
    assert applied.status == "success", applied.findings


def _copy_light_package(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPOSITORY_ROOT / "concorde.json", destination / "concorde.json")

    def _ignore(_directory: str, names: list[str]) -> list[str]:
        return [name for name in names if name in IGNORED_PACKAGE_DIRS]

    shutil.copytree(REPOSITORY_ROOT / "docsite", destination / "docsite", ignore=_ignore)
    return destination


class DocsiteScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_unconfigured_project_is_invalid_001(self) -> None:
        result = propose_docsite(self.root)
        self.assertEqual(result.status, "invalid")
        self.assertEqual({finding.rule_id for finding in result.findings}, {"CONCORDE-DOCSITE-001"})

    def test_broken_package_root_is_invalid_002(self) -> None:
        _init_project(self.root)
        with tempfile.TemporaryDirectory() as package_tmp:
            broken_package = Path(package_tmp) / "package"
            broken_package.mkdir()
            (broken_package / "concorde.json").write_text(json.dumps({"package_roots": ["src"]}), encoding="utf-8")
            result = propose_docsite(self.root, package_root=broken_package)
            self.assertEqual(result.status, "invalid")
            self.assertEqual({finding.rule_id for finding in result.findings}, {"CONCORDE-DOCSITE-002"})

    def test_proposal_is_deterministic(self) -> None:
        _init_project(self.root)
        first = propose_docsite(self.root)
        second = propose_docsite(self.root)
        self.assertEqual(first.status, "proposal")
        self.assertEqual(first.result["proposal"], second.result["proposal"])

    def test_proposal_file_set(self) -> None:
        _init_project(self.root)
        result = propose_docsite(self.root)
        proposal = result.result["proposal"]
        paths = {item["path"] for item in proposal["files"]}
        expected_adapter = set(adapter_files(REPOSITORY_ROOT))
        self.assertTrue(expected_adapter.issubset(paths))
        self.assertIn(f"{TEMPLATE_ROOT}/site.json", paths)
        self.assertNotIn("README.md", paths)
        self.assertTrue(all(not path.startswith(f"{TEMPLATE_ROOT}/scaffold/") for path in paths))
        site_json_entry = next(item for item in proposal["files"] if item["path"] == f"{TEMPLATE_ROOT}/site.json")
        real_site_json = (REPOSITORY_ROOT / "docsite/site.json").read_text(encoding="utf-8")
        self.assertNotEqual(site_json_entry["content"], real_site_json)

    def test_defaults_without_git_use_localhost_and_info_finding(self) -> None:
        _init_project(self.root)
        result = propose_docsite(self.root)
        identity = result.result["proposal"]["identity"]
        self.assertEqual(identity["url"], "https://localhost")
        self.assertEqual(identity["baseUrl"], "/")
        self.assertNotIn("repository", identity)
        self.assertIn("CONCORDE-DOCSITE-009", {finding.rule_id for finding in result.findings})

    def test_github_origin_derives_identity_defaults(self) -> None:
        _init_project(self.root)
        git_dir = self.root / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text('[remote "origin"]\n\turl = git@github.com:org/atlas.git\n', encoding="utf-8")
        result = propose_docsite(self.root)
        identity = result.result["proposal"]["identity"]
        self.assertEqual(identity["repository"], "https://github.com/org/atlas")
        self.assertEqual(identity["url"], "https://org.github.io")
        self.assertEqual(identity["baseUrl"], "/atlas/")
        self.assertEqual(identity["organizationName"], "org")
        self.assertEqual(identity["projectName"], "atlas")
        self.assertNotIn("CONCORDE-DOCSITE-009", {finding.rule_id for finding in result.findings})

    def test_github_pages_username_repository_uses_root_base_url(self) -> None:
        _init_project(self.root)
        git_dir = self.root / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text('[remote "origin"]\n\turl = https://github.com/org/org.github.io.git\n', encoding="utf-8")
        result = propose_docsite(self.root)
        identity = result.result["proposal"]["identity"]
        self.assertEqual(identity["baseUrl"], "/")

    def test_explicit_overrides_win(self) -> None:
        _init_project(self.root)
        result = propose_docsite(
            self.root,
            title="Custom Title",
            repository="https://example.test/repo",
            url="https://example.test",
            base_url="/atlas/",
            github_pages=True,
        )
        identity = result.result["proposal"]["identity"]
        self.assertEqual(identity["title"], "Custom Title")
        self.assertEqual(identity["repository"], "https://example.test/repo")
        self.assertEqual(identity["url"], "https://example.test")
        self.assertEqual(identity["baseUrl"], "/atlas/")

    def test_invalid_inputs_are_rejected_003(self) -> None:
        _init_project(self.root)
        for kwargs in (
            {"title": "   "},
            {"repository": "not-a-url"},
            {"url": "ftp://example.test"},
            {"base_url": "no-slashes"},
        ):
            with self.subTest(kwargs=kwargs):
                result = propose_docsite(self.root, **kwargs)
                self.assertEqual(result.status, "invalid")
                self.assertEqual({finding.rule_id for finding in result.findings}, {"CONCORDE-DOCSITE-003"})

    def test_github_pages_adds_workflow_template_copy(self) -> None:
        _init_project(self.root)
        result = propose_docsite(self.root, github_pages=True)
        proposal = result.result["proposal"]
        entry = next(item for item in proposal["files"] if item["path"] == ".github/workflows/deploy-docsite.yml")
        self.assertEqual(entry["source"], "docsite/scaffold/deploy-docsite.yml")
        expected_sha = "sha256:" + hashlib.sha256(workflow_template(REPOSITORY_ROOT)).hexdigest()
        self.assertEqual(entry["sha256"], expected_sha)

    def test_existing_readme_is_not_overwritten_or_proposed(self) -> None:
        _init_project(self.root)
        (self.root / "README.md").write_text("# Existing\n", encoding="utf-8")
        result = propose_docsite(self.root)
        paths = {item["path"] for item in result.result["proposal"]["files"]}
        self.assertNotIn("README.md", paths)

    def test_pre_existing_docsite_directory_reports_conflicts(self) -> None:
        _init_project(self.root)
        (self.root / "docsite").mkdir()
        (self.root / "docsite/docusaurus.config.ts").write_text("existing", encoding="utf-8")
        result = propose_docsite(self.root)
        conflicts = {item["path"] for item in result.result["proposal"]["conflicts"]}
        self.assertIn("docsite/docusaurus.config.ts", conflicts)
        self.assertEqual(result.status, "proposal")

    def test_apply_from_saved_proposal_succeeds_and_is_idempotent(self) -> None:
        _init_project(self.root)
        proposed = propose_docsite(self.root, github_pages=True)
        (self.root / ".concorde/docsite-proposal.json").write_text(json.dumps(proposed.result), encoding="utf-8")
        applied = apply_docsite(self.root, ".concorde/docsite-proposal.json")
        self.assertEqual(applied.status, "success", applied.findings)
        expected_adapter = adapter_files(REPOSITORY_ROOT)
        for path, content in expected_adapter.items():
            target = self.root / path
            self.assertTrue(target.is_file())
            self.assertEqual(target.read_bytes(), content)
        identity_path = self.root / "docsite/site.json"
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        self.assertEqual(identity, proposed.result["proposal"]["identity"])
        self.assertTrue((self.root / ".github/workflows/deploy-docsite.yml").is_file())
        self.assertFalse((self.root / "README.md").exists())

        second_apply = apply_docsite(self.root, ".concorde/docsite-proposal.json")
        self.assertEqual(second_apply.status, "unchanged")

        second_propose = propose_docsite(self.root, github_pages=True)
        self.assertEqual(second_propose.status, "unchanged")

    def test_tampered_sha256_is_rejected_004(self) -> None:
        _init_project(self.root)
        proposed = propose_docsite(self.root)
        payload = json.loads(json.dumps(proposed.result))
        payload["proposal"]["files"][0]["sha256"] = "sha256:" + "0" * 64
        (self.root / ".concorde/docsite-proposal.json").write_text(json.dumps(payload), encoding="utf-8")
        applied = apply_docsite(self.root, ".concorde/docsite-proposal.json")
        self.assertEqual(applied.status, "invalid")
        self.assertEqual({finding.rule_id for finding in applied.findings}, {"CONCORDE-DOCSITE-004"})
        self.assertNotIn("stale", applied.findings[0].message)
        self.assertFalse((self.root / "docsite").exists())

    def test_changed_package_bytes_are_rejected_as_stale_004(self) -> None:
        _init_project(self.root)
        with tempfile.TemporaryDirectory() as package_tmp:
            package_copy = _copy_light_package(Path(package_tmp) / "package")
            proposed = propose_docsite(self.root, package_root=package_copy)
            (self.root / ".concorde/docsite-proposal.json").write_text(json.dumps(proposed.result), encoding="utf-8")
            config_path = package_copy / "docsite/docusaurus.config.ts"
            config_path.write_text(config_path.read_text(encoding="utf-8") + "\n// mutated\n", encoding="utf-8")
            applied = apply_docsite(self.root, ".concorde/docsite-proposal.json", package_root=package_copy)
            self.assertEqual(applied.status, "invalid")
            self.assertEqual({finding.rule_id for finding in applied.findings}, {"CONCORDE-DOCSITE-004"})
            self.assertIn("stale", applied.findings[0].message)

    def test_modified_target_is_a_conflict_and_nothing_else_is_written_005(self) -> None:
        _init_project(self.root)
        proposed = propose_docsite(self.root)
        (self.root / ".concorde/docsite-proposal.json").write_text(json.dumps(proposed.result), encoding="utf-8")
        (self.root / "docsite").mkdir()
        (self.root / "docsite/docusaurus.config.ts").write_text("tampered\n", encoding="utf-8")
        applied = apply_docsite(self.root, ".concorde/docsite-proposal.json")
        self.assertEqual(applied.status, "conflict")
        self.assertTrue(any(finding.rule_id == "CONCORDE-DOCSITE-005" for finding in applied.findings))
        self.assertFalse((self.root / "docsite/site.json").exists())
        self.assertFalse((self.root / "README.md").exists())
        self.assertEqual((self.root / "docsite/docusaurus.config.ts").read_text(encoding="utf-8"), "tampered\n")

    def test_missing_prerequisites_produce_warnings_without_changing_the_proposal_007(self) -> None:
        _init_project(self.root)
        baseline = propose_docsite(self.root)
        missing = [
            {"name": "node", "status": "missing", "detail": "not found"},
            {"name": "npm", "status": "missing", "detail": "not found"},
            {"name": "archify", "status": "missing", "detail": "not found"},
        ]
        with mock.patch("concorde.autodocs.docsite_scaffold._detect_prerequisites", return_value=missing):
            patched = propose_docsite(self.root)
        self.assertEqual(patched.result["proposal"], baseline.result["proposal"])
        rule_ids = [finding.rule_id for finding in patched.findings if finding.rule_id == "CONCORDE-DOCSITE-007"]
        self.assertEqual(len(rule_ids), 3)
        self.assertEqual({finding.severity for finding in patched.findings if finding.rule_id == "CONCORDE-DOCSITE-007"}, {"warning"})

    def test_cli_propose_round_trip(self) -> None:
        _init_project(self.root)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["--project-root", str(self.root), "docsite", "--propose", "--allow-primary-worktree"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["tool"], "docsite")
        self.assertIn(payload["status"], {"proposal", "unchanged"})

    def test_cli_apply_without_proposal_is_008(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["--project-root", str(self.root), "docsite", "--apply", "--allow-primary-worktree"])
        self.assertEqual(exit_code, 1)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "invalid")
        self.assertEqual(payload["findings"][0]["rule_id"], "CONCORDE-DOCSITE-008")


if __name__ == "__main__":
    unittest.main()

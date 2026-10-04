from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution.cli import main  # noqa: E402
from concorde.spec.initialize import (  # noqa: E402
    apply_project_proposal,
    project_proposal,
)
from concorde.spec.verification import verifies  # noqa: E402
from concorde.spec.views.docsite_scaffold import apply_docsite, propose_docsite  # noqa: E402
from concorde.spec.views.docsite_template import (
    TEMPLATE_ROOT,
    adapter_files,
    workflow_template,
)  # noqa: E402

IGNORED_PACKAGE_DIRS = {
    "node_modules",
    "build",
    ".generated",
    ".docusaurus",
    "coverage",
}


def _init_project(
    root: Path, module_id: str = "module.atlas", name: str = "Atlas"
) -> None:
    from concorde.distribution.project_defaults import install_project_defaults

    install_project_defaults(
        root, REPOSITORY_ROOT
    )  # what the installer places before initialization
    apply_project_proposal(
        root,
        REPOSITORY_ROOT,
        project_proposal(root, REPOSITORY_ROOT, name, module_id),
    )


def _copy_light_package(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPOSITORY_ROOT / "concorde.json", destination / "concorde.json")

    def _ignore(_directory: str, names: list[str]) -> list[str]:
        return [name for name in names if name in IGNORED_PACKAGE_DIRS]

    shutil.copytree(
        REPOSITORY_ROOT / "docsite", destination / "docsite", ignore=_ignore
    )
    return destination


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        env={"PATH": os.environ["PATH"], "HOME": str(root)},
    )


def _git_repository(root: Path, origin: str) -> None:
    _git(root, "init", "-q")
    _git(root, "remote", "add", "origin", origin)


class DocsiteScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_unconfigured_project_is_invalid_001(self) -> None:
        result = propose_docsite(self.root)
        self.assertEqual(result.status, "invalid")
        self.assertEqual(
            {finding.rule_id for finding in result.findings}, {"CONCORDE-DOCSITE-001"}
        )

    def test_broken_package_root_is_invalid_002(self) -> None:
        _init_project(self.root)
        with tempfile.TemporaryDirectory() as package_tmp:
            broken_package = Path(package_tmp) / "package"
            broken_package.mkdir()
            (broken_package / "concorde.json").write_text(
                json.dumps({"package_roots": ["src"]}), encoding="utf-8"
            )
            result = propose_docsite(self.root, package_root=broken_package)
            self.assertEqual(result.status, "invalid")
            self.assertEqual(
                {finding.rule_id for finding in result.findings},
                {"CONCORDE-DOCSITE-002"},
            )

    @verifies("scenario.views.scaffold-propose")
    def test_proposal_is_deterministic(self) -> None:
        _init_project(self.root)
        first = propose_docsite(self.root)
        second = propose_docsite(self.root)
        self.assertEqual(first.status, "proposal")
        self.assertEqual(first.result["proposal"], second.result["proposal"])

    @verifies("scenario.views.scaffold-stale-rejected")
    def test_only_exact_inventory_is_admitted_before_destination_handling(self) -> None:
        _init_project(self.root)
        baseline = propose_docsite(self.root).result["proposal"]
        workflow = propose_docsite(self.root, github_pages=True).result["proposal"]
        cases = []

        def variant(name, source=baseline):
            value = json.loads(json.dumps(source))
            cases.append((name, value))
            return value

        variant("partial")["files"].pop()
        variant("additional")["files"].append(
            {
                "path": "unrelated.txt",
                "content": "x",
                "sha256": "sha256:" + hashlib.sha256(b"x").hexdigest(),
            }
        )
        for destination in ("docsite/custom-docs/owned.md", "unrelated.txt"):
            variant(destination)["files"][0]["path"] = destination
        inline = variant("inline adapter")["files"][0]
        inline.pop("source")
        inline.update(
            content="arbitrary",
            sha256="sha256:" + hashlib.sha256(b"arbitrary").hexdigest(),
        )
        identity = next(
            item
            for item in variant("identity bytes")["files"]
            if item["path"] == "docsite/site.json"
        )
        identity["content"] += " "
        identity["sha256"] = (
            "sha256:" + hashlib.sha256(identity["content"].encode()).hexdigest()
        )
        variant("unexpected workflow", workflow)["github_pages"] = False
        variant("missing workflow")["github_pages"] = True
        variant("remapped workflow", workflow)["files"][0]["path"] = "workflow.yml"
        variant("wrong workflow source", workflow)["files"][0]["source"] = baseline[
            "files"
        ][0]["source"]
        variant("duplicate")["files"].append(baseline["files"][0])
        variant("unsorted")["files"].reverse()
        variant("both forms")["files"][0]["content"] = "extra"
        variant("wrong template root")["template_root"] = "other"
        variant("nonboolean workflow")["github_pages"] = "false"

        for name, proposal in cases:
            with self.subTest(name=name):
                path = self.root / ".concorde/docsite-proposal.json"
                path.write_text(json.dumps(proposal), encoding="utf-8")
                before = {
                    str(p.relative_to(self.root)): p.read_bytes()
                    for p in self.root.rglob("*")
                    if p.is_file()
                }
                with mock.patch(
                    "concorde.spec.views.docsite_scaffold.apply_files"
                ) as apply:
                    result = apply_docsite(self.root, ".concorde/docsite-proposal.json")
                self.assertEqual(result.status, "invalid", result.findings)
                apply.assert_not_called()
                after = {
                    str(p.relative_to(self.root)): p.read_bytes()
                    for p in self.root.rglob("*")
                    if p.is_file()
                }
                self.assertEqual(after, before)

    @verifies("scenario.views.scaffold-stale-rejected")
    def test_old_proposal_requires_regeneration_without_writing(self) -> None:
        _init_project(self.root)
        proposal = propose_docsite(self.root).result["proposal"]
        self.assertEqual(proposal["proposal_version"], 2)
        proposal["proposal_version"] = 1
        (self.root / "old-proposal.json").write_text(json.dumps(proposal))
        result = apply_docsite(self.root, "old-proposal.json")
        self.assertEqual(result.status, "invalid")
        self.assertIn("regenerate with docsite --propose", str(result.findings))
        self.assertFalse((self.root / "docsite").exists())

    @verifies("scenario.views.scaffold-propose")
    def test_proposal_file_set(self) -> None:
        _init_project(self.root)
        result = propose_docsite(self.root)
        proposal = result.result["proposal"]
        paths = {item["path"] for item in proposal["files"]}
        expected_adapter = set(adapter_files(REPOSITORY_ROOT))
        self.assertTrue(expected_adapter.issubset(paths))
        self.assertIn(f"{TEMPLATE_ROOT}/site.json", paths)
        self.assertNotIn("README.md", paths)
        self.assertNotIn("docsite/src/pages/graph.tsx", paths)
        self.assertNotIn("docsite/static/architecture-graph.json", paths)
        self.assertTrue(
            all(not path.startswith(f"{TEMPLATE_ROOT}/scaffold/") for path in paths)
        )
        site_json_entry = next(
            item
            for item in proposal["files"]
            if item["path"] == f"{TEMPLATE_ROOT}/site.json"
        )
        real_site_json = (REPOSITORY_ROOT / "docsite/site.json").read_text(
            encoding="utf-8"
        )
        self.assertNotEqual(site_json_entry["content"], real_site_json)

    @verifies("scenario.views.scaffold-propose")
    def test_defaults_without_git_use_localhost_and_info_finding(self) -> None:
        _init_project(self.root)
        result = propose_docsite(self.root)
        identity = result.result["proposal"]["identity"]
        self.assertEqual(identity["url"], "https://localhost")
        self.assertEqual(identity["baseUrl"], "/")
        self.assertNotIn("repository", identity)
        self.assertIn(
            "CONCORDE-DOCSITE-009", {finding.rule_id for finding in result.findings}
        )

    @verifies("scenario.views.scaffold-propose")
    def test_github_origin_derives_identity_defaults(self) -> None:
        _init_project(self.root)
        _git_repository(self.root, "git@github.com:org/atlas.git")
        result = propose_docsite(self.root)
        identity = result.result["proposal"]["identity"]
        self.assertEqual(identity["repository"], "https://github.com/org/atlas")
        self.assertEqual(identity["url"], "https://org.github.io")
        self.assertEqual(identity["baseUrl"], "/atlas/")
        self.assertEqual(identity["organizationName"], "org")
        self.assertEqual(identity["projectName"], "atlas")
        self.assertNotIn(
            "CONCORDE-DOCSITE-009", {finding.rule_id for finding in result.findings}
        )

    @verifies("scenario.views.scaffold-propose")
    def test_github_pages_username_repository_uses_root_base_url(self) -> None:
        _init_project(self.root)
        _git_repository(self.root, "https://github.com/org/org.github.io.git")
        result = propose_docsite(self.root)
        identity = result.result["proposal"]["identity"]
        self.assertEqual(identity["baseUrl"], "/")

    @verifies("scenario.views.scaffold-propose")
    def test_linked_worktree_reads_the_repository_origin(self) -> None:
        primary = self.root / "primary"
        primary.mkdir()
        _git_repository(primary, "https://github.com/org/atlas.git")
        _git(
            primary,
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "start",
        )
        linked = self.root / "linked"
        _git(primary, "worktree", "add", "-q", str(linked))
        self.assertTrue((linked / ".git").is_file())
        _init_project(linked)
        identity = propose_docsite(linked).result["proposal"]["identity"]
        self.assertEqual(identity["repository"], "https://github.com/org/atlas")
        self.assertEqual(identity["baseUrl"], "/atlas/")

    def test_a_directory_inside_another_repository_has_no_origin(self) -> None:
        _git_repository(self.root, "https://github.com/org/atlas.git")
        project = self.root / "nested"
        project.mkdir()
        _init_project(project)
        identity = propose_docsite(project).result["proposal"]["identity"]
        self.assertNotIn("repository", identity)

    @verifies("scenario.views.scaffold-propose")
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
            {"url": "https://"},
            {"url": "https:///path"},
            {"repository": "http://:80/x"},
            {"base_url": "no-slashes"},
        ):
            with self.subTest(kwargs=kwargs):
                result = propose_docsite(self.root, **kwargs)
                self.assertEqual(result.status, "invalid")
                self.assertEqual(
                    {finding.rule_id for finding in result.findings},
                    {"CONCORDE-DOCSITE-003"},
                )

    @verifies("scenario.views.scaffold-propose")
    def test_github_pages_adds_workflow_template_copy(self) -> None:
        _init_project(self.root)
        result = propose_docsite(self.root, github_pages=True)
        proposal = result.result["proposal"]
        entry = next(
            item
            for item in proposal["files"]
            if item["path"] == ".github/workflows/deploy-docsite.yml"
        )
        self.assertEqual(entry["source"], "docsite/scaffold/deploy-docsite.yml")
        expected_sha = (
            "sha256:" + hashlib.sha256(workflow_template(REPOSITORY_ROOT)).hexdigest()
        )
        self.assertEqual(entry["sha256"], expected_sha)

    @verifies("scenario.views.scaffold-propose")
    def test_existing_readme_is_not_overwritten_or_proposed(self) -> None:
        _init_project(self.root)
        (self.root / "README.md").write_text("# Existing\n", encoding="utf-8")
        result = propose_docsite(self.root)
        paths = {item["path"] for item in result.result["proposal"]["files"]}
        self.assertNotIn("README.md", paths)

    @verifies("scenario.views.scaffold-propose")
    def test_pre_existing_docsite_directory_reports_conflicts(self) -> None:
        _init_project(self.root)
        (self.root / "docsite").mkdir()
        (self.root / "docsite/docusaurus.config.ts").write_text(
            "existing", encoding="utf-8"
        )
        result = propose_docsite(self.root)
        conflicts = {item["path"] for item in result.result["proposal"]["conflicts"]}
        self.assertIn("docsite/docusaurus.config.ts", conflicts)
        self.assertEqual(result.status, "proposal")

    @verifies("scenario.views.scaffold-apply")
    def test_apply_from_saved_proposal_succeeds_and_is_idempotent(self) -> None:
        _init_project(self.root)
        proposed = propose_docsite(self.root, github_pages=True)
        (self.root / ".concorde/docsite-proposal.json").write_text(
            json.dumps(proposed.result), encoding="utf-8"
        )
        applied = apply_docsite(self.root, ".concorde/docsite-proposal.json")
        self.assertEqual(applied.status, "success", applied.findings)
        expected_adapter = adapter_files(REPOSITORY_ROOT)
        for path, content in expected_adapter.items():
            target = self.root / path
            self.assertTrue(target.is_file())
            self.assertEqual(target.read_bytes(), content)
        self.assertFalse((self.root / "docsite/src/pages/graph.tsx").exists())
        self.assertFalse(
            (self.root / "docsite/static/architecture-graph.json").exists()
        )
        config = (self.root / "docsite/docusaurus.config.ts").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("label: 'Graph'", config)
        # Diagrams are D2, rendered by the d2 program; the Mermaid theme is gone.
        self.assertNotIn("theme-mermaid", config)
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
        (self.root / ".concorde/docsite-proposal.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        applied = apply_docsite(self.root, ".concorde/docsite-proposal.json")
        self.assertEqual(applied.status, "invalid")
        self.assertEqual(
            {finding.rule_id for finding in applied.findings}, {"CONCORDE-DOCSITE-004"}
        )
        self.assertNotIn("stale", applied.findings[0].message)
        self.assertFalse((self.root / "docsite").exists())

    @verifies("scenario.views.scaffold-stale-rejected")
    def test_changed_package_bytes_are_rejected_as_stale_004(self) -> None:
        _init_project(self.root)
        with tempfile.TemporaryDirectory() as package_tmp:
            package_copy = _copy_light_package(Path(package_tmp) / "package")
            proposed = propose_docsite(self.root, package_root=package_copy)
            (self.root / ".concorde/docsite-proposal.json").write_text(
                json.dumps(proposed.result), encoding="utf-8"
            )
            config_path = package_copy / "docsite/docusaurus.config.ts"
            config_path.write_text(
                config_path.read_text(encoding="utf-8") + "\n// mutated\n",
                encoding="utf-8",
            )
            applied = apply_docsite(
                self.root, ".concorde/docsite-proposal.json", package_root=package_copy
            )
            self.assertEqual(applied.status, "invalid")
            self.assertEqual(
                {finding.rule_id for finding in applied.findings},
                {"CONCORDE-DOCSITE-004"},
            )
            self.assertIn("stale", applied.findings[0].message)

    @verifies("scenario.views.scaffold-conflict")
    def test_modified_target_is_a_conflict_and_nothing_else_is_written_005(
        self,
    ) -> None:
        _init_project(self.root)
        proposed = propose_docsite(self.root)
        (self.root / ".concorde/docsite-proposal.json").write_text(
            json.dumps(proposed.result), encoding="utf-8"
        )
        (self.root / "docsite").mkdir()
        (self.root / "docsite/docusaurus.config.ts").write_text(
            "tampered\n", encoding="utf-8"
        )
        (self.root / "docsite/package.json").write_text("{}\n", encoding="utf-8")
        applied = apply_docsite(self.root, ".concorde/docsite-proposal.json")
        self.assertEqual(applied.status, "conflict")
        self.assertEqual(
            ["docsite/docusaurus.config.ts", "docsite/package.json"],
            applied.result["conflicts"],
        )
        self.assertEqual(
            {"CONCORDE-DOCSITE-005"},
            {finding.rule_id for finding in applied.findings},
        )
        self.assertFalse((self.root / "docsite/site.json").exists())
        self.assertFalse((self.root / "README.md").exists())
        self.assertEqual(
            (self.root / "docsite/docusaurus.config.ts").read_text(encoding="utf-8"),
            "tampered\n",
        )

    @verifies("scenario.views.scaffold-propose")
    def test_missing_prerequisites_produce_warnings_without_changing_the_proposal_007(
        self,
    ) -> None:
        _init_project(self.root)
        baseline = propose_docsite(self.root)
        missing = [
            {"name": "node", "status": "missing", "detail": "not found"},
            {"name": "npm", "status": "outdated", "detail": "npm 8 was found"},
        ]
        with mock.patch(
            "concorde.spec.views.docsite_scaffold._detect_prerequisites",
            return_value=missing,
        ):
            patched = propose_docsite(self.root)
        self.assertEqual(patched.result["proposal"], baseline.result["proposal"])
        rule_ids = [
            finding.rule_id
            for finding in patched.findings
            if finding.rule_id == "CONCORDE-DOCSITE-007"
        ]
        self.assertEqual(len(rule_ids), 2)
        self.assertEqual(
            {
                finding.strictness
                for finding in patched.findings
                if finding.rule_id == "CONCORDE-DOCSITE-007"
            },
            {"warning"},
        )

    @verifies("scenario.views.scaffold-propose")
    def test_cli_propose_round_trip(self) -> None:
        _init_project(self.root)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "--project-root",
                    str(self.root),
                    "docsite",
                    "--propose",
                ]
            )
        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["tool"], "docsite")
        self.assertIn(payload["status"], {"proposal", "unchanged"})

    def test_cli_apply_without_proposal_is_008(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "--project-root",
                    str(self.root),
                    "docsite",
                    "--apply",
                ]
            )
        self.assertEqual(exit_code, 1)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "invalid")
        self.assertEqual(payload["findings"][0]["rule_id"], "CONCORDE-DOCSITE-008")


class DocsiteScaffoldRefusalTests(unittest.TestCase):
    """Malformed proposals and damaged packages are refused with the promised status."""

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        _init_project(self.root)
        self.proposed = propose_docsite(self.root)
        self.assertEqual("proposal", self.proposed.status, self.proposed.findings)

    def apply(self, value, **options):
        (self.root / ".concorde/docsite-proposal.json").write_text(
            json.dumps(value), encoding="utf-8"
        )
        with mock.patch(
            "concorde.spec.views.docsite_scaffold.apply_files"
        ) as apply_files:
            result = apply_docsite(
                self.root, ".concorde/docsite-proposal.json", **options
            )
        if result.status != "success":
            apply_files.assert_not_called()
        return result

    def proposal(self) -> dict:
        return json.loads(json.dumps(self.proposed.result["proposal"]))

    @verifies("scenario.views.scaffold-stale-rejected")
    def test_malformed_proposal_shapes_are_invalid_004(self) -> None:
        cases = {
            "null result": {"result": None},
            "result without proposal": {"result": {"prerequisites": []}},
            "null proposal": {"proposal": None},
        }
        extra = self.proposal()
        extra["unexpected"] = True
        cases["extra field"] = extra
        missing = self.proposal()
        del missing["conflicts"]
        cases["missing conflicts"] = missing
        bad_conflicts = self.proposal()
        bad_conflicts["conflicts"] = [{"path": "x"}]
        cases["bad conflict"] = bad_conflicts
        for key, value in (
            ("schema_version", 2),
            ("url", "https://"),
            ("baseUrl", "atlas"),
            ("title", ""),
            ("tagline", "added"),
        ):
            identity = self.proposal()
            identity["identity"][key] = value
            cases[f"identity {key}"] = identity
        for name, value in cases.items():
            with self.subTest(name=name):
                result = self.apply(value)
                self.assertEqual("invalid", result.status, result.findings)
                self.assertEqual(
                    {"CONCORDE-DOCSITE-004"}, {f.rule_id for f in result.findings}
                )
                self.assertFalse((self.root / "docsite").exists())

    @verifies("scenario.views.scaffold-stale-rejected")
    def test_differing_files_name_every_path_and_repeats(self) -> None:
        many = self.proposal()
        for item in many["files"]:
            item["sha256"] = "sha256:" + "0" * 64
        result = self.apply(many)
        self.assertEqual("invalid", result.status)
        message = str(result.error)
        self.assertGreater(len(many["files"]), 20)
        for item in many["files"]:
            self.assertIn(item["path"], message)

        repeated = self.proposal()
        repeated["files"].append(repeated["files"][0])
        message = str(self.apply(repeated).error)
        self.assertIn("repeated paths: " + repeated["files"][0]["path"], message)

        reordered = self.proposal()
        reordered["files"].reverse()
        message = str(self.apply(reordered).error)
        self.assertIn("not sorted by path", message)
        self.assertNotIn("0 differing", message)

    def test_package_without_docsite_root_is_invalid_002_on_apply(self) -> None:
        with tempfile.TemporaryDirectory() as package_tmp:
            package = _copy_light_package(Path(package_tmp) / "package")
            proposed = propose_docsite(self.root, package_root=package)
            (package / "concorde.json").write_text(
                json.dumps({"package_roots": ["src"]}), encoding="utf-8"
            )
            result = self.apply(proposed.result, package_root=package)
        self.assertEqual("invalid", result.status)
        self.assertEqual({"CONCORDE-DOCSITE-002"}, {f.rule_id for f in result.findings})
        self.assertIn("reinstall", result.findings[0].remediation)

    def test_unsafe_template_is_invalid_002_on_propose_and_apply(self) -> None:
        with tempfile.TemporaryDirectory() as package_tmp:
            package = _copy_light_package(Path(package_tmp) / "package")
            proposed = propose_docsite(self.root, package_root=package)
            (package / "docsite/plugins/link.ts").symlink_to("index.ts")
            for result in (
                propose_docsite(self.root, package_root=package),
                self.apply(proposed.result, package_root=package),
            ):
                self.assertEqual("invalid", result.status)
                self.assertEqual(
                    {"CONCORDE-DOCSITE-002"}, {f.rule_id for f in result.findings}
                )

    def test_missing_workflow_template_is_invalid_002(self) -> None:
        with tempfile.TemporaryDirectory() as package_tmp:
            package = _copy_light_package(Path(package_tmp) / "package")
            (package / "docsite/scaffold/deploy-docsite.yml").unlink()
            result = propose_docsite(self.root, package_root=package, github_pages=True)
        self.assertEqual("invalid", result.status)
        self.assertEqual({"CONCORDE-DOCSITE-002"}, {f.rule_id for f in result.findings})

    @verifies("scenario.views.scaffold-conflict")
    def test_dangling_destination_symlink_is_a_conflict(self) -> None:
        (self.root / "docsite").mkdir()
        (self.root / "docsite/package.json").symlink_to("missing-target")
        result = self.apply(self.proposed.result)
        self.assertEqual("conflict", result.status, result.findings)
        self.assertEqual(["docsite/package.json"], result.result["conflicts"])
        self.assertTrue((self.root / "docsite/package.json").is_symlink())

    @verifies("scenario.views.scaffold-apply")
    def test_every_change_requires_an_absent_destination(self) -> None:
        (self.root / ".concorde/docsite-proposal.json").write_text(
            json.dumps(self.proposed.result), encoding="utf-8"
        )
        with mock.patch(
            "concorde.spec.views.docsite_scaffold.apply_files", return_value=[]
        ) as apply_files:
            apply_docsite(self.root, ".concorde/docsite-proposal.json")
        changes = apply_files.call_args.args[1]
        self.assertTrue(changes)
        self.assertEqual({None}, {change["before_digest"] for change in changes})


if __name__ == "__main__":
    unittest.main()

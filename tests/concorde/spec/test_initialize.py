"""Initialization: an honest Protocol 13 root Module stub, proposed before anything is written."""

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.distribution.project_defaults import install_project_defaults
from concorde.spec import initialize
from concorde.spec.initialize import apply_project_proposal, project_proposal
from concorde.spec.repository import SpecError, SpecRepository, digest
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from tests.concorde.support.spec_project import PACKAGE


class InitialModuleTests(unittest.TestCase):
    @verifies(
        "scenario.spec.propose-initialization",
        "scenario.spec.apply-initialization",
        "scenario.spec.rollback-on-failure",
    )
    def test_initialization_is_honest_and_rolls_back_a_bad_reading_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install_project_defaults(
                root, PACKAGE
            )  # the installer's outputs precede initialization
            proposal = project_proposal(root, PACKAGE, "New project")
            self.assertEqual(
                [
                    ".concorde/config.json",
                    ".concorde/specs.json",
                    "specs/project/module.md",
                    "specs/project/module.md.json",
                ],
                [item["path"] for item in proposal["files"]],
            )
            self.assertTrue(
                all(item["before_digest"] is None for item in proposal["files"])
            )
            self.assertFalse((root / ".concorde/config.json").exists())
            source = next(
                f for f in proposal["files"] if f["path"] == "specs/project/module.md"
            )
            before = source["content"]
            source["content"] = before.replace("## Relationships", "## Drawing")
            with self.assertRaises(SpecError):
                apply_project_proposal(root, PACKAGE, proposal)
            self.assertFalse((root / ".concorde/config.json").exists())
            self.assertFalse((root / "specs/project/module.md").exists())
            source["content"] = before
            applied = apply_project_proposal(root, PACKAGE, proposal)
            self.assertEqual("applied", applied["status"])
            repository = SpecRepository(root, PACKAGE)
            target = repository.module("module.project")
            self.assertEqual("specs/project/module.md", target.primary_document)
            self.assertEqual(("specs/project/module.md",), target.documents)
            body = repository.document(target.primary_document).body
            self.assertIn("not been specified yet", body)
            self.assertEqual((), target.files)
            definitions = repository.definitions(target)
            self.assertEqual(
                ((), (), (), ()),
                (
                    definitions.requirements,
                    definitions.scenarios,
                    definitions.concepts,
                    definitions.realizations,
                ),
            )
            registry = json.loads((root / ".concorde/specs.json").read_text())
            self.assertEqual(
                {
                    "schema_version": 3,
                    "modules": [
                        {
                            "id": "module.project",
                            "title": "New project",
                            "entry": "specs/project/module.md",
                            "owns": ["specs/project/module.md"],
                            "contains": [],
                            "uses": [],
                            "includes": [],
                            "participates": [],
                        }
                    ],
                },
                registry,
            )
            config = json.loads((root / ".concorde/config.json").read_text())
            self.assertEqual([], config["checks"])
            self.assertEqual(
                "success", validate_repository(root, package_root=PACKAGE).status
            )

    @verifies("scenario.spec.project-python")
    def test_the_configuration_records_the_projects_own_interpreter(self):
        def config(root, **options) -> dict:
            proposal = project_proposal(root, PACKAGE, "New project", **options)
            content = next(
                f["content"]
                for f in proposal["files"]
                if f["path"] == ".concorde/config.json"
            )
            return json.loads(content)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install_project_defaults(root, PACKAGE)
            self.assertNotIn("python", config(root))
            (root / ".venv/bin").mkdir(parents=True)
            (root / ".venv/bin/python").write_text("")
            self.assertEqual(".venv/bin/python", config(root)["python"])
            self.assertEqual(
                "/opt/env/bin/python",
                config(root, python="/opt/env/bin/python")["python"],
            )
            proposal = project_proposal(root, PACKAGE, "New project")
            self.assertEqual(
                "applied", apply_project_proposal(root, PACKAGE, proposal)["status"]
            )
            self.assertEqual(
                ".venv/bin/python",
                json.loads((root / ".concorde/config.json").read_text())["python"],
            )

    @verifies("scenario.spec.init-installation")
    def test_concorde_installed_files_are_bound_apart(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            for path, content in {
                "app.py": "print('app')\n",
                "CLAUDE.md": "# Rules\n",
                ".claude/skills/concorde/SKILL.md": "---\nname: concorde\n---\n",
                ".claude/settings.json": "{}\n",
            }.items():
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_text(content)
            install_project_defaults(root, PACKAGE)
            (root / ".concorde/install.json").write_text(
                json.dumps(
                    {
                        "files": [
                            ".claude/skills/concorde/SKILL.md",
                            ".concorde/bin/concorde",
                        ],
                        "amended": [".gitignore", "CLAUDE.md"],
                    }
                )
            )
            proposal = project_proposal(root, PACKAGE, "App")
            metadata = json.loads(
                next(
                    f for f in proposal["files"] if f["path"].endswith("module.md.json")
                )["content"]
            )
            realizations = {r["id"]: r["entries"] for r in metadata["defines"]}
            self.assertEqual(
                [".claude/skills/concorde/SKILL.md"],
                realizations["realization.project.concorde-installation"],
            )
            existing = realizations["realization.project.existing-files"]
            self.assertIn("CLAUDE.md", existing)
            # The project's own file next to the installed skill is bound exactly.
            self.assertIn(".claude/settings.json", existing)
            self.assertNotIn(".claude/", existing)
            self.assertNotIn(".claude/skills/concorde/SKILL.md", existing)
            apply_project_proposal(root, PACKAGE, proposal)
            subprocess.run(("git", "add", "-A"), cwd=root, check=True)
            report = validate_repository(root, package_root=PACKAGE)
            self.assertEqual(
                "success",
                report.status,
                [f.message for f in report.findings if f.severity == "error"],
            )

    def test_existing_version_controlled_files_are_bound_to_the_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            for path, content in {
                "README.md": "# App\n",
                "src/app.py": "print('app')\n",
                "src/.hidden.cfg": "x\n",
                "specs/notes.txt": "drafts\n",
                ".gitignore": "ignored/\n",
                "ignored/cache.txt": "never tracked\n",
            }.items():
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_text(content)
            install_project_defaults(root, PACKAGE)
            proposal = project_proposal(root, PACKAGE, "App")
            metadata = json.loads(
                next(
                    f for f in proposal["files"] if f["path"].endswith("module.md.json")
                )["content"]
            )
            (realization,) = metadata["defines"]
            self.assertEqual("realization.project.existing-files", realization["id"])
            entries = realization["entries"]
            self.assertIn("src/", entries)
            self.assertIn("src/.hidden.cfg", entries)
            self.assertIn("specs/notes.txt", entries)
            self.assertIn("README.md", entries)
            self.assertIn(".gitignore", entries)
            self.assertNotIn("specs/", entries)
            self.assertFalse(any(entry.startswith("ignored") for entry in entries))
            apply_project_proposal(root, PACKAGE, proposal)
            subprocess.run(("git", "add", "-A"), cwd=root, check=True)
            report = validate_repository(root, package_root=PACKAGE)
            self.assertEqual(
                "success",
                report.status,
                [f.message for f in report.findings if f.severity == "error"],
            )

    @verifies("scenario.spec.reject-not-installed")
    def test_a_project_without_the_protocol_copy_is_not_initialized(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Existing project\n")
            before = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
            with self.assertRaises(SpecError) as raised:
                project_proposal(root, PACKAGE, "New project")
            self.assertEqual("not_installed", raised.exception.code)
            self.assertEqual(
                before, sorted(str(p.relative_to(root)) for p in root.rglob("*"))
            )
            self.assertEqual("# Existing project\n", (root / "README.md").read_text())

    @verifies("scenario.spec.reject-already-initialized")
    def test_an_already_configured_project_refuses_a_second_initialization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            from concorde.distribution.project_defaults import install_project_defaults

            install_project_defaults(root, PACKAGE)
            apply_project_proposal(
                root,
                PACKAGE,
                project_proposal(root, PACKAGE, "New project"),
            )
            paths = [
                ".concorde/config.json",
                ".concorde/specs.json",
                "specs/project/module.md",
                "specs/project/module.md.json",
            ]
            before = {path: (root / path).read_bytes() for path in paths}
            with self.assertRaises(SpecError) as raised:
                project_proposal(root, PACKAGE, "Second project")
            self.assertEqual("already_initialized", raised.exception.code)
            self.assertEqual(
                before, {path: (root / path).read_bytes() for path in paths}
            )

    @verifies(
        "scenario.spec.reject-invalid-proposal",
        "scenario.spec.reject-stale-proposal",
        "scenario.spec.reject-proposal-outside-files",
    )
    def test_apply_rejects_an_invalid_out_of_bound_or_stale_proposal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            from concorde.distribution.project_defaults import install_project_defaults

            install_project_defaults(root, PACKAGE)
            original = project_proposal(root, PACKAGE, "New project")

            def mutated(update):
                proposal = copy.deepcopy(original)
                update(proposal)
                return proposal

            def reconfigured(update):
                proposal = copy.deepcopy(original)
                config = json.loads(proposal["files"][0]["content"])
                proposal["files"][0]["content"] = (
                    json.dumps(update(config), indent=2) + "\n"
                )
                return proposal

            cases = [
                (
                    "foreign envelope",
                    "invalid_proposal",
                    mutated(
                        lambda p: p.update(type_id="concorde-topology-application")
                    ),
                ),
                (
                    "issuance token",
                    "invalid_proposal",
                    mutated(lambda p: p.update(issuance_token="accepted")),  # noqa: S106 - deliberately forged proposal field
                ),
                (
                    "registry omitted",
                    "invalid_proposal",
                    mutated(lambda p: p["files"].pop(1)),
                ),
                (
                    "registry rebound",
                    "invalid_proposal",
                    reconfigured(lambda c: {**c, "registry": ".concorde/other.json"}),
                ),
                (
                    "Protocol rebound",
                    "invalid_proposal",
                    reconfigured(
                        lambda c: {
                            **c,
                            "protocol": {
                                **c["protocol"],
                                "digest": digest(b"another Protocol"),
                            },
                        }
                    ),
                ),
                (
                    "replacement claimed",
                    "invalid_proposal",
                    mutated(lambda p: p.update(base_digest=digest(b"earlier"))),
                ),
                (
                    "overwrite claimed",
                    "invalid_proposal",
                    mutated(
                        lambda p: p["files"][2].update(before_digest=digest(b"earlier"))
                    ),
                ),
                (
                    "out of bound file",
                    "permission_denied",
                    mutated(
                        lambda p: p["files"].append(
                            {
                                "path": "specs/project/extra.md",
                                "before_digest": None,
                                "content": "# Extra\n",
                            }
                        )
                    ),
                ),
            ]
            for label, code, proposal in cases:
                with self.subTest(case=label):
                    with self.assertRaises(SpecError) as raised:
                        apply_project_proposal(root, PACKAGE, proposal)
                    self.assertEqual(code, raised.exception.code)
                    self.assertFalse((root / ".concorde/config.json").exists())
                    self.assertFalse((root / "specs/project").exists())
            # The proposal's preconditions changed: a destination the proposal expects to be absent exists.
            (root / "specs/project").mkdir(parents=True)
            (root / "specs/project/module.md").write_text("# Concurrent draft\n")
            with self.assertRaises(SpecError) as raised:
                apply_project_proposal(root, PACKAGE, original)
            self.assertEqual("stale_proposal", raised.exception.code)
            self.assertFalse((root / ".concorde/config.json").exists())
            self.assertFalse((root / ".concorde/specs.json").exists())
            self.assertEqual(
                "# Concurrent draft\n", (root / "specs/project/module.md").read_text()
            )


class ProposalBindingTests(unittest.TestCase):
    """Apply accepts only the exact proposal propose returned, named by its digest."""

    def init(self, root, data):
        return initialize.initialize(root, PACKAGE, data)

    @verifies(
        "scenario.spec.reject-invalid-proposal",
        "scenario.spec.reject-stale-proposal",
        "scenario.spec.apply-initialization",
    )
    def test_apply_is_bound_to_the_proposal_digest_and_the_project_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            install_project_defaults(root, PACKAGE)
            (root / "app.py").write_text("print('app')\n")
            proposed = self.init(
                root,
                {"action": "propose", "name": "App"},
            )
            proposal, named = proposed["proposal"], proposed["proposal_digest"]
            self.assertEqual(digest(proposal), named)

            def refused(data, code):
                with self.assertRaises(SpecError) as raised:
                    self.init(root, {"action": "apply", **data})
                self.assertEqual(code, raised.exception.code)
                self.assertFalse((root / ".concorde/config.json").exists())
                self.assertFalse((root / "specs/project").exists())

            # A digest that names another proposal, or a proposal changed after propose.
            refused(
                {"proposal": proposal, "proposal_digest": digest(b"other")},
                "invalid_proposal",
            )
            forged = copy.deepcopy(proposal)
            forged["data"]["files"][2]["content"] += "\nAn extra promise.\n"
            refused({"proposal": forged, "proposal_digest": named}, "invalid_proposal")
            refused({"proposal": proposal}, "invalid_input")
            # A new project file changes what propose would return: the proposal is stale.
            (root / "tool.py").write_text("print('tool')\n")
            refused({"proposal": proposal, "proposal_digest": named}, "stale_proposal")
            (root / "tool.py").unlink()
            applied = self.init(
                root,
                {"action": "apply", "proposal": proposal, "proposal_digest": named},
            )
            self.assertEqual("applied", applied["status"])
            self.assertIsNone(applied["proposal_digest"])


if __name__ == "__main__":
    unittest.main()

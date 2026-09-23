"""Initialization: an honest Protocol 11 root Module stub, proposed before anything is written."""

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.distribution.project_defaults import install_project_defaults
from concorde.spec.initialize import apply_project_proposal, project_proposal
from concorde.spec.repository import SpecError, SpecRepository, digest
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from tests.concorde.support.spec_project import CONFIGURATION, PACKAGE


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
            proposal = project_proposal(root, PACKAGE, "New project", CONFIGURATION)
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
            proposal = project_proposal(root, PACKAGE, "App", CONFIGURATION)
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
                project_proposal(root, PACKAGE, "New project", CONFIGURATION)
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
                project_proposal(root, PACKAGE, "New project", CONFIGURATION),
            )
            paths = [
                ".concorde/config.json",
                ".concorde/specs.json",
                "specs/project/module.md",
                "specs/project/module.md.json",
            ]
            before = {path: (root / path).read_bytes() for path in paths}
            with self.assertRaises(SpecError) as raised:
                project_proposal(root, PACKAGE, "Second project", CONFIGURATION)
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
            original = project_proposal(root, PACKAGE, "New project", CONFIGURATION)

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


if __name__ == "__main__":
    unittest.main()

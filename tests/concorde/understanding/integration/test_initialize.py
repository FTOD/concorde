import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.understanding.initialize import apply_proposal, propose_initialization  # noqa: E402
from tests.concorde.support.operation_json import CONFIGURATION
from concorde.understanding.validate import validate_project  # noqa: E402


class InitializationTests(unittest.TestCase):
    def test_installed_reflection_settings_are_preserved_and_bound_to_proposal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = root / ".concorde/reflections/config.json"
            settings.parent.mkdir(parents=True)
            value = json.loads((REPOSITORY_ROOT / "agent-assets/reflections/config.default.json").read_text())
            value["require_approval"] = True
            settings.write_text(json.dumps(value) + "\n")
            before = settings.read_bytes()
            proposed = propose_initialization(root, "module.example", "Example", operation_configuration=CONFIGURATION)
            self.assertEqual(proposed.result["proposal"]["conflicts"], ())
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]))
            settings.write_text(json.dumps({**value, "order": "oldest-first"}))
            self.assertEqual(apply_proposal(root, "accepted.json").status, "conflict")
            self.assertFalse((root / ".concorde/config.json").exists())
            settings.write_bytes(before)
            self.assertEqual(apply_proposal(root, "accepted.json").status, "success")
            self.assertEqual(settings.read_bytes(), before)
            self.assertEqual(apply_proposal(root, "accepted.json").status, "unchanged")

    def test_proposal_is_deterministic_minimal_profile_seven_and_non_mutating(self):
        with tempfile.TemporaryDirectory(prefix="Example Project ") as temporary:
            root = Path(temporary)
            before = list(root.rglob("*"))
            first = propose_initialization(root, operation_configuration=CONFIGURATION)
            self.assertEqual(first, propose_initialization(root, operation_configuration=CONFIGURATION))
            self.assertEqual(first.status, "proposal")
            proposal = first.result["proposal"]
            self.assertEqual(proposal["proposal_version"], 4)
            slug = proposal["project_root_id"].split(".", 1)[1]
            self.assertEqual(
                {item["path"] for item in proposal["files"]},
                {
                    ".concorde/config.json",
                    ".concorde/reflections/index.json",
                    ".concorde/reflections/config.json",
                    f"specs/{slug}/architecture.md",
                    f"specs/{slug}/diagrams/system-overview.json",
                },
            )
            config = next(item for item in proposal["files"] if item["path"] == ".concorde/config.json")
            self.assertIn('"profile_version": 7', config["content"])
            reflections = next(item for item in proposal["files"] if item["path"] == ".concorde/reflections/index.json")
            self.assertEqual(json.loads(reflections["content"]), {"high_water": "R-000", "schema_version": 1})
            architecture = next(item for item in proposal["files"] if item["path"].endswith("architecture.md"))
            for heading in ("Responsibility", "Boundary", "Entities", "Relationships", "Interactions", "Modules", "Features", "Decisions"):
                self.assertIn(f"## {heading}", architecture["content"])
            self.assertIn("diagrams/system-overview.json", architecture["content"])
            diagram = next(item for item in proposal["files"] if item["path"].endswith("system-overview.json"))
            diagram_value = json.loads(diagram["content"])
            self.assertEqual(diagram_value["diagram_type"], "architecture")
            self.assertEqual(diagram_value["meta"]["quality_profile"], "showcase")
            self.assertEqual(diagram_value["meta"]["legend"], {"mode": "hidden"})
            self.assertGreaterEqual(len(diagram_value["connections"]), 1)
            for forbidden in ("module.md", "design.md", "abstract.md", "implementation.md", "contracts"):
                self.assertNotIn(forbidden, {item["path"] for item in proposal["files"]})
            for item in proposal["files"]:
                self.assertEqual(item["sha256"], "sha256:" + hashlib.sha256(item["content"].encode()).hexdigest())
            self.assertEqual(list(root.rglob("*")), before)

    def test_apply_is_exact_idempotent_and_produces_valid_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposed = propose_initialization(root, "module.sample", "Sample", operation_configuration=CONFIGURATION)
            proposal = root / "accepted.json"
            proposal.write_text(json.dumps(proposed.result["proposal"]), encoding="utf-8")
            applied = apply_proposal(root, "accepted.json")
            self.assertEqual(applied.status, "success", applied.findings)
            self.assertTrue((root / "specs/sample/architecture.md").is_file())
            self.assertTrue((root / "specs/sample/diagrams/system-overview.json").is_file())
            self.assertTrue((root / ".concorde/reflections/index.json").is_file())
            self.assertEqual(json.loads((root / ".concorde/reflections/index.json").read_text()), {"high_water": "R-000", "schema_version": 1})
            self.assertFalse((root / "specs/sample/module.md").exists())
            self.assertEqual(validate_project(root).status, "success", validate_project(root).findings)
            self.assertEqual(apply_proposal(root, "accepted.json").status, "unchanged")

    def test_existing_configured_architecture_is_unchanged_not_reproposed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposed = propose_initialization(root, "module.sample", "Sample", operation_configuration=CONFIGURATION)
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]), encoding="utf-8")
            self.assertEqual(apply_proposal(root, "accepted.json").status, "success")
            result = propose_initialization(root, "module.different", "Different")
            self.assertEqual(result.status, "unchanged")
            self.assertEqual(result.result["architecture"]["module_architecture"], "specs/sample/architecture.md")
            self.assertEqual(
                set(result.artifacts),
                {
                    ".concorde/config.json",
                    ".concorde/reflections/index.json",
                    ".concorde/reflections/config.json",
                    "specs/sample/architecture.md",
                    "specs/sample/diagrams/system-overview.json",
                },
            )

    def test_partial_conflict_and_staged_failure_are_non_mutating(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposed = propose_initialization(root, "module.sample", "Sample", operation_configuration=CONFIGURATION)
            (root / "specs/sample").mkdir(parents=True)
            (root / "specs/sample/architecture.md").write_text("occupied", encoding="utf-8")
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]), encoding="utf-8")
            result = apply_proposal(root, "accepted.json")
            self.assertEqual(result.status, "conflict")
            self.assertFalse((root / ".concorde/config.json").exists())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposed = propose_initialization(root, "module.sample", "Sample", operation_configuration=CONFIGURATION)
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]), encoding="utf-8")
            with mock.patch("pathlib.Path.replace", side_effect=OSError("injected promotion failure")):
                failed = apply_proposal(root, "accepted.json")
            self.assertEqual(failed.status, "failed")
            self.assertFalse((root / ".concorde/config.json").exists())


if __name__ == "__main__":
    unittest.main()

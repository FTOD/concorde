import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.initialize import apply_proposal, propose_initialization  # noqa: E402
from concorde.validate import validate_project  # noqa: E402


class InitializationTests(unittest.TestCase):
    def test_proposal_is_deterministic_minimal_profile_seven_and_non_mutating(self):
        with tempfile.TemporaryDirectory(prefix="Example Project ") as temporary:
            root = Path(temporary)
            before = list(root.rglob("*"))
            first = propose_initialization(root)
            self.assertEqual(first, propose_initialization(root))
            self.assertEqual(first.status, "proposal")
            proposal = first.result["proposal"]
            self.assertEqual(proposal["proposal_version"], 2)
            slug = proposal["project_root_id"].split(".", 1)[1]
            self.assertEqual(
                {item["path"] for item in proposal["files"]},
                {".concorde/config.json", ".concorde/reflections/log.md", f"specs/{slug}/architecture.md"},
            )
            config = next(item for item in proposal["files"] if item["path"] == ".concorde/config.json")
            self.assertIn('"profile_version": 7', config["content"])
            reflections = next(item for item in proposal["files"] if item["path"] == ".concorde/reflections/log.md")
            self.assertIn("# Reflections:", reflections["content"])
            self.assertIn("<!-- concorde-reflection-high-water: R-000 -->", reflections["content"])
            architecture = next(item for item in proposal["files"] if item["path"].endswith("architecture.md"))
            for heading in ("Responsibility", "Boundary", "Entities", "Relationships", "Interactions", "Modules", "Features", "Decisions"):
                self.assertIn(f"## {heading}", architecture["content"])
            for forbidden in ("module.md", "design.md", "abstract.md", "implementation.md", "contracts"):
                self.assertNotIn(forbidden, {item["path"] for item in proposal["files"]})
            for item in proposal["files"]:
                self.assertEqual(item["sha256"], "sha256:" + hashlib.sha256(item["content"].encode()).hexdigest())
            self.assertEqual(list(root.rglob("*")), before)

    def test_apply_is_exact_idempotent_and_produces_valid_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposed = propose_initialization(root, "module.sample", "Sample")
            proposal = root / "accepted.json"
            proposal.write_text(json.dumps(proposed.result["proposal"]), encoding="utf-8")
            applied = apply_proposal(root, "accepted.json")
            self.assertEqual(applied.status, "success", applied.findings)
            self.assertTrue((root / "specs/sample/architecture.md").is_file())
            self.assertTrue((root / ".concorde/reflections/log.md").is_file())
            self.assertIn(
                "<!-- concorde-reflection-high-water: R-000 -->",
                (root / ".concorde/reflections/log.md").read_text(encoding="utf-8"),
            )
            self.assertFalse((root / "specs/sample/module.md").exists())
            self.assertEqual(validate_project(root).status, "success", validate_project(root).findings)
            self.assertEqual(apply_proposal(root, "accepted.json").status, "unchanged")

    def test_existing_configured_architecture_is_unchanged_not_reproposed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposed = propose_initialization(root, "module.sample", "Sample")
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]), encoding="utf-8")
            self.assertEqual(apply_proposal(root, "accepted.json").status, "success")
            result = propose_initialization(root, "module.different", "Different")
            self.assertEqual(result.status, "unchanged")
            self.assertEqual(result.result["architecture"]["module_architecture"], "specs/sample/architecture.md")
            self.assertEqual(
                set(result.artifacts),
                {".concorde/config.json", ".concorde/reflections/log.md", "specs/sample/architecture.md"},
            )

    def test_partial_conflict_and_staged_failure_are_non_mutating(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposed = propose_initialization(root, "module.sample", "Sample")
            (root / "specs/sample").mkdir(parents=True)
            (root / "specs/sample/architecture.md").write_text("occupied", encoding="utf-8")
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]), encoding="utf-8")
            result = apply_proposal(root, "accepted.json")
            self.assertEqual(result.status, "conflict")
            self.assertFalse((root / ".concorde/config.json").exists())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposed = propose_initialization(root, "module.sample", "Sample")
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]), encoding="utf-8")
            with mock.patch("pathlib.Path.replace", side_effect=OSError("injected promotion failure")):
                failed = apply_proposal(root, "accepted.json")
            self.assertEqual(failed.status, "failed")
            self.assertFalse((root / ".concorde/config.json").exists())


if __name__ == "__main__":
    unittest.main()

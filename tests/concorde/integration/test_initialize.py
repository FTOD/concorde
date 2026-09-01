import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.initialize import apply_proposal, propose_initialization  # noqa: E402
from concorde.validate import validate_project  # noqa: E402


class InitializationTests(unittest.TestCase):
    def test_proposal_is_deterministic_complete_and_writes_nothing(self):
        with tempfile.TemporaryDirectory(prefix="Example Project ") as temporary:
            root = Path(temporary)
            before = list(root.rglob("*"))
            first = propose_initialization(root)
            second = propose_initialization(root)
            self.assertEqual(first, second)
            self.assertEqual(first.status, "proposal")
            interaction = first.result["interaction_model"]
            self.assertEqual(interaction["user_interface"], "skills")
            self.assertEqual(interaction["deterministic_operations"], "scripts")
            self.assertEqual(interaction["workspace_state"], "files")
            self.assertIn("attempt/", interaction["file_lifetimes"]["temporal"])
            proposal = first.result["proposal"]
            self.assertRegex(proposal["project_root_id"], r"^module\.[a-z0-9-]+$")
            self.assertTrue(proposal["responsibility"])
            self.assertTrue(proposal["boundary"])
            self.assertEqual(proposal["provided_contracts"], ())
            self.assertEqual(proposal["required_contracts"], ())
            self.assertEqual({item["path"] for item in proposal["files"]}, {
                ".concorde/config.json",
                f"specs/{proposal['project_root_id'].split('.', 1)[1]}/module.md",
                f"specs/{proposal['project_root_id'].split('.', 1)[1]}/design.md",
                f"specs/{proposal['project_root_id'].split('.', 1)[1]}/architecture/diagrams/level-view.json",
            })
            config = next(item for item in proposal["files"] if item["path"] == ".concorde/config.json")
            self.assertIn('"profile_version": 4', config["content"])
            module = next(item for item in proposal["files"] if item["path"].endswith("/module.md"))
            design = next(item for item in proposal["files"] if item["path"].endswith("/design.md"))
            self.assertNotIn("view:", module["content"].split("---")[1])
            self.assertIn("(architecture/diagrams/level-view.json)", module["content"])
            self.assertIn("## Terminology", design["content"])
            self.assertIn("| Term | Meaning | Relationships |", design["content"])
            self.assertIn("`Skills`", design["content"])
            for concept in ("Skills", "Scripts", "Workspace Files", "attempt/"):
                self.assertIn(concept, module["content"])
            diagram = next(item for item in proposal["files"] if item["path"].endswith("/level-view.json"))
            diagram_content = json.loads(diagram["content"])
            self.assertEqual(diagram_content["meta"]["quality_profile"], "showcase")
            self.assertEqual(diagram_content["meta"]["legend"], {"mode": "hidden"})
            self.assertRegex(diagram_content["meta"]["views"][0]["id"], r"^scenario-example-project-[a-z0-9-]+-root-overview$")
            self.assertNotIn("stable_id", diagram_content["components"][0])
            for item in proposal["files"]:
                self.assertEqual(item["sha256"], "sha256:" + hashlib.sha256(item["content"].encode()).hexdigest())
            self.assertEqual(list(root.rglob("*")), before)

    def test_apply_is_exact_idempotent_and_refuses_changed_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposed = propose_initialization(root, "module.sample", "Sample")
            proposal_path = root / "accepted.json"
            proposal_path.write_text(json.dumps(proposed.result["proposal"]))
            applied = apply_proposal(root, "accepted.json")
            self.assertEqual(applied.status, "success")
            self.assertTrue((root / "specs/sample/design.md").is_file())
            validated = validate_project(root)
            self.assertEqual([item.rule_id for item in validated.findings if item.rule_id.startswith(("CONCORDE-SUMMARY-", "CONCORDE-MODULE-"))], [])
            self.assertEqual(validated.status, "success", validated.findings)
            unchanged = apply_proposal(root, "accepted.json")
            self.assertEqual(unchanged.status, "unchanged")
            (root / "specs/sample/module.md").write_text("user change")
            conflict = apply_proposal(root, "accepted.json")
            self.assertEqual(conflict.status, "conflict")
            self.assertEqual((root / "specs/sample/module.md").read_text(), "user change")

    def test_existing_configured_architecture_is_reported_not_reproposed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposed = propose_initialization(root, "module.sample", "Sample")
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]))
            self.assertEqual(apply_proposal(root, "accepted.json").status, "success")
            design = root / "specs/sample/design.md"
            design.write_text(design.read_text() + "\nProject-specific decision.\n")

            result = propose_initialization(root, "module.different", "Different")

            self.assertEqual(result.status, "unchanged")
            self.assertNotIn("proposal", result.result)
            self.assertEqual(result.result["architecture"]["root_module_id"], "module.sample")
            self.assertEqual(result.result["architecture"]["children"], ())
            self.assertEqual(result.result["interaction_model"]["user_interface"], "skills")
            self.assertEqual(set(result.artifacts), {
                ".concorde/config.json",
                "specs/sample/module.md",
                "specs/sample/design.md",
                "specs/sample/architecture/diagrams/level-view.json",
            })

    def test_existing_incomplete_configured_architecture_is_a_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".concorde").mkdir()
            (root / ".concorde/config.json").write_text(json.dumps({
                "profile_version": 4,
                "root_module_id": "module.sample",
                "specification_root": "specs/sample",
            }))

            result = propose_initialization(root)

            self.assertEqual(result.status, "conflict")
            self.assertEqual([item.rule_id for item in result.findings], ["CONCORDE-INIT-006"])
            self.assertFalse((root / "specs").exists())

    def test_partial_package_conflicts_without_promotion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposed = propose_initialization(root, "module.sample", "Sample")
            (root / "specs/sample").mkdir(parents=True)
            (root / "specs/sample/module.md").write_text("occupied")
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]))
            result = apply_proposal(root, "accepted.json")
            self.assertEqual(result.status, "conflict")
            self.assertFalse((root / ".concorde/config.json").exists())
            self.assertFalse((root / "specs/sample/design.md").exists())
            self.assertEqual({item.source for item in result.findings}, {"specs/sample/module.md"})

    def test_staged_promotion_failure_rolls_back_and_unsafe_proposal_path_is_invalid(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposed = propose_initialization(root, "module.sample", "Sample")
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]))
            with mock.patch("pathlib.Path.replace", side_effect=OSError("injected promotion failure")):
                failed = apply_proposal(root, "accepted.json")
            self.assertEqual(failed.status, "failed")
            self.assertFalse((root / ".concorde/config.json").exists())
            self.assertEqual(apply_proposal(root, "../accepted.json").status, "invalid")


if __name__ == "__main__":
    unittest.main()

"""Public standalone review through Studio's shared executable boundary."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.harness.studio import build_studio_graph
from concorde.spec.verification import verifies
from tests.concorde.harness.test_studio import invocation
from tests.concorde.spec.support import PACKAGE, ModelProcessDouble, project


class StandaloneReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        project(self.root)
        self.double = ModelProcessDouble()
        self.addCleanup(self.double.runtime_directory.cleanup)

    def graph(self, capability):
        return build_studio_graph(capability, self.root, PACKAGE, executor=self.double.executor)

    @verifies("scenario.development.standalone-review")
    def test_public_review_routes_without_a_change_and_preserves_read_only_scope(self):
        for args in [("init",), ("add", "."), ("-c", "user.name=Test",
                     "-c", "user.email=test@example.invalid", "commit", "-m", "Review baseline")]:
            subprocess.run(("git", *args), cwd=self.root, capture_output=True, check=True)
        head = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=self.root, text=True).strip()
        code = self.root / "app/transfer.py"
        code.write_text(code.read_text() + "\n# Uncommitted review input\n")
        before = {p.relative_to(self.root): p.read_bytes()
                  for directory in ("specs", "app", "checks", ".concorde/reflections")
                  for p in (self.root / directory).rglob("*") if p.is_file()}
        for mode in ("spec", "code"):
            with self.subTest(mode=mode):
                self.double.calls.clear()
                actual = self.graph("concorde-review").invoke({"invocation": invocation(
                    "concorde-review", data={"task": "Inspect transfer for defects", "review_mode": mode})})
                result = actual["result"]
                self.assertEqual("succeeded", result["status"], result)
                output = result["output"]["data"]
                self.assertEqual("service.transfer", output["target_id"])
                self.assertIsNone(output["change_id"])
                reviewed = output["reviews"][0]["data"]
                self.assertEqual(mode, reviewed["review_mode"])
                self.assertEqual("no_findings", reviewed["status"])
                self.assertTrue(reviewed["representative_tasks"])
                self.assertEqual(head, reviewed["revision"]["baseline"])
                self.assertTrue((self.root / output["artifacts"][0]["path"]).is_file())
                self.assertEqual(["route", "route", mode + "-review"],
                                 [call["stage"] for call in self.double.calls])
                for policy in actual["policies"]:
                    self.assertEqual([], policy["write_paths"])
                    self.assertFalse(policy["network"])
                    self.assertTrue(policy["fresh_session"])
                for policy in actual["policies"][:-1]:
                    self.assertEqual(["context.json"], policy["read_paths"])
                review_policy = actual["policies"][-1]
                self.assertEqual(mode == "code", "app/transfer.py" in review_policy["read_paths"])
                self.assertNotIn("app/ledger.py", review_policy["read_paths"])
                self.assertFalse((self.root / ".concorde/worktree.json").exists())
                self.assertEqual([], list((self.root / ".concorde/reflections").rglob("R-*.md")))
                self.assertEqual(before, {p: (self.root / p).read_bytes() for p in before})

    @verifies("scenario.development.standalone-review", "scenario.development.describe-policy")
    def test_public_review_preview_and_blocked_route_do_not_launch_a_reviewer(self):
        preview = self.graph("concorde-review").invoke({"invocation": invocation(
            "concorde-review", "describe-policy", {"task": "Inspect transfer", "review_mode": "code",
                                                   "target_id": "service.transfer"})})
        self.assertEqual("described", preview["result"]["status"], preview)
        self.assertEqual([], self.double.calls)
        self.assertEqual(2, len(preview["policies"]))
        self.assertIn("app/transfer.py", preview["policies"][-1]["read_paths"])
        self.assertFalse((self.root / ".concorde/runs").exists())

        def block(stage, snapshot, data, cwd):
            if stage == "route":
                data.update(outcome="unsupported", answer="No matching Module.",
                            expand_targets=[], routes=[])
        self.double.callback = block
        blocked = self.graph("concorde-review").invoke({"invocation": invocation(
            "concorde-review", data={"task": "Inspect an unknown responsibility", "review_mode": "code"})})
        self.assertEqual("blocked", blocked["result"]["status"], blocked)
        self.assertEqual([], blocked["result"]["output"]["data"]["reviews"])
        self.assertEqual(["route"], [call["stage"] for call in self.double.calls])
        self.assertFalse((self.root / ".concorde/worktree.json").exists())

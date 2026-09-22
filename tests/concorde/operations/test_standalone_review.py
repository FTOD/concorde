"""Domain-only staged-double review regression; native public dispatch has separate tests."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.spec.verification import verifies
from concorde.spec.wire_shapes import type_version
from tests.concorde.spec.support import PACKAGE, ModelProcessDouble, project
from tests.concorde.support.legacy_graphs.studio import build_studio_graph


def invocation(operation="concorde-issues", mode="execute", data=None):
    return {
        "type_id": "concorde-operation-invocation",
        "schema_version": 3,
        "operation_id": operation,
        "mode": mode,
        "configuration": None,
        "input": {
            "type_id": operation + "-request",
            "schema_version": type_version(operation + "-request"),
            "data": data
            if data is not None
            else {
                "target_id": "service.transfer",
                "task": "Explain transfer",
                **({"action": "list"} if operation == "concorde-issues" else {}),
            },
        },
    }


class StandaloneReviewTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import patch

        from tests.concorde.support.native_planning import OperationHost

        adapter = patch(
            "tests.concorde.support.legacy_graphs.studio.OperationHost", OperationHost
        )
        adapter.start()
        self.addCleanup(adapter.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        project(self.root)
        self.double = ModelProcessDouble()

    def graph(self, operation):
        return build_studio_graph(
            operation, self.root, PACKAGE, executor=self.double.executor
        )

    @verifies("scenario.review.standalone")
    def test_explicit_selection_binds_exact_unicode_intent_to_read_only_reviewer(
        self,
    ):
        task = "只读列出实际 LangGraph 图的 factory、节点和边。\n明确不存在的标识。"
        constraints = ["不修改文件。", "保留顺序。", "不修改文件。"]
        actual = self.graph("concorde-code-review").invoke(
            {
                "invocation": invocation(
                    "concorde-code-review",
                    data={
                        "target_id": "service.transfer",
                        "task": task,
                        "constraints": constraints,
                    },
                )
            }
        )
        self.assertEqual("succeeded", actual["result"]["status"], actual)
        reviewer = self.double.calls[-1]
        self.assertEqual("code-review", reviewer["stage"])
        self.assertEqual(task, reviewer["snapshot"]["task"])
        self.assertEqual(constraints, reviewer["snapshot"]["constraints"])
        self.assertEqual([], actual["policies"][-1]["write_paths"])
        self.assertNotIn("app/ledger.py", actual["policies"][-1]["read_paths"])

    @verifies("scenario.review.standalone")
    def test_invalid_selection_fails_before_worker_or_persistence(self):
        for data in (
            {"task": "Inspect"},
            {"task": "Inspect", "target_id": "module.unknown"},
            {
                "task": "Inspect",
                "target_id": "service.transfer",
                "focus_id": "scenario.ledger.read",
            },
        ):
            with self.subTest(data=data):
                before = {
                    p.relative_to(self.root): p.read_bytes()
                    for p in self.root.rglob("*")
                    if p.is_file()
                }
                actual = self.graph("concorde-code-review").invoke(
                    {"invocation": invocation("concorde-code-review", data=data)}
                )
                self.assertEqual("blocked", actual["result"]["status"], actual)
                self.assertTrue(actual["result"]["errors"])
                self.assertEqual([], self.double.calls)
                self.assertEqual(
                    before,
                    {
                        p.relative_to(self.root): p.read_bytes()
                        for p in self.root.rglob("*")
                        if p.is_file()
                    },
                )

    @verifies("scenario.review.standalone")
    def test_public_review_without_a_change_preserves_read_only_scope(self):
        for args in [
            ("init",),
            ("add", "."),
            (
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                "Review baseline",
            ),
        ]:
            subprocess.run(
                ("git", *args), cwd=self.root, capture_output=True, check=True
            )
        head = subprocess.check_output(
            ("git", "rev-parse", "HEAD"), cwd=self.root, text=True
        ).strip()
        code = self.root / "app/transfer.py"
        code.write_text(code.read_text() + "\n# Uncommitted review input\n")
        before = {
            p.relative_to(self.root): p.read_bytes()
            for directory in ("specs", "app", "checks", ".concorde/reflections")
            for p in (self.root / directory).rglob("*")
            if p.is_file()
        }
        for mode in ("spec", "code"):
            with self.subTest(mode=mode):
                self.double.calls.clear()
                operation = f"concorde-{mode}-review"
                actual = self.graph(operation).invoke(
                    {
                        "invocation": invocation(
                            operation,
                            data={
                                "task": "Inspect transfer for defects",
                                "target_id": "service.transfer",
                            },
                        )
                    }
                )
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
                # Spec review also covers the target's Spec consumers; code review only the target.
                self.assertEqual(
                    {mode + "-review"},
                    {call["stage"] for call in self.double.calls},
                )
                for policy in actual["policies"]:
                    self.assertEqual([], policy["write_paths"])
                    self.assertFalse(policy["network"])
                    self.assertTrue(policy["fresh_session"])
                review_policy = actual["policies"][-1]
                self.assertEqual(
                    mode == "code", "app/transfer.py" in review_policy["read_paths"]
                )
                self.assertNotIn("app/ledger.py", review_policy["read_paths"])
                self.assertFalse((self.root / ".concorde/worktree.json").exists())
                self.assertEqual(
                    [], list((self.root / ".concorde/reflections").rglob("R-*.md"))
                )
                self.assertEqual(
                    before, {p: (self.root / p).read_bytes() for p in before}
                )

    @verifies("scenario.review.standalone", "scenario.harness.describe-policy")
    def test_public_review_preview_does_not_launch_a_reviewer(self):
        preview = self.graph("concorde-code-review").invoke(
            {
                "invocation": invocation(
                    "concorde-code-review",
                    "describe-policy",
                    {
                        "task": "Inspect transfer",
                        "target_id": "service.transfer",
                    },
                )
            }
        )
        self.assertEqual("described", preview["result"]["status"], preview)
        self.assertEqual([], self.double.calls)
        self.assertEqual(1, len(preview["policies"]))
        self.assertIn("app/transfer.py", preview["policies"][-1]["read_paths"])
        self.assertFalse((self.root / ".concorde/runs").exists())

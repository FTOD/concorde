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

    def graph(self, operation):
        return build_studio_graph(
            operation, self.root, PACKAGE, executor=self.double.executor
        )

    @verifies("scenario.review.standalone")
    def test_pi_worker_route_result_schema_requests_only_routing_judgment(self):
        from concorde.harness.worker_executor import worker_result_parameters
        from concorde.harness.worker_profile import worker_profile

        request = invocation(
            "concorde-code-review",
            data={
                "target_id": "service.transfer",
                "task": "只读检查。",
                "constraints": ["不修改文件。"],
            },
        )
        result = self.graph("concorde-code-review").invoke({"invocation": request})
        self.assertEqual("succeeded", result["result"]["status"], result)
        routers = [call for call in self.double.calls if call["stage"] == "route"]
        self.assertTrue(routers)
        for call in routers:
            schema = call["launch"].result_schema
            self.assertEqual(worker_result_parameters(worker_profile("router")), schema)
            route = schema["properties"]["routes"]["items"]
            self.assertEqual(
                {"target_id", "focus_id", "task", "constraints"},
                set(route["properties"]),
            )
            self.assertEqual({"target_id", "focus_id"}, set(route["required"]))
            self.assertFalse(route["additionalProperties"])

    @verifies("scenario.review.standalone")
    def test_selection_only_route_binds_exact_unicode_intent_to_read_only_reviewer(
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
    def test_explicit_route_rewrites_fail_with_field_diagnostics_before_reviewer(self):
        for patch in (
            {"task": "Rewrite code"},
            {"constraints": []},
            {"task": "Rewrite code", "constraints": ["extra", "Read only"]},
        ):
            with self.subTest(patch=patch):
                self.double.calls.clear()

                def rewrite(stage, snapshot, data, cwd, patch=patch):
                    if stage == "route" and data["routes"]:
                        data["routes"][0].update(patch)

                self.double.callback = rewrite
                actual = self.graph("concorde-code-review").invoke(
                    {
                        "invocation": invocation(
                            "concorde-code-review",
                            data={
                                "target_id": "service.transfer",
                                "task": "Inspect",
                                "constraints": ["Read only"],
                            },
                        )
                    }
                )
                self.assertEqual("blocked", actual["result"]["status"], actual)
                errors = actual["result"]["errors"]
                self.assertEqual("incompatible_handoff", errors[0]["code"])
                for field in patch:
                    self.assertIn("routes[0]." + field, errors[0]["message"])
                    self.assertIn("routes[0]." + field, errors[0]["field"])
                self.assertTrue(all(c["stage"] == "route" for c in self.double.calls))

    @verifies("scenario.review.standalone")
    def test_legacy_exact_echo_is_accepted_but_target_focus_and_cardinality_remain_checked(
        self,
    ):
        def echo(stage, snapshot, data, cwd):
            if stage == "route" and data["routes"]:
                data["routes"][0].update(
                    task=snapshot["task"], constraints=snapshot["constraints"]
                )

        self.double.callback = echo
        request = invocation(
            "concorde-code-review",
            data={
                "target_id": "service.transfer",
                "task": "Inspect",
                "constraints": ["Read only"],
            },
        )
        result = self.graph("concorde-code-review").invoke({"invocation": request})
        self.assertEqual("succeeded", result["result"]["status"], result)
        for mutation in ("unknown-target", "foreign-focus", "multiple"):
            self.double.calls.clear()

            def invalid(stage, snapshot, data, cwd, mutation=mutation):
                if stage != "route" or not data["routes"]:
                    return
                if mutation == "unknown-target":
                    data["routes"][0]["target_id"] = "module.unknown"
                elif mutation == "foreign-focus":
                    data["routes"][0]["focus_id"] = "scenario.ledger.read"
                else:
                    data["routes"].append(dict(data["routes"][0]))

            self.double.callback = invalid
            actual = self.graph("concorde-code-review").invoke({"invocation": request})
            self.assertEqual("blocked", actual["result"]["status"], actual)
            self.assertTrue(all(c["stage"] == "route" for c in self.double.calls))

    @verifies("scenario.review.standalone")
    def test_public_review_routes_without_a_change_and_preserves_read_only_scope(self):
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
                self.assertEqual(
                    ["route", "route", mode + "-review"],
                    [call["stage"] for call in self.double.calls],
                )
                for policy in actual["policies"]:
                    self.assertEqual([], policy["write_paths"])
                    self.assertFalse(policy["network"])
                    self.assertTrue(policy["fresh_session"])
                for policy in actual["policies"][:-1]:
                    self.assertIn("context.json", policy["read_paths"])
                    self.assertTrue(
                        all(
                            p == "context.json"
                            or p.startswith(("specs/", ".concorde/protocol/"))
                            for p in policy["read_paths"]
                        ),
                        policy["read_paths"],
                    )
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
    def test_public_review_preview_and_blocked_route_do_not_launch_a_reviewer(self):
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
        self.assertEqual(2, len(preview["policies"]))
        self.assertIn("app/transfer.py", preview["policies"][-1]["read_paths"])
        self.assertFalse((self.root / ".concorde/runs").exists())

        def block(stage, snapshot, data, cwd):
            if stage == "route":
                data.update(
                    outcome="unsupported",
                    answer="No matching Module.",
                    expand_targets=[],
                    routes=[],
                )

        self.double.callback = block
        blocked = self.graph("concorde-code-review").invoke(
            {
                "invocation": invocation(
                    "concorde-code-review",
                    data={
                        "task": "Inspect an unknown responsibility",
                    },
                )
            }
        )
        self.assertEqual("blocked", blocked["result"]["status"], blocked)
        self.assertEqual([], blocked["result"]["output"]["data"]["reviews"])
        self.assertEqual(["route"], [call["stage"] for call in self.double.calls])
        self.assertFalse((self.root / ".concorde/worktree.json").exists())

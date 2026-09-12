"""Public standalone review through Studio's shared executable boundary."""
import subprocess
import json
from dataclasses import replace
import tempfile
import unittest
from pathlib import Path

from concorde.harness.studio import build_studio_graph
from concorde.spec.verification import verifies
from concorde.spec.typed_data import typed
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
    def test_native_codex_and_claude_schemas_request_only_routing_judgment(self):
        for integration in ('codex', 'claude'):
            with self.subTest(integration=integration):
                configuration = typed('concorde-capability-configuration',
                    {'integration': integration, 'enforcement': 'native'})
                path = self.root / '.concorde/config.json'
                config = json.loads(path.read_text())
                config['capability_configuration'] = configuration
                path.write_text(json.dumps(config))
                captured = []
                def runner(argv, **kwargs):
                    schema = (json.loads(Path(argv[argv.index('--output-schema') + 1]).read_text())
                        if '--output-schema' in argv else json.loads(argv[argv.index('--json-schema') + 1]))
                    if schema['properties']['stage']['const'] == 'route':
                        route = schema['$defs']['concorde-main-stage-result']['properties']['routes']['items']
                        self.assertEqual({'target_id', 'focus_id'}, set(route['properties']))
                        self.assertEqual({'target_id', 'focus_id'}, set(route['required']))
                        self.assertFalse(route['additionalProperties'])
                        captured.append(route)
                    return self.double.run(argv, **kwargs)
                self.double.executor = replace(self.double.executor, runner=runner)
                request = invocation('concorde-review', data={'target_id': 'service.transfer',
                    'task': '只读检查。', 'constraints': ['不修改文件。'], 'review_mode': 'code'})
                request['configuration'] = configuration
                result = self.graph('concorde-review').invoke({'invocation': request})
                self.assertEqual('succeeded', result['result']['status'], result)
                self.assertTrue(captured)

    @verifies("scenario.development.standalone-review")
    def test_selection_only_route_binds_exact_unicode_intent_to_read_only_reviewer(self):
        task = "只读列出实际 LangGraph 图的 factory、节点和边。\n明确不存在的标识。"
        constraints = ["不修改文件。", "保留顺序。", "不修改文件。"]
        actual = self.graph("concorde-review").invoke({"invocation": invocation(
            "concorde-review", data={"target_id": "service.transfer", "task": task,
                                    "constraints": constraints, "review_mode": "code"})})
        self.assertEqual("succeeded", actual["result"]["status"], actual)
        reviewer = self.double.calls[-1]
        self.assertEqual("code-review", reviewer["stage"])
        self.assertEqual(task, reviewer["snapshot"]["task"])
        self.assertEqual(constraints, reviewer["snapshot"]["constraints"])
        self.assertEqual([], actual["policies"][-1]["write_paths"])
        self.assertNotIn("app/ledger.py", actual["policies"][-1]["read_paths"])

    @verifies("scenario.development.standalone-review")
    def test_explicit_route_rewrites_fail_with_field_diagnostics_before_reviewer(self):
        for patch in ({"task": "Rewrite code"}, {"constraints": []},
                      {"task": "Rewrite code", "constraints": ["extra", "Read only"]}):
            with self.subTest(patch=patch):
                self.double.calls.clear()
                def rewrite(stage, snapshot, data, cwd):
                    if stage == "route" and data["routes"]:
                        data["routes"][0].update(patch)
                self.double.callback = rewrite
                actual = self.graph("concorde-review").invoke({"invocation": invocation(
                    "concorde-review", data={"target_id": "service.transfer", "task": "Inspect",
                        "constraints": ["Read only"], "review_mode": "code"})})
                self.assertEqual("blocked", actual["result"]["status"], actual)
                errors = actual["result"]["errors"]
                self.assertEqual("incompatible_handoff", errors[0]["code"])
                for field in patch:
                    self.assertIn("routes[0]." + field, errors[0]["message"])
                    self.assertIn("routes[0]." + field, errors[0]["field"])
                self.assertTrue(all(c["stage"] == "route" for c in self.double.calls))

    @verifies("scenario.development.standalone-review")
    def test_legacy_exact_echo_is_accepted_but_target_focus_and_cardinality_remain_checked(self):
        def echo(stage, snapshot, data, cwd):
            if stage == "route" and data["routes"]:
                data["routes"][0].update(task=snapshot['task'], constraints=snapshot['constraints'])
        self.double.callback = echo
        request = invocation("concorde-review", data={"target_id": "service.transfer",
            "task": "Inspect", "constraints": ["Read only"], "review_mode": "code"})
        result = self.graph("concorde-review").invoke({"invocation": request})
        self.assertEqual('succeeded', result['result']['status'], result)
        for mutation in ('unknown-target', 'foreign-focus', 'multiple'):
            self.double.calls.clear()
            def invalid(stage, snapshot, data, cwd):
                if stage != 'route' or not data['routes']:
                    return
                if mutation == 'unknown-target':
                    data['routes'][0]['target_id'] = 'module.unknown'
                elif mutation == 'foreign-focus':
                    data['routes'][0]['focus_id'] = 'scenario.ledger.read'
                else:
                    data['routes'].append(dict(data['routes'][0]))
            self.double.callback = invalid
            actual = self.graph('concorde-review').invoke({'invocation': request})
            self.assertEqual('blocked', actual['result']['status'], actual)
            self.assertTrue(all(c['stage'] == 'route' for c in self.double.calls))

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

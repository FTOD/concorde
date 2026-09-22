"""Source user session TODO instruction contracts, not live model behavior or a TODO runtime."""

from __future__ import annotations

import json
import re
import unittest

from concorde.distribution import installation
from concorde.distribution.build import build
from concorde.distribution.prompt_resolver import resolve_role_prompt
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


class UserSessionTodoInstructionTests(unittest.TestCase):
    def setUp(self):
        self.prompt = resolve_role_prompt(
            REPOSITORY_ROOT, "prompts/user-session/source/coordinator.md"
        ).body
        # Ignore editorial line wrapping, not the words that carry the obligations.
        self.text = " ".join(self.prompt.split())

    def assert_obligations(self, *clauses):
        for clause in clauses:
            with self.subTest(clause=clause):
                self.assertIn(clause, self.text)

    @verifies("scenario.distribution.user-session-todo-collection")
    def test_consent_maturity_and_implementation_intent(self):
        self.assert_obligations(
            "always remain available to chat, answer questions, read relevant sources",
            "not a mode switch, agent, subagent or Operation",
            "never silently turn it into a TODO",
            "Ask which intent the user means if unclear",
            "Discussion alone does not write records",
            "Once a concrete actionable conclusion is settled",
            "you may ask whether to record it, not after every message",
            "Record a mature task only on the user's explicit request or approval",
            "Mature means the key goal, scope and expected behavior are resolved",
            "does not require a detailed implementation plan or Spec validation",
            "Recording changes only TODO records and explicitly authorized issue records",
            "never implementation or Specs",
            "Do not launch maintenance, create a candidate, register status or bind a child",
            "No accumulated task count starts implementation automatically",
            "batching needs an explicit user request",
        )

    @verifies("scenario.distribution.user-session-todo-unsettled")
    def test_immature_choice_and_no_action_need_separate_consent(self):
        self.assert_obligations(
            "If an explicit TODO request is still underspecified, ask whether to continue "
            "clarification or save it as an issue",
            "Wait for that choice: neither save an immature TODO nor automatically create an issue",
            "Issues may retain immature concerns",
            "A settled conclusion with no further action gets no TODO",
            "closing or deleting an issue in that case requires separate user confirmation",
        )

    @verifies("scenario.distribution.user-session-todo-collection")
    def test_lightweight_content_deduplication_and_verified_persistence(self):
        self.assert_obligations(
            "one task per `.md` file under `.concorde/todos/`",
            "directory itself is the list; do not create a redundant index",
            "update the same change's record instead of creating a duplicate",
            "substantive discussion context and motivation, agreed behavior",
            "important decisions, alternatives and reasons",
            "boundaries and non-goals, necessary examples, and source issue references",
            "identity and path when present",
            "not a bare title or raw transcript",
            "lightweight notes, not planner outputs or paired Spec documents",
            "no metadata companion, registry entry, Spec verification or heavyweight task pipeline",
            "Write durably and reread the saved task to verify its complete content",
            "Preserve prior records on a failed write",
            "Check current bytes and ownership before updating",
            "avoid unsafe or symlinked paths",
            "stop on concurrent changes rather than overwriting another session's work",
        )

    @verifies("scenario.distribution.user-session-todo-promotion")
    def test_transfer_order_failure_and_partial_issue_safeguards(self):
        promotion = self.text.split("### Promote an issue", 1)[1]
        steps = (
            "User confirmation to move a mature issue into TODO also authorizes deleting",
            "First read the whole issue and its associated records",
            "Durably write the task with all relevant background",
            "then reread and verify it",
            "Only after that succeeds delete the corresponding source issue",
        )
        positions = [promotion.index(step) for step in steps]
        self.assertEqual(sorted(positions), positions)
        self.assert_obligations(
            "do not ask for redundant deletion approval",
            "observations, decisions and reasons, plus the source references",
            "A failed write or verification preserves the source",
            "If deletion fails, retain the verified task and source",
            "report the partial transfer",
            "update that same task on retry rather than duplicating it",
            "Partial resolution must not delete a multi-part issue",
            "keep still-unresolved content in the source",
            "record only the mature actionable part",
            "associated records, permissions and ownership/concurrency rules",
            "self-contained Markdown/JSON records with immutable observations",
            "normal store dispositions retain those records",
            "not an Issue solver disposition, proof of resolution",
            "Check associated metadata and live references before deletion",
            "never orphan them, delete shared records, rewrite status/runs or broaden permission",
            "preserve the issue and explain the blocker",
        )

    @verifies("scenario.distribution.user-session-todo-collection")
    def test_only_coordinator_projection_and_no_consumer_package_leakage(self):
        source = build(REPOSITORY_ROOT)
        coordinator_path = ".pi/extensions/concorde-coordinator.ts"
        coordinator = next(o for o in source.outputs if o.path == coordinator_path)
        embedded = re.search(
            r"const COORDINATOR = (.+);\n", coordinator.content.decode()
        )
        self.assertIsNotNone(embedded)
        self.assertEqual(self.prompt, json.loads(embedded.group(1)))
        self.assertEqual(
            ("prompts/user-session/source/coordinator.md",), coordinator.sources
        )
        markers = (
            b".concorde/todos/",
            b"Promote an issue only after its background is safe",
        )
        # Includes terminal worker bodies and the private Operation catalog, not only Task subagents.
        for output in source.outputs:
            if output.path != coordinator_path:
                for marker in markers:
                    self.assertNotIn(marker, output.content, output.path)
        installed = build(REPOSITORY_ROOT, framework_prefix=".concorde/framework")
        package = installation.Package(
            REPOSITORY_ROOT, json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        )
        payloads = [(o.path, o.content) for o in installed.outputs]
        payloads += [
            (path, content)
            for path, (content, _role) in installation.desired_outputs(package).items()
        ]
        for path, content in payloads:
            for marker in markers:
                self.assertNotIn(marker, content, path)
        self.assertEqual(
            {".pi/agents/tester.md", ".pi/agents/maintenance-worker.md"},
            {o.path for o in source.outputs if o.path.startswith(".pi/agents/")},
        )

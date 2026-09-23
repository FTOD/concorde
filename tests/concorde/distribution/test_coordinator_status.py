"""Source user session lifecycle instructions and their existing CLI, without launching children."""

from __future__ import annotations

import json
import re
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))
from concorde.distribution.cli import create_parser, dispatch
from concorde.distribution.prompt_resolver import resolve_role_prompt
from concorde.distribution.task_subagents import render
from concorde.harness.change_worktree import git
from concorde.harness.status_store import read_status
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies


class CoordinatorStatusTests(unittest.TestCase):
    def source_prompt(self):
        return resolve_role_prompt(
            REPOSITORY_ROOT, "prompts/user-session/source/coordinator.md"
        ).body

    @verifies(
        "scenario.session.coordinator-ownership",
        "scenario.session.task-subagents",
    )
    def test_canonical_lifecycle_is_rendered_only_for_source_user_session(self):
        prompt = self.source_prompt()
        outputs = {item.path: item for item in render(REPOSITORY_ROOT)}
        coordinator = outputs[".pi/extensions/concorde-coordinator.ts"]
        embedded = re.search(
            r"const COORDINATOR = (.+);\n", coordinator.content.decode()
        )
        self.assertIsNotNone(embedded)
        assert embedded is not None  # narrow for static checkers
        self.assertEqual(prompt, json.loads(embedded.group(1)))
        self.assertIn("prompts/user-session/source/coordinator.md", coordinator.sources)
        steps = (
            'status --register "$candidate" --task "$goal" --mode maintenance',
            "Retain the returned stable `change_id`",
            "Only after verified registration launch",
            'status --change-id "$change_id" --child "$child_id" --phase maintenance',
            "Before a tester or resumed-author ownership handoff",
            "--phase maintenance --release",
            "Only after verified release",
        )
        positions = [prompt.index(step) for step in steps]
        self.assertEqual(sorted(positions), positions)
        for obligation in (
            "Registration failure or an absent/mismatched record",
            "without changing its goal or mode",
            "not a workflow container",
            "stop any launched child",
            "release that exact existing child",
            "verify `child` is null",
            "--phase test",
            "resume the stage author",
            "Any release/binding failure blocks the handoff",
            "cannot substitute for status registration or child binding",
            "Never create a shadow ledger",
            "Preserve terminal task records",
            "not already-running peers",
        ):
            self.assertIn(obligation, prompt)
        for path in (".pi/agents/maintenance-worker.md", ".pi/agents/tester.md"):
            self.assertNotIn("Register before launch", outputs[path].content.decode())
            self.assertIn("excludeTools: subagent", outputs[path].content.decode())
        installed = render(REPOSITORY_ROOT, ".concorde/framework")
        self.assertFalse(any("concorde-coordinator" in item.path for item in installed))
        self.assertFalse(
            any("Register before launch" in item.content.decode() for item in installed)
        )

    @verifies("scenario.session.stage-continuity")
    def test_stage_reuse_fresh_handoff_and_native_steps(self):
        prompt = self.source_prompt()
        for text in (
            "high-level decomposition",
            "NOT Concorde product plan/tasks",
            "terminal Pi workers",
            "unfinished coherent stage",
            "After a completed stage",
            "durable handoff",
            "Observe stop, release the exact owner",
            "Independent components may run in parallel",
            "component gates",
            "combination barrier",
            "may directly author or repair agent profiles",
        ):
            self.assertIn(text, prompt)
        self.assertNotIn("not a LangGraph node or the maintenance author", prompt)
        self.assertNotIn(
            "Continue this session across ordinary stages",
            (
                REPOSITORY_ROOT / "prompts/task-subagent/source/maintenance-worker.md"
            ).read_text(),
        )

    @verifies("scenario.session.coordinator-ownership")
    def test_documented_cli_registers_two_candidates_and_hands_off_exact_owner(self):
        commands = re.findall(
            r"^\.venv/bin/python scripts/concorde.py (status[^\n]*)$",
            self.source_prompt(),
            re.MULTILINE,
        )
        self.assertEqual(6, len(commands))
        with tempfile.TemporaryDirectory() as directory:
            primary = Path(directory) / "primary"
            primary.mkdir()
            git(primary, "init", "-q", "-b", "trunk")
            git(primary, "config", "user.name", "Test")
            git(primary, "config", "user.email", "test@example.invalid")
            (primary / "file").write_text("base")
            git(primary, "add", ".")
            git(primary, "commit", "-qm", "base")
            values = {"$goal": "clarify coordination", "$child_id": "actual-author-run"}

            def invoke(command, root=primary):
                argv = [values.get(arg, arg) for arg in shlex.split(command)]
                return dispatch(
                    create_parser().parse_args(["--project-root", str(root), *argv])
                ).result

            states = []
            for name in ("first", "second"):
                candidate = Path(directory) / name
                git(primary, "worktree", "add", "-b", name, str(candidate))
                values["$candidate"] = str(candidate)
                state = invoke(commands[0])
                values["$change_id"] = state["change_id"]
                self.assertEqual("maintenance", state["mode"])
                self.assertIsNone(state["child"])
                self.assertEqual(state, read_status(primary, state["change_id"]))
                self.assertEqual(state, invoke(commands[0]))  # reuse, not a second ID
                self.assertIn(state, invoke(commands[1])["tasks"])
                self.assertEqual({}, state["guidance"])
                self.assertFalse((candidate / ".concorde/status").exists())
                self.assertFalse((candidate / ".concorde/runs").exists())
                states.append(state)
            self.assertEqual(2, len(invoke(commands[1])["tasks"]))
            self.assertNotEqual(states[0]["change_id"], states[1]["change_id"])
            # No model/session is launched: exercise only the documented host store API.
            bound = invoke(commands[2])
            self.assertEqual("actual-author-run", bound["child"]["id"])
            self.assertIn(bound, invoke(commands[3])["tasks"])
            values["$child_id"] = "different-run"
            for command in (commands[2], commands[4]):
                with self.assertRaises(SpecError):
                    invoke(command)
                self.assertEqual(bound, read_status(primary, bound["change_id"]))
            with self.assertRaises(SpecError):
                invoke(commands[2], root=candidate)
            values["$child_id"] = "actual-author-run"
            released = invoke(commands[4])
            self.assertIsNone(released["child"])
            self.assertIn(released, invoke(commands[5])["tasks"])
            values["$child_id"] = "actual-tester-run"
            tester = invoke(commands[2].replace("--phase maintenance", "--phase test"))
            self.assertEqual("test", tester["child"]["phase"])
            invoke(commands[4].replace("--phase maintenance", "--phase test"))
            values["$child_id"] = "actual-author-run"
            resumed = invoke(commands[2])
            self.assertEqual(bound["child"], resumed["child"])
            self.assertEqual(states[0], read_status(primary, states[0]["change_id"]))

    @verifies("scenario.session.coordinator-ownership")
    def test_cleanup_flag_is_never_silently_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            primary = Path(directory) / "primary"
            primary.mkdir()
            git(primary, "init", "-q", "-b", "trunk")
            git(primary, "config", "user.name", "Test")
            git(primary, "config", "user.email", "test@example.invalid")
            (primary / "file").write_text("base")
            git(primary, "add", ".")
            git(primary, "commit", "-qm", "base")
            candidate = Path(directory) / "candidate"
            git(primary, "worktree", "add", "-b", "candidate", str(candidate))

            def invoke(*argv, root=primary):
                return dispatch(
                    create_parser().parse_args(
                        ["--project-root", str(root), "status", *argv]
                    )
                ).result

            state = invoke("--register", str(candidate), "--task", "work")
            change_id = state["change_id"]
            with self.assertRaises(SpecError) as missing_id:
                invoke("--cleanup", "removed")
            self.assertEqual("invalid_input", missing_id.exception.code)
            with self.assertRaises(SpecError) as unrecorded:
                invoke("--change-id", change_id, "--cleanup", "retained")
            self.assertEqual("stale_evidence", unrecorded.exception.code)
            with self.assertRaises(SpecError):  # primary-only coordination
                invoke(
                    "--change-id", change_id, "--cleanup", "retained", root=candidate
                )
            self.assertEqual(state, read_status(primary, change_id))
            merged = invoke("--change-id", change_id, "--manual-merge", "HEAD")
            self.assertEqual("pending", merged["cleanup"]["status"])  # default
            git(primary, "worktree", "remove", "--force", str(candidate))
            removed = invoke("--change-id", change_id, "--cleanup", "removed")
            from concorde.delivery.records import manual_merge

            self.assertEqual(manual_merge(merged), manual_merge(removed))
            self.assertEqual("removed", removed["cleanup"]["status"])
            self.assertEqual(removed, read_status(primary, change_id))

"""The source checkout's worktree guard: hook decisions and the integration files that register it.

Concorde's own checkout refuses native worktree creation in developer agent sessions, because its
project-local Skills are worktree-owned build output. These cases exercise the hook script offline
(as Claude Code and Codex would invoke it) and pin the checked-in Claude and Codex configuration
that registers it. Nothing here touches a real agent runtime or creates a worktree.
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[4]
SCRIPT = PACKAGE / "scripts/worktree-guard.py"
SPEC = importlib.util.spec_from_file_location("concorde_worktree_guard", SCRIPT)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)

CREATING_COMMANDS = (
    "git worktree add ../feature -b feature",
    "git worktree add -b feature /tmp/wt HEAD",
    "git worktree move ../feature ../elsewhere",
    "git -C /home/dev/concorde worktree add /tmp/wt",
    "git --git-dir=/repo/.git worktree add /tmp/wt",
    "git --git-dir /repo/.git --work-tree /repo worktree add /tmp/wt",
    "git -c core.hooksPath=/dev/null worktree add /tmp/wt",
    "git --no-pager -C '/my dir' worktree add /tmp/wt",
    "cd /home/dev/concorde && git worktree add ../candidate",
    "git status; git worktree add ../candidate",
    "bash -lc 'git worktree add ../candidate'",
    "sh -c \"git worktree add /tmp/wt\"",
    "GIT_DIR=/repo/.git git worktree add /tmp/wt",
    "/usr/bin/git worktree add /tmp/wt",
    "git worktree\tadd /tmp/wt",
    "claude --worktree feature",
    "claude --worktree=feature",
    "claude -w feature",
    "claude -p --worktree probe 'describe the repository'",
    "cd /tmp && claude -w probe",
)

ORDINARY_COMMANDS = (
    "git worktree list",
    "git worktree list --porcelain -z",
    "git worktree remove --force /tmp/wt",
    "git worktree prune",
    "git worktree lock /tmp/wt",
    "git -C /tmp/wt worktree list",
    "git status",
    "git log --grep=worktree",
    "git log -- worktree add",
    "git add scripts/worktree-guard.py",
    "git commit -m 'add the worktree guard'",
    "grep -rn 'worktree add' specs",
    "python3 scripts/run-capability.py concorde-dev-loop",
    "python3 scripts/concorde.py build --check",
    "cd /tmp/concorde-worktree-abc/project && claude -p 'resume the accepted task'",
    "claude --version",
    "claude --model claude-opus-5 -p 'hello'",
    "codex exec 'hello'",
    "echo digit worktree add",
    "mygit worktree add /tmp/wt",
)


def payload(tool_name: str, tool_input: object, event: str = "PreToolUse") -> dict:
    return {"session_id": "s", "cwd": str(PACKAGE), "hook_event_name": event,
            "tool_name": tool_name, "tool_input": tool_input, "tool_use_id": "t"}


class GuardDecisionTests(unittest.TestCase):
    def test_shell_commands_that_create_or_move_worktrees_are_refused(self):
        for command in CREATING_COMMANDS:
            with self.subTest(command=command):
                verdict = guard.evaluate(payload("Bash", {"command": command}))
                self.assertTrue(verdict.blocked)
                self.assertIn(verdict.kind, {"git-worktree", "claude-worktree"})
                self.assertIn("concorde-dev-loop", verdict.reason)

    def test_ordinary_commands_including_worktree_inspection_are_allowed(self):
        for command in ORDINARY_COMMANDS:
            with self.subTest(command=command):
                self.assertFalse(guard.evaluate(payload("Bash", {"command": command})).blocked)

    def test_codex_and_powershell_shell_tools_share_the_command_check(self):
        for tool in ("Bash", "PowerShell", "shell", "exec_command"):
            with self.subTest(tool=tool):
                self.assertTrue(guard.evaluate(payload(tool, {"command": "git worktree add /tmp/wt"})).blocked)
        self.assertTrue(guard.evaluate(payload("Bash", {"argv": ["git", "worktree", "add", "/tmp/wt"]})).blocked)
        self.assertTrue(guard.evaluate(payload("Bash", "git worktree add /tmp/wt")).blocked)
        self.assertFalse(guard.evaluate(payload("Bash", {})).blocked)

    def test_enter_worktree_tool_is_refused(self):
        self.assertEqual("enter-worktree", guard.evaluate(payload("EnterWorktree", {})).kind)
        self.assertEqual("enter-worktree", guard.evaluate(payload("EnterWorktree", {"path": "/tmp/wt"})).kind)

    def test_subagent_worktree_isolation_is_refused_but_other_subagents_are_allowed(self):
        for tool in ("Agent", "Task"):
            with self.subTest(tool=tool):
                self.assertEqual("isolated-subagent",
                                 guard.evaluate(payload(tool, {"prompt": "x", "isolation": "worktree"})).kind)
                self.assertFalse(guard.evaluate(payload(tool, {"prompt": "x", "isolation": "remote"})).blocked)
                self.assertFalse(guard.evaluate(payload(tool, {"prompt": "x"})).blocked)

    def test_worktree_create_event_is_always_refused(self):
        verdict = guard.evaluate({"session_id": "s", "hook_event_name": "WorktreeCreate",
                                  "cwd": str(PACKAGE), "name": "probe", "base_ref": "main"})
        self.assertEqual("worktree-create", verdict.kind)

    def test_other_events_and_tools_are_ignored(self):
        self.assertFalse(guard.evaluate(payload("Bash", {"command": "git worktree add /tmp/wt"}, "PostToolUse")).blocked)
        self.assertFalse(guard.evaluate(payload("Read", {"file_path": "git worktree add"})).blocked)
        self.assertFalse(guard.evaluate(payload("Write", {"file_path": "x", "content": "git worktree add /tmp/wt"})).blocked)
        self.assertFalse(guard.evaluate({"hook_event_name": "SessionStart"}).blocked)
        self.assertFalse(guard.evaluate({}).blocked)


class GuardProcessTests(unittest.TestCase):
    def run_guard(self, *arguments: str, stdin: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), *arguments], input=stdin,
                              capture_output=True, text=True, cwd=str(PACKAGE))

    def test_refusal_reports_a_permission_decision_on_stdout_and_the_reason_on_stderr(self):
        completed = self.run_guard(stdin=json.dumps(payload("Bash", {"command": "git worktree add /tmp/wt"})))
        self.assertEqual(2, completed.returncode)
        decision = json.loads(completed.stdout)["hookSpecificOutput"]
        self.assertEqual("PreToolUse", decision["hookEventName"])
        self.assertEqual("deny", decision["permissionDecision"])
        self.assertEqual(guard.REASON, decision["permissionDecisionReason"])
        self.assertEqual(guard.REASON, completed.stderr.strip())

    def test_worktree_create_refusal_uses_the_exit_code_and_stderr_only(self):
        completed = self.run_guard(stdin=json.dumps({"hook_event_name": "WorktreeCreate", "name": "probe"}))
        self.assertEqual(2, completed.returncode)
        self.assertEqual("", completed.stdout)
        self.assertEqual(guard.REASON, completed.stderr.strip())

    def test_allowed_calls_are_silent(self):
        completed = self.run_guard(stdin=json.dumps(payload("Bash", {"command": "git status"})))
        self.assertEqual((0, "", ""), (completed.returncode, completed.stdout, completed.stderr))

    def test_unreadable_input_is_a_visible_non_blocking_error(self):
        for stdin in ("", "not json", "[1, 2]"):
            with self.subTest(stdin=stdin):
                completed = self.run_guard(stdin=stdin)
                self.assertEqual(1, completed.returncode)
                self.assertIn("worktree-guard", completed.stderr)

    def test_check_mode_decides_a_command_text_for_people_and_scripts(self):
        refused = self.run_guard("--check", "git -C /tmp/repo worktree add /tmp/wt")
        self.assertEqual(2, refused.returncode)
        self.assertTrue(refused.stdout.startswith("deny (git-worktree)"), refused.stdout)
        allowed = self.run_guard("--check", "git worktree list")
        self.assertEqual((0, "allow\n"), (allowed.returncode, allowed.stdout))
        explained = self.run_guard("--explain")
        self.assertEqual(0, explained.returncode)
        self.assertIn(".claude/settings.json", explained.stdout)
        self.assertIn(".codex/hooks.json", explained.stdout)


class IntegrationFilesTests(unittest.TestCase):
    """The checked-in integration files register the guard; Claude and Codex read them per worktree."""

    def test_claude_settings_deny_native_worktree_creation_and_register_the_guard(self):
        settings = json.loads((PACKAGE / ".claude/settings.json").read_text(encoding="utf-8"))
        deny = settings["permissions"]["deny"]
        for rule in ("EnterWorktree", "Agent(isolation:worktree)", "Bash(git worktree add *)",
                     "Bash(git worktree move *)", "Bash(git * worktree add *)", "Bash(git * worktree move *)",
                     "Bash(claude --worktree *)", "Bash(claude -w *)"):
            self.assertIn(rule, deny)
        self.assertNotIn("worktree", settings, "native worktree creation is refused, not configured")
        pre_tool_use = settings["hooks"]["PreToolUse"]
        guarded = [entry for entry in pre_tool_use
                   if any("scripts/worktree-guard.py" in hook["command"] for hook in entry["hooks"])]
        self.assertEqual(1, len(guarded))
        matched = set(guarded[0]["matcher"].split("|"))
        self.assertTrue({"EnterWorktree", "Agent", "Task", "Bash"} <= matched, matched)
        command = guarded[0]["hooks"][0]["command"]
        self.assertIn("${CLAUDE_PROJECT_DIR}", command)
        self.assertEqual("command", guarded[0]["hooks"][0]["type"])
        create = settings["hooks"]["WorktreeCreate"]
        self.assertTrue(any("scripts/worktree-guard.py" in hook["command"]
                            for entry in create for hook in entry["hooks"]))
        for entry in create:
            self.assertNotIn("matcher", entry, "WorktreeCreate has no matcher")

    def test_codex_hooks_register_the_guard_for_shell_commands(self):
        hooks = json.loads((PACKAGE / ".codex/hooks.json").read_text(encoding="utf-8"))
        entries = hooks["hooks"]["PreToolUse"]
        guarded = [entry for entry in entries
                   if any("scripts/worktree-guard.py" in hook["command"] for hook in entry["hooks"])]
        self.assertEqual(1, len(guarded))
        self.assertIn("Bash", guarded[0]["matcher"].split("|"))
        self.assertEqual("command", guarded[0]["hooks"][0]["type"])
        self.assertEqual(set(hooks), {"hooks"})

    def test_codex_rules_forbid_git_worktree_add_and_move(self):
        rules = (PACKAGE / ".codex/rules/worktree.rules").read_text(encoding="utf-8")
        blocks = re.findall(r"prefix_rule\((.*?)\)\n", rules, flags=re.S)
        forbidden = [block for block in blocks if 'decision = "forbidden"' in block]
        patterns = {re.search(r"pattern = (\[.*?\])", block, flags=re.S).group(1) for block in forbidden}
        self.assertEqual({'["git", "worktree", "add"]', '["git", "worktree", "move"]'}, patterns)
        self.assertNotIn('decision = "allow"', rules)

    @unittest.skipUnless(shutil.which("codex"), "the Codex CLI is not installed here")
    def test_codex_execpolicy_accepts_the_rules(self):
        def check(*command: str) -> dict:
            completed = subprocess.run(
                ["codex", "execpolicy", "check", "--rules", str(PACKAGE / ".codex/rules/worktree.rules"),
                 "--", *command], capture_output=True, text=True, cwd=str(PACKAGE), timeout=60)
            self.assertEqual(0, completed.returncode, completed.stderr)
            return json.loads(completed.stdout)

        self.assertEqual("forbidden", check("git", "worktree", "add", "/tmp/wt").get("decision"))
        self.assertEqual("forbidden", check("git", "worktree", "move", "/tmp/a", "/tmp/b").get("decision"))
        self.assertEqual([], check("git", "worktree", "list")["matchedRules"])


if __name__ == "__main__":
    unittest.main()

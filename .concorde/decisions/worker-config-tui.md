# Decision log: worker-config-tui

Goal: Implement the approved worker model configuration redesign without backward compatibility: configure-workers defaults to a human-facing terminal UI with draft edits, save/cancel, backend/model/reasoning selection, inheritance and effective source display; .concorde/worker-models.json remains the editable source of truth containing default and sparse Operation/worker overrides, AI edits it directly; shared runtime/TUI validation checks structure and catalog names without making model discovery a prerequisite; expose read-only --show --json and --check for inspection/validation; extract standalone scripts/available_models.py with --backend pi|claude and optional --json, usable outside a Git worktree and via shared functions; discovery lists configured credentialed candidates, does not probe API calls, and does not gate custom/offline configuration; remove obsolete mutation/candidate CLI flags and update existing pi picker, guidance, installation, Specs and tests. Preserve per-worktree configuration/task inheritance. Validate, deliver, and report.

## Main session: approved design and scope

The developer approved a human-facing configure-workers TUI, standalone available_models.py, and direct AI edits to worker-models.json; explicitly no backward compatibility is required. Preserve the existing sparse default/Operation/worker structure where useful, and per-worktree inheritance. Shared validation must reject malformed structure and unknown catalog names without calling model discovery. Candidate availability is advisory, not a prerequisite for editing or checking custom/offline configuration. Include Workers, Main session, Distribution, and Operations because runtime consumers, pi UI, installed entry points, and guidance must agree. No changes to the developer's current model selections are authorized or needed. Initial read-only path guesses for CLI/installation specs and task-session sources were absent; resolved actual module locations through tracked file search, with no mutation.

- Implement the approved redesign with a standard-library curses draft editor shared by the terminal command and pi picker; this avoids duplicated write/validation behavior and a new runtime dependency. AI edits JSON directly and uses read-only inspection/checking. Preserve schema version 3 and existing backend-reset inheritance; the redesign changes interfaces, not file layout.
- Extract discovery into a worktree-independent module and script, preserving credential-aware pi listing and explicitly incomplete Claude candidates; discovery is advisory and never required for configuration validation.
- Preparation succeeded with uv and npm. uv fell back from hardlinks to copies; npm reported 31 dependency vulnerabilities in the existing lockfile. No dependency upgrades are needed for this task. Initial optional-directory listing exited 2 because dependencies were not yet prepared.

## Main-session review while implementation runs

The initial configure_tui.py draft returns False on q/Esc/Cancel even with unsaved edits. The approved design explicitly promised a prompt before discarding an unsaved draft. Ensure dirty exit offers keep editing / discard (including a considered Ctrl-C path), while a clean exit needs no prompt. The original proposed UI also offered model/scope search; add a small filter/search interaction if feasible for long provider model lists. These are completion items under the approved TUI goal, not a new approval request. Verify real PTY interaction and pi suspend/resume behavior rather than only Draft methods.

- Additional main-session review: pi_models.ts refusalText previously rendered each error link's unhandled reason/explanation; the redesign removed that information without needing to. Preserve it so refusal messages retain the full decision-relevant chain. No compatibility requirement is involved. Scope/model filtering and retaining the selected scope after returning from Edit will make the new human-facing UI usable with long lists.

- Keep backend reasoning vocabulary validation independent of discovered models; unlisted model IDs are accepted. Discover on explicit request in the editor so missing programs, auth or offline operation never prevent draft edits or Save. Use duplicate-key JSON rejection to avoid ambiguous direct edits.
- Save compares the original file bytes before atomic replacement and refuses an externally changed file; cancelling and reopening retains the other edit. Backend selection clears the entry's own model/reasoning, matching the reset semantics shown to the human.
- pi opens the shared curses editor with its terminal released and always restored, rather than maintaining another mutation interface. RPC/headless callers receive direct-edit/read-only guidance; a missing named task worktree is refused rather than editing primary.
- Validation tooling: uvx initially failed because its global tool directory is sandbox read-only; use task-local UV_TOOL_DIR. Prettier was absent from docsite dependencies; npx Prettier succeeded. Persistent LSP incorrectly reports missing imports for newly created modules; fresh Pyright reports 0 errors and executable imports/tests pass. Marked those findings false-positive with evidence, although automated session-cache reminders persist. No inline ignores added.
- First focused test run: 8 failures from missing generated build preparation; building fixed them. Next run: the PTY interruption case timed out because the child had no controlling terminal, so the fixture now sends SIGINT directly. Focused runtime/editor/adapter tests then passed (17 tests, 8 subtests).
- Expanded tests: 60 passed, 40 subtests passed, one failed due to a new assertion expecting individual ignored framework files in the install receipt. Removed that assertion; retained installed-file existence and execution checks. Refactored the existing dynamic fake-d2 function attribute to a typed callable fixture to clear pre-existing Pyright findings in the touched file.
- Found out-of-scope follow-ups: src/concorde/execution/context.py still recommends removed --operation/--worker/--backend flags, and Tasks Specs say only configure-workers changes the task copy. Will request module.execution and module.tasks scope before changing those sources and delivering.

- Final in-scope verification: build and build --check passed; spec-validation passed with 0 errors/warnings; second-pass Ruff and Prettier formatting checks passed; fresh Pyright on changed Python sources/tests passed. Full suite: 624 passed, 4 skipped, 357 subtests passed, 2 failures. Both failures are old-interface references outside current Modules: execution/test_runner.py expects --backend claude in the missing-backend message; tasks/test_store.py calls removed --model/--allow-unlisted flags.
- task-validation run r-20260927T175206-task_validation-39200d35 ended blocked with the complete not_deliverable -> check_failed chain for check.tasks.tests. All other 11 configured checks passed, including Workers, Main session and Distribution. Read the full result and chain. Cannot deliver without reconciling the Tasks and Execution consumers; requesting scope expansion rather than compatibility shims or editing outside the task.
- Source changes remain in the worktree for the next round; no delivery or merge attempted while validation is blocked. Temporary task-validation stdout copy will be removed; the run store retains the complete durable result/readiness/check logs.

## Escalated to the main agent, 2026-09-27T17:54:03Z

- **task-session** task session (task worker-config-tui): `consumer_scope_required`
  The redesign is implemented in the assigned Modules. Build, build --check, structural Spec validation, focused editor/adapter tests and fresh Pyright pass. Full pytest: 624 passed, 4 skipped, 2 failed, 357 subtests passed. tests/concorde/tasks/test_store.py:134 still invokes removed --model/--allow-unlisted flags; task-validation preserves that failure below. tests/concorde/execution/test_runner.py:420 still asserts --backend claude in the missing-backend message. src/concorde/execution/context.py:482 still recommends removed --operation/--worker/--backend mutation flags. Tasks module.md/scenarios.md state that only configure-workers changes a task copy, which must include approved direct JSON edits. These files belong to module.tasks and module.execution, outside this task's Modules. Sources are preserved uncommitted in the task worktree; no backward compatibility was reintroduced.
  Not handled here (decision): Only the main agent may expand this task's Modules. Updating these consumers is required by the approved no-backward-compatibility redesign and for delivery, but this session may not edit their sources or Specs under its current scope.
  Options: Add module.tasks and module.execution to this task and its workspace binding, then resume this session to update the obsolete tests, recovery guidance and Tasks wording, verify and deliver.
  Recommendation: Expand scope to module.tasks and module.execution; these are narrow consumer reconciliations of the already approved redesign, not a new product decision.
  Caused by:
  - **command** Command task-validation r-20260927T175206-task_validation-39200d35 (workspace worker-config-tui): `not_deliverable`
    workspace worker-config-tui is not deliverable: 1 blocking finding(s), each a cause below; delivery, which decides the same readiness again, refuses the workspace until they are repaired (readiness in .concorde/runs/r-20260927T175206-task_validation-39200d35/readiness.json)
    Not handled here (decision): task-validation only decides readiness and never repairs; each finding needs a Spec change (specify) or a code change (implement), which the task level chooses
    Evidence (blocking): check.tasks.tests module.tasks check failed (exit 1); log .concorde/runs/r-20260927T175206-task_validation-39200d35/checks/check.tasks.tests.log
    Options: repair each blocking finding in the workspace and run task-validation again; run specify for a Spec finding, implement for a code or check finding
    Recommendation: repair the first blocking finding: check check.tasks.tests: module.tasks check failed (exit 1); log .concorde/runs/r-20260927T175206-task_validation-39200d35/checks/check.tasks.tests.log
    Caused by:
    - **check** check.tasks.tests: `check_failed`
      the configured check check.tasks.tests of module.tasks failed with exit code 1; its log /home/zhenyu/concorde/.concorde/runs/r-20260927T175206-task_validation-39200d35/checks/check.tasks.tests.log ends with:
      | ============================= test session starts ==============================
      | platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
      | rootdir: /home/zhenyu/concorde/.claude/worktrees/worker-config-tui
      | configfile: pyproject.toml
      | plugins: langsmith-0.14.1, xdist-3.8.0, anyio-4.15.1
      | created: 4/4 workers
      | 4 workers [34 items]
      | 
      | ........F.........................                                       [100%]
      | =================================== FAILURES ===================================
      | __________ TaskStoreTests.test_a_new_task_keeps_its_own_worker_models __________
      | [gw2] linux -- Python 3.11.15 /home/zhenyu/concorde/.claude/worktrees/worker-config-tui/.venv/bin/python
      | 
      | self = <tests.concorde.tasks.test_store.TaskStoreTests testMethod=test_a_new_task_keeps_its_own_worker_models>
      | 
      |     @verifies("scenario.tasks.open-inherits-worker-models")
      |     def test_a_new_task_keeps_its_own_worker_models(self):
      |         primary_config = self.root / models.CONFIG
      |         primary_config.write_text(
      |             json.dumps({"schema_version": 3, "default": {"model": "anthropic/a"}})
      |         )
      |         worktree = Path(self.project.open_task("t1")["worktree"])
      |         task_config = worktree / models.CONFIG
      |         inherited = task_config.read_text()
      |         self.assertEqual(primary_config.read_text(), inherited)
      |         self.assertEqual("", git(worktree, "status", "--porcelain"))
      |         primary_config.write_text(
      |             json.dumps({"schema_version": 3, "default": {"model": "anthropic/b"}})
      |         )
      |         self.assertEqual(inherited, task_config.read_text())
      |         # configure-workers changes the configuration of the worktree it runs in.
      |         output = io.StringIO()
      |         environ = {
      |             **fake_agents(self.project.base / "bin", self.project.home),
      |             "CONCORDE_CLIENT": "pi",
      |         }
      |         with (
      |             patch.dict(os.environ, environ),
      |             patch("pathlib.Path.home", return_value=self.project.home),
      |             contextlib.redirect_stdout(output),
      |             contextlib.redirect_stderr(io.StringIO()),
      |         ):
      |             status = configure.main(
      |                 ["--model", "anthropic/c", "--allow-unlisted"], cwd=worktree
      |             )
      |         value = json.loads(output.getvalue())
      | >       self.assertEqual((0, "ok"), (status, value["status"]), value)
      |                                              ^^^^^^^^^^^^^^^
      | E       KeyError: 'status'
      | 
      | tests/concorde/tasks/test_store.py:137: KeyError
      | ---------------------------- concorde test evidence ----------------------------
      | reason=manual scope=unspecified phase=unspecified attempt=1 workers=4 dist=load
      | discovery 0.8s, elapsed 4.4s; unit time 12.2s is summed concurrent work, not wall time
      | =========================== short test summary info ============================
      | FAILED tests/concorde/tasks/test_store.py::TaskStoreTests::test_a_new_task_keeps_its_own_worker_models
      | ========================= 1 failed, 33 passed in 4.44s =========================
      Not handled here (capability): a configured check only measures the code it runs against
      Evidence (log): /home/zhenyu/concorde/.concorde/runs/r-20260927T175206-task_validation-39200d35/checks/check.tasks.tests.log sha256:37f2366e85286dee3dd613f3bd5167125862c7df35dcb7bcd1a03174e5359719

```json
{
  "level": "task-session",
  "actor": "task session (task worker-config-tui)",
  "code": "consumer_scope_required",
  "detail": "The redesign is implemented in the assigned Modules. Build, build --check, structural Spec validation, focused editor/adapter tests and fresh Pyright pass. Full pytest: 624 passed, 4 skipped, 2 failed, 357 subtests passed. tests/concorde/tasks/test_store.py:134 still invokes removed --model/--allow-unlisted flags; task-validation preserves that failure below. tests/concorde/execution/test_runner.py:420 still asserts --backend claude in the missing-backend message. src/concorde/execution/context.py:482 still recommends removed --operation/--worker/--backend mutation flags. Tasks module.md/scenarios.md state that only configure-workers changes a task copy, which must include approved direct JSON edits. These files belong to module.tasks and module.execution, outside this task's Modules. Sources are preserved uncommitted in the task worktree; no backward compatibility was reintroduced.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Only the main agent may expand this task's Modules. Updating these consumers is required by the approved no-backward-compatibility redesign and for delivery, but this session may not edit their sources or Specs under its current scope."
  },
  "options": [
    "Add module.tasks and module.execution to this task and its workspace binding, then resume this session to update the obsolete tests, recovery guidance and Tasks wording, verify and deliver."
  ],
  "recommendation": "Expand scope to module.tasks and module.execution; these are narrow consumer reconciliations of the already approved redesign, not a new product decision.",
  "causes": [
    {
      "level": "command",
      "actor": "Command task-validation r-20260927T175206-task_validation-39200d35 (workspace worker-config-tui)",
      "code": "not_deliverable",
      "detail": "workspace worker-config-tui is not deliverable: 1 blocking finding(s), each a cause below; delivery, which decides the same readiness again, refuses the workspace until they are repaired (readiness in .concorde/runs/r-20260927T175206-task_validation-39200d35/readiness.json)",
      "evidence": [
        {
          "kind": "blocking",
          "ref": "check.tasks.tests",
          "detail": "module.tasks check failed (exit 1); log .concorde/runs/r-20260927T175206-task_validation-39200d35/checks/check.tasks.tests.log"
        }
      ],
      "attempts": [],
      "unhandled": {
        "reason": "decision",
        "explanation": "task-validation only decides readiness and never repairs; each finding needs a Spec change (specify) or a code change (implement), which the task level chooses"
      },
      "options": [
        "repair each blocking finding in the workspace and run task-validation again",
        "run specify for a Spec finding, implement for a code or check finding"
      ],
      "recommendation": "repair the first blocking finding: check check.tasks.tests: module.tasks check failed (exit 1); log .concorde/runs/r-20260927T175206-task_validation-39200d35/checks/check.tasks.tests.log",
      "causes": [
        {
          "level": "check",
          "actor": "check.tasks.tests",
          "code": "check_failed",
          "detail": "the configured check check.tasks.tests of module.tasks failed with exit code 1; its log /home/zhenyu/concorde/.concorde/runs/r-20260927T175206-task_validation-39200d35/checks/check.tasks.tests.log ends with:\n============================= test session starts ==============================\nplatform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0\nrootdir: /home/zhenyu/concorde/.claude/worktrees/worker-config-tui\nconfigfile: pyproject.toml\nplugins: langsmith-0.14.1, xdist-3.8.0, anyio-4.15.1\ncreated: 4/4 workers\n4 workers [34 items]\n\n........F.........................                                       [100%]\n=================================== FAILURES ===================================\n__________ TaskStoreTests.test_a_new_task_keeps_its_own_worker_models __________\n[gw2] linux -- Python 3.11.15 /home/zhenyu/concorde/.claude/worktrees/worker-config-tui/.venv/bin/python\n\nself = <tests.concorde.tasks.test_store.TaskStoreTests testMethod=test_a_new_task_keeps_its_own_worker_models>\n\n    @verifies(\"scenario.tasks.open-inherits-worker-models\")\n    def test_a_new_task_keeps_its_own_worker_models(self):\n        primary_config = self.root / models.CONFIG\n        primary_config.write_text(\n            json.dumps({\"schema_version\": 3, \"default\": {\"model\": \"anthropic/a\"}})\n        )\n        worktree = Path(self.project.open_task(\"t1\")[\"worktree\"])\n        task_config = worktree / models.CONFIG\n        inherited = task_config.read_text()\n        self.assertEqual(primary_config.read_text(), inherited)\n        self.assertEqual(\"\", git(worktree, \"status\", \"--porcelain\"))\n        primary_config.write_text(\n            json.dumps({\"schema_version\": 3, \"default\": {\"model\": \"anthropic/b\"}})\n        )\n        self.assertEqual(inherited, task_config.read_text())\n        # configure-workers changes the configuration of the worktree it runs in.\n        output = io.StringIO()\n        environ = {\n            **fake_agents(self.project.base / \"bin\", self.project.home),\n            \"CONCORDE_CLIENT\": \"pi\",\n        }\n        with (\n            patch.dict(os.environ, environ),\n            patch(\"pathlib.Path.home\", return_value=self.project.home),\n            contextlib.redirect_stdout(output),\n            contextlib.redirect_stderr(io.StringIO()),\n        ):\n            status = configure.main(\n                [\"--model\", \"anthropic/c\", \"--allow-unlisted\"], cwd=worktree\n            )\n        value = json.loads(output.getvalue())\n>       self.assertEqual((0, \"ok\"), (status, value[\"status\"]), value)\n                                             ^^^^^^^^^^^^^^^\nE       KeyError: 'status'\n\ntests/concorde/tasks/test_store.py:137: KeyError\n---------------------------- concorde test evidence ----------------------------\nreason=manual scope=unspecified phase=unspecified attempt=1 workers=4 dist=load\ndiscovery 0.8s, elapsed 4.4s; unit time 12.2s is summed concurrent work, not wall time\n=========================== short test summary info ============================\nFAILED tests/concorde/tasks/test_store.py::TaskStoreTests::test_a_new_task_keeps_its_own_worker_models\n========================= 1 failed, 33 passed in 4.44s =========================",
          "evidence": [
            {
              "kind": "log",
              "ref": "/home/zhenyu/concorde/.concorde/runs/r-20260927T175206-task_validation-39200d35/checks/check.tasks.tests.log",
              "detail": "sha256:37f2366e85286dee3dd613f3bd5167125862c7df35dcb7bcd1a03174e5359719"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "a configured check only measures the code it runs against"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        }
      ]
    }
  ]
}
```

## Main-session decision on escalation 1

Read the entire consumer_scope_required -> not_deliverable -> check_failed chain and the Tasks test log. Approved adding module.tasks and module.execution for the narrow reconciliation of direct-file editing documentation, old mutation-CLI tests, and obsolete backend recovery text. Updated the task record through store.update and the workspace through binding.write after the round ended. The task CLI has no scope-update verb; these are the owning tools' validated APIs, not source edits. The user already authorized the redesign without compatibility. Full-suite failures (624 passed, 4 skipped, 2 failed) are attributable to these old consumer assumptions. Resume to fix them and the TUI review items recorded above, validate and deliver. Main has advanced concurrently; main agent will arrange reconciliation before the checked merge if needed.

- Resume CLI initially returned invalid_input because --answer cannot be combined with --main; retried without --main, reusing the established session. No source or config mutation occurred from the refused command.

- Main-session check: primary worker-models.json SHA-256 before integration is 7feec1cbfd00ab71a53e766a66ca5e67169b02775d934b83493d77bd13ba2397; no configuration values are changed by this task.

## Task session round 2

- Read the complete affected Tasks and Execution Specs after the main agent expanded scope. Reconciled Tasks' direct-file-edit inheritance test and wording, and Execution's old mutation-flag recovery text/assertion. These follow the approved interface removal without compatibility shims.
- Implemented review requests: every dirty q/Esc/Cancel or Ctrl-C exit offers Keep editing by default and explicit Discard changes; Escape or another Ctrl-C at the confirmation keeps the draft. Ctrl-C from a nested edit uses the same confirmation. Clean exits remain immediate.
- Added slash search for scopes and discovered models; an empty query clears it. Scope selection and filter persist when returning from Edit, with Save/Cancel always available. Restored each pi refusal link's unhandled reason and explanation.
- Expanded real PTY tests to cover each dirty-exit path, safe defaults, explicit discard, nested interruption, scope/model search, clearing search, retained selection, Save, and the pi adapter running the actual terminal editor and restoring its terminal. The focused suite passed 65 tests and 7 subtests.
- Review found control-character edge cases in the configuration string pattern; tightened it and added NUL/trailing-newline cases so malformed text is rejected before backend launch.
- Tooling observations: the old Tasks/Execution test helpers have baseline Pyright optional-result errors. Compared fresh Pyright on base and changed test sources: 187 baseline errors, 184 current, no new diagnostic messages/counts; corrected the new assertions with an explicit non-null assertion. The first comparison used a hidden temporary directory that Pyright skipped, then a visible temporary directory established the baseline. Fresh Pyright on changed implementation and new tests reports 0 errors. No repeated LSP import troubleshooting or broad unrelated typing edits. One read-before-edit refusal was resolved by reading the guidance test before retrying. A /tmp output redirect was read-only under the session sandbox; reran structural validation through stdout without an output file.
- Final input verification passed: full pytest 629 passed, 4 skipped, 360 subtests passed; build and build --check; spec-validation with no findings; Ruff second-pass formatting (13 files) and Prettier check. The user model configuration was not edited; all configuration interaction tests used temporary projects.

- Inspected staged changes and committed implementation as c942df0c (Redesign worker configuration around a terminal draft editor). No user model configuration or sandbox placeholders were staged.
- task-validation r-20260927T180817-task_validation-789c0e67 passed all 14 configured checks and reported ready. delivery r-20260927T180935-delivery-f048f1f2 independently validated and delivered as 291e3825250e406158705e0a1dd591a39077fe04 with evidence .concorde/evidence/worker-config-tui/1.json. Tracked worktree is clean after delivery. No merge/rebase performed; main agent owns integration with concurrent changes.

## Main-session delivery review

Reviewed the implementation during both rounds, final report and delivery evidence 291e3825250e406158705e0a1dd591a39077fe04. Required dirty-exit confirmation, search/retained selection, and full pi error explanations are implemented and exercised in PTY/adapter tests. Final suite: 629 passed, 4 skipped, 360 subtests passed; task-validation and delivery each passed all 14 checks. Diff check is clean. Existing baseline typing findings in older test helpers are documented; no new findings remain and core changed code passes fresh Pyright. Proceeding with the mandatory checked merge.

## Closed: merged, 2026-09-27T18:12:14Z

## Main-session completion

Checked merge succeeded at 92288e9b626dec81014f53f0ece0f236e11a66e3; both build and spec-validation passed, no warnings, task closed. Post-merge read-only smoke checks passed: --check; --show --json resolves 9 Operations / 15 workers; available_models.py --backend pi --json runs from /tmp outside Git and lists 16 configured candidates. Primary worktree is clean. The user configuration SHA-256 is unchanged from 7feec1cbfd00ab71a53e766a66ca5e67169b02775d934b83493d77bd13ba2397. No unresolved product decisions remain.

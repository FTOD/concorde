# Decision log: split-agent-instructions

Goal: Split source-checkout instructions into pi AGENTS.md and Claude Code CLAUDE.md with shared DEVELOPING.md; preserve existing development rules and use host-supported task workflows; validate and deliver.

## Authorized implementation

The developer approved separate host entry files after we verified the default loaders: Claude Code chooses CLAUDE.md when present (unless configured to load both); this installed pi chooses the first readable file per directory in AGENTS.override.md, AGENTS.md, AGENTS.MD, CLAUDE.md, CLAUDE.MD order. pi has no EnterWorktree/ExitWorktree tool in this session, and shell cd does not switch session context.

Keep this change confined to source-checkout instructions and their root Module bindings, not installed consumer prompts or runtime behavior. Move shared development rules from the existing AGENTS.md into root DEVELOPING.md (docs/ is explicitly user documentation and never agent context). Both host entry files must explicitly require reading DEVELOPING.md in full. Clearly scope each entry's workflow to its host, including when both are loaded. Keep Claude Code's EnterWorktree(path)/ExitWorktree(keep) workflow. For pi, the main session stays in the primary worktree and starts a Concorde task session in the target worktree even for a single task; a pi task session already in its task does the work directly, without launching another session. Initialize references in the task worktree before starting a session, monitor its result, and merge from the primary session. Preserve the existing approval exception, defect-report process, verification, decision logging and merge checks.

Read the canonical principles and all root Module Specs; register CLAUDE.md and DEVELOPING.md in the root realization. Do not add implementation-mirroring tests for this documentation change. Run required checks and the final full suite, inspect diffs, commit, run validate and delivery Operations, and report the exact files, verification and delivery commit. Do not merge; the main session will review and merge. The main session has already initialized this task's references.

## Round 1 decisions and preparation

- Keep all shared rules in DEVELOPING.md and explicitly scope AGENTS.md to pi and CLAUDE.md to Claude Code, including when both load. The recorded authorization confirms pi must delegate even a single task and an existing task session must work directly.
- Add only CLAUDE.md and DEVELOPING.md to the root project-files realization; no Module promises or installed prompts change. Declare them pending before creation and remove pending once present.
- Use the pi Concorde task-session tool when available, with an explicit CONCORDE_CLIENT=pi CLI fallback for source checkouts without the extension; shell cd is for command execution only, not a session context switch.
- Inspection found no CLAUDE.md, virtual environment or docsite dependencies (expected initial missing-path results); one search used module.json instead of module.md.json, corrected immediately. Optional .pi and .claude/settings.json paths are absent. No source defect is implied.
- uv sync and npm ci succeeded. uv used copies instead of hardlinks; npm reported dependency deprecations and 31 audit vulnerabilities. Dependency updates are outside this documentation task. The build succeeded and all reference submodules are initialized. Protected sandbox placeholder paths in git status are not task changes and will not be staged.

- Shared instructions now explicitly preserve append-only decision logging and task-session escalation. Conflict resolution remains the main agent's responsibility, consistent with task sessions never merging branches.
- build --check and structural validate passed with zero findings. The first full-suite invocation did not start: redirecting its log to /tmp/split-agent-instructions-pytest.log failed with "Read-only file system". Respecting the session boundary, run pytest directly without that outside log path.
- Format the three root Markdown files and root metadata with Prettier and check a second pass; no new tests are warranted for this documentation-only split.

## Verification and scope blocker

- Full suite: 572 passed, 4 skipped, 3 failed. Two failures are caused by the intended instruction split: the existing Dogfooding test reads AGENTS.md alone, and docsite/tests/repository/run-checks.py omits CLAUDE.md and DEVELOPING.md from its copy list. Full targeted failure output: /tmp/concorde-ts-85aad5427229/split-agent-instructions-layout-failures.log.
- The third failure was CheckExecutorTests.test_project_tmpdir_cannot_become_a_writable_project_mount: CheckSandboxError: no writable host temporary directory outside the project is available. Retrying that test with CONCORDE_CHECK_TMPDIR="$TMPDIR" passed (1 passed), using the already permitted session scratch directory, without changing code or boundaries. Use that setting for the eventual full-suite rerun.
- validate Operation r-20260926T182531-validate-6887fe90 returned ok/ready and its configured check.concorde.tests passed, but it does not cover the two failing checks in other Modules. Do not deliver a known failing full suite solely on this readiness result.
- Escalate for module.dogfooding and module.views scope authorization before adapting their existing checks. All four intended files remain uncommitted for the next round; no other sources changed.

## Escalated to the main agent, 2026-09-26T18:26:29Z

- **task-session** task session (task split-agent-instructions): `instruction_split_requires_check_updates`
  The instruction split is implemented in AGENTS.md, CLAUDE.md, DEVELOPING.md and root realization metadata. Build, formatting, structural validation and validate Operation pass. The required full suite exposes two existing checks tied to the old file layout, reproduced with their complete output in the cause. tests/concorde/dogfooding/test_dogfooding.py reads AGENTS.md alone, and docsite/tests/repository/run-checks.py must copy the two new registered root files. These are owned by module.dogfooding and module.views, outside this task.
  Not handled here (scope): Only module.concorde is authorized and the recorded implementation scope excludes unrelated Modules; I cannot edit the two existing checks without main-agent authorization.
  Options: Authorize expanding this task to module.dogfooding and module.views for only the existing instruction test and repository-check copy list.
  Recommendation: Expand scope for those minimal adaptations, then rerun the full suite with CONCORDE_CHECK_TMPDIR="$TMPDIR", commit, validate and deliver.
  Caused by:
  - **check** full-suite follow-up for split-agent-instructions: `instruction_layout_checks_failed`
    ============================= test session starts ==============================
    | platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
    | rootdir: /home/zhenyu/concorde/.claude/worktrees/split-agent-instructions
    | configfile: pyproject.toml
    | plugins: xdist-3.8.0
    | collected 2 items
    | 
    | tests/concorde/dogfooding/test_dogfooding.py F                           [ 50%]
    | tests/concorde/views/test_repository_checks.py F                         [100%]
    | 
    | =================================== FAILURES ===================================
    | _ ConcordeRepositoryTests.test_the_repository_instructions_take_reports_and_share_the_observation_rule _
    | 
    | self = <tests.concorde.dogfooding.test_dogfooding.ConcordeRepositoryTests testMethod=test_the_repository_instructions_take_reports_and_share_the_observation_rule>
    | 
    |     @verifies("scenario.dogfooding.concorde-instructions")
    |     def test_the_repository_instructions_take_reports_and_share_the_observation_rule(
    |         self,
    |     ):
    |         instructions = words((REPOSITORY_ROOT / "AGENTS.md").read_text())
    |         for fragment in (
    |             "## Defect reports from develop installs",
    |             "python3 scripts/issues.py report --file <report> --task <task>",
    |             "Fix a Concorde implementation bug",
    |             "ask the developer before changing Concorde's design or Protocol or loosening any boundary",
    |             "`--reason not-actionable`",
    |             "Fix the defect generally, never only for the reporting project",
    |         ):
    | >           self.assertIn(words(fragment), instructions)
    | E           AssertionError: '## Defect reports from develop installs' not found in "# Developing Concorde with pi These instructions apply to pi only, including when both `AGENTS.md` and `CLAUDE.md` are loaded. Claude Code follows `CLAUDE.md` for its host workflow. Read [DEVELOPING.md](DEVELOPING.md) in full before working on this source checkout. It contains shared development rules, preparation, verification, delivery, merge checks and defect handling. ## Main session Stay in the primary worktree. Open a task as described in `DEVELOPING.md`, then start a Concorde task session in its worktree even for a single task. pi has no EnterWorktree or ExitWorktree tool; a shell `cd` changes only that command's working directory, not the session's context. 1. Open the task from the primary worktree and obtain its path with `python3 scripts/concorde.py task show <task>`. 2. Before starting the session, run `python3 scripts/development/init-references.py` from that task worktree, using its own script. The task session cannot register submodules in the shared Git configuration. 3. Use `concorde_task_session` when available. Without that extension, run `CONCORDE_CLIENT=pi python3 scripts/concorde.py task session <task> --main <its session name>` from the primary worktree. This starts pi in the task worktree; use `--answer` on the same command for a subsequent round, or the tool's `answer` input when using the extension. 4. Monitor the session's recorded result and read any escalation's complete chain with `python3 scripts/concorde.py task show <task>`. Record decisions, answer escalations within your authority, and have the session finish validation and delivery. 5. After delivery, inspect the result and merge from the primary worktree with the command and both merge checks in `DEVELOPING.md`. For several tasks, start one session per task and coordinate their results from the primary worktree. Do not edit task sources from the primary pi session or treat shell `cd` as entering a task. If a merge conflicts, the main agent arranges the Git resolution in the task worktree, then resumes its task session for verification and delivery before retrying the checked merge. ## Task session If you are already a Concorde task session in your assigned worktree, do the task directly there. Do not launch another session. Use that worktree's own `python3 scripts/concorde.py`, run commands and Operations in foreground Bash, and follow the task-session prompt for decision logging, escalation and the final `concorde_report`. Validate and deliver; leave merging to the main agent."
    | 
    | tests/concorde/dogfooding/test_dogfooding.py:227: AssertionError
    | _ RepositoryCheckPreparationTests.test_real_registry_listing_roots_are_copied __
    | 
    | self = <tests.concorde.views.test_repository_checks.RepositoryCheckPreparationTests testMethod=test_real_registry_listing_roots_are_copied>
    | 
    |     @verifies("scenario.views.load-registry")
    |     def test_real_registry_listing_roots_are_copied(self):
    |         wrapper = load_wrapper()
    | >       self.assertEqual([], wrapper.uncopied_listing_roots())
    | E       AssertionError: Lists differ: [] != ['CLAUDE.md', 'DEVELOPING.md']
    | E       
    | E       Second list contains 2 additional elements.
    | E       First extra element 0:
    | E       'CLAUDE.md'
    | E       
    | E       - []
    | E       + ['CLAUDE.md', 'DEVELOPING.md']
    | 
    | tests/concorde/views/test_repository_checks.py:37: AssertionError
    | ---------------------------- concorde test evidence ----------------------------
    | reason=manual scope=unspecified phase=unspecified attempt=1 workers=in-process
    | discovery 0.1s, elapsed 0.1s; unit time 0.0s is summed concurrent work, not wall time
    | =========================== short test summary info ============================
    | FAILED tests/concorde/dogfooding/test_dogfooding.py::ConcordeRepositoryTests::test_the_repository_instructions_take_reports_and_share_the_observation_rule
    | FAILED tests/concorde/views/test_repository_checks.py::RepositoryCheckPreparationTests::test_real_registry_listing_roots_are_copied
    | ============================== 2 failed in 0.09s ===============================
    | 
    Not handled here (scope): The fixes require module.dogfooding and module.views; this task is bound only to module.concorde.
    Tried: Full suite: 572 passed, 4 skipped, 3 failed.
    Tried: The temporary-directory failure passed when CONCORDE_CHECK_TMPDIR was set to the existing session TMPDIR.
    Tried: Reproduced the two instruction-layout failures with pytest -n 0.
    Evidence (log): /tmp/concorde-ts-85aad5427229/split-agent-instructions-layout-failures.log Complete targeted reproduction of both remaining full-suite failures.
    Recommendation: Authorize the minimal existing-test and docsite copy-list adaptations.

```json
{
  "level": "task-session",
  "actor": "task session (task split-agent-instructions)",
  "code": "instruction_split_requires_check_updates",
  "detail": "The instruction split is implemented in AGENTS.md, CLAUDE.md, DEVELOPING.md and root realization metadata. Build, formatting, structural validation and validate Operation pass. The required full suite exposes two existing checks tied to the old file layout, reproduced with their complete output in the cause. tests/concorde/dogfooding/test_dogfooding.py reads AGENTS.md alone, and docsite/tests/repository/run-checks.py must copy the two new registered root files. These are owned by module.dogfooding and module.views, outside this task.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "scope",
    "explanation": "Only module.concorde is authorized and the recorded implementation scope excludes unrelated Modules; I cannot edit the two existing checks without main-agent authorization."
  },
  "options": [
    "Authorize expanding this task to module.dogfooding and module.views for only the existing instruction test and repository-check copy list."
  ],
  "recommendation": "Expand scope for those minimal adaptations, then rerun the full suite with CONCORDE_CHECK_TMPDIR=\"$TMPDIR\", commit, validate and deliver.",
  "causes": [
    {
      "level": "check",
      "actor": "full-suite follow-up for split-agent-instructions",
      "code": "instruction_layout_checks_failed",
      "detail": "============================= test session starts ==============================\nplatform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0\nrootdir: /home/zhenyu/concorde/.claude/worktrees/split-agent-instructions\nconfigfile: pyproject.toml\nplugins: xdist-3.8.0\ncollected 2 items\n\ntests/concorde/dogfooding/test_dogfooding.py F                           [ 50%]\ntests/concorde/views/test_repository_checks.py F                         [100%]\n\n=================================== FAILURES ===================================\n_ ConcordeRepositoryTests.test_the_repository_instructions_take_reports_and_share_the_observation_rule _\n\nself = <tests.concorde.dogfooding.test_dogfooding.ConcordeRepositoryTests testMethod=test_the_repository_instructions_take_reports_and_share_the_observation_rule>\n\n    @verifies(\"scenario.dogfooding.concorde-instructions\")\n    def test_the_repository_instructions_take_reports_and_share_the_observation_rule(\n        self,\n    ):\n        instructions = words((REPOSITORY_ROOT / \"AGENTS.md\").read_text())\n        for fragment in (\n            \"## Defect reports from develop installs\",\n            \"python3 scripts/issues.py report --file <report> --task <task>\",\n            \"Fix a Concorde implementation bug\",\n            \"ask the developer before changing Concorde's design or Protocol or loosening any boundary\",\n            \"`--reason not-actionable`\",\n            \"Fix the defect generally, never only for the reporting project\",\n        ):\n>           self.assertIn(words(fragment), instructions)\nE           AssertionError: '## Defect reports from develop installs' not found in \"# Developing Concorde with pi These instructions apply to pi only, including when both `AGENTS.md` and `CLAUDE.md` are loaded. Claude Code follows `CLAUDE.md` for its host workflow. Read [DEVELOPING.md](DEVELOPING.md) in full before working on this source checkout. It contains shared development rules, preparation, verification, delivery, merge checks and defect handling. ## Main session Stay in the primary worktree. Open a task as described in `DEVELOPING.md`, then start a Concorde task session in its worktree even for a single task. pi has no EnterWorktree or ExitWorktree tool; a shell `cd` changes only that command's working directory, not the session's context. 1. Open the task from the primary worktree and obtain its path with `python3 scripts/concorde.py task show <task>`. 2. Before starting the session, run `python3 scripts/development/init-references.py` from that task worktree, using its own script. The task session cannot register submodules in the shared Git configuration. 3. Use `concorde_task_session` when available. Without that extension, run `CONCORDE_CLIENT=pi python3 scripts/concorde.py task session <task> --main <its session name>` from the primary worktree. This starts pi in the task worktree; use `--answer` on the same command for a subsequent round, or the tool's `answer` input when using the extension. 4. Monitor the session's recorded result and read any escalation's complete chain with `python3 scripts/concorde.py task show <task>`. Record decisions, answer escalations within your authority, and have the session finish validation and delivery. 5. After delivery, inspect the result and merge from the primary worktree with the command and both merge checks in `DEVELOPING.md`. For several tasks, start one session per task and coordinate their results from the primary worktree. Do not edit task sources from the primary pi session or treat shell `cd` as entering a task. If a merge conflicts, the main agent arranges the Git resolution in the task worktree, then resumes its task session for verification and delivery before retrying the checked merge. ## Task session If you are already a Concorde task session in your assigned worktree, do the task directly there. Do not launch another session. Use that worktree's own `python3 scripts/concorde.py`, run commands and Operations in foreground Bash, and follow the task-session prompt for decision logging, escalation and the final `concorde_report`. Validate and deliver; leave merging to the main agent.\"\n\ntests/concorde/dogfooding/test_dogfooding.py:227: AssertionError\n_ RepositoryCheckPreparationTests.test_real_registry_listing_roots_are_copied __\n\nself = <tests.concorde.views.test_repository_checks.RepositoryCheckPreparationTests testMethod=test_real_registry_listing_roots_are_copied>\n\n    @verifies(\"scenario.views.load-registry\")\n    def test_real_registry_listing_roots_are_copied(self):\n        wrapper = load_wrapper()\n>       self.assertEqual([], wrapper.uncopied_listing_roots())\nE       AssertionError: Lists differ: [] != ['CLAUDE.md', 'DEVELOPING.md']\nE       \nE       Second list contains 2 additional elements.\nE       First extra element 0:\nE       'CLAUDE.md'\nE       \nE       - []\nE       + ['CLAUDE.md', 'DEVELOPING.md']\n\ntests/concorde/views/test_repository_checks.py:37: AssertionError\n---------------------------- concorde test evidence ----------------------------\nreason=manual scope=unspecified phase=unspecified attempt=1 workers=in-process\ndiscovery 0.1s, elapsed 0.1s; unit time 0.0s is summed concurrent work, not wall time\n=========================== short test summary info ============================\nFAILED tests/concorde/dogfooding/test_dogfooding.py::ConcordeRepositoryTests::test_the_repository_instructions_take_reports_and_share_the_observation_rule\nFAILED tests/concorde/views/test_repository_checks.py::RepositoryCheckPreparationTests::test_real_registry_listing_roots_are_copied\n============================== 2 failed in 0.09s ===============================\n",
      "evidence": [
        {
          "kind": "log",
          "ref": "/tmp/concorde-ts-85aad5427229/split-agent-instructions-layout-failures.log",
          "detail": "Complete targeted reproduction of both remaining full-suite failures."
        }
      ],
      "attempts": [
        "Full suite: 572 passed, 4 skipped, 3 failed.",
        "The temporary-directory failure passed when CONCORDE_CHECK_TMPDIR was set to the existing session TMPDIR.",
        "Reproduced the two instruction-layout failures with pytest -n 0."
      ],
      "unhandled": {
        "reason": "scope",
        "explanation": "The fixes require module.dogfooding and module.views; this task is bound only to module.concorde."
      },
      "options": [],
      "recommendation": "Authorize the minimal existing-test and docsite copy-list adaptations.",
      "causes": []
    }
  ]
}
```

## Round 2 authorization and decisions

- The main agent approved expanding this task to module.dogfooding and module.views solely for the existing instruction test and repository-check copy list. Read both complete Specs and metadata before editing. Register the expansion through an Operation with all three Modules.
- Preserve every existing defect-handling and shared-observation assertion; read those rules from DEVELOPING.md and additionally require both host entries to instruct reading that shared file in full. Add only the two new files to the docsite copy list. No runtime changes or relaxed assertions.
- Round 1 report attempts failed because the exposed schema required a commit field but the escalated-report handler rejected its presence. The supervisor recorded session_no_report. Delivery in this round will provide its verified commit and must end with a successful concorde_report.

## Main-agent review follow-up

The new Dogfooding test reads CLAUDE.md and DEVELOPING.md, but check.dogfooding.tests in .concorde/config.json still fingerprints only AGENTS.md. Add both new files to that check's inputs so later edits invalidate its evidence. Add all three instruction files to check.views.repository-regressions inputs as they are copied and validated there. This narrow project-check configuration update is authorized as part of the same split. Preserve all existing inputs and checks. Revalidate and deliver after this adjustment; do not merge with stale check inputs.

## Bounded handoff after round 2

- Main agent authorized adding CLAUDE.md and DEVELOPING.md to check.dogfooding.tests inputs and all three instruction files to check.views.repository-regressions inputs. Preserved every existing input and check; no runtime changes.
- uvx initially failed creating /home/zhenyu/.local/share/uv/tools/.tmpNmel44 (read-only filesystem). Retried with UV_TOOL_DIR in the existing writable session TMPDIR; Ruff format and its idempotence check passed. Prettier format and idempotence checks passed for all changed Markdown/JSON. An exploratory run-path search used the task-local .concorde/runs path and found none; Operation evidence actually lives in the primary repository run store.
- validate Operations r-20260926T182949-validate-f69e13dd and r-20260926T183428-validate-eb1e721b were blocked by check.views.publication-types and check.views.repository-regressions: npm reported "Exit handler never called!" during fresh dependency installation. Both complete error chains and logs remain in the Operation records. Other selected checks passed. The check service intentionally passes PATH/LANG and configured env; the session network proxy is absent there. A diagnostic direct check invocation with inherited session environment passed the docsite type check, without changing its read-only boundary. This is diagnostic evidence, not a substitute for configured validation. A direct repository-check diagnostic was interrupted by the main agent; no success is claimed.
- The main agent explicitly stopped further runtime/network investigation and will run normal validate/delivery Operations on the host, from this task worktree with its branch scripts and ordinary check boundary. No more Operations will run inside this task session.
- The report tool schema problem remains recorded: it requires commit in the exposed call schema, but rejects any commit field for escalated reports. The main agent explicitly authorized an ordinary final status for this bounded handoff; do not fabricate a delivery commit or new escalation.
- After the final configuration edit: build --check passed; structural validate passed with zero errors, warnings or infos; relevant Python tests passed (51); final full pytest with CONCORDE_CHECK_TMPDIR=$TMPDIR passed (575 passed, 4 skipped). All changes are ready for a source commit, with host Operations still pending.

- Inspected the complete staged diff and committed the seven verified files as f02c9be0f43bf71ce7a8600b9c3cdeb463b295b4 (source commit, not delivery). Post-commit status has no tracked changes; sandbox-protected placeholder paths remain untracked and were not staged. Host validate and delivery for all three Modules remain the main agent's next step.

## Main-agent host verification

- Reviewed all seven changed files and confirmed shared defect-handling and verification rules are preserved, host workflows are explicitly scoped, and both new instruction files participate in check input fingerprints.
- Stopped round 2 to bound investigation of npm failures in nested task-session/check execution. Round 3 was explicitly limited to final edits, formatting, tests and a verified commit, followed by a plain handoff. Its supervisor session_no_report is expected from that authorized handoff and is not delivery evidence.
- Final full suite after the configuration change: 575 passed, 4 skipped; targeted Python checks: 51 passed. Source commit f02c9be0f43bf71ce7a8600b9c3cdeb463b295b4.
- Ran the branch copy of validate from the task worktree under the main host, preserving the standard read-only check boundary. Run r-20260926T184210-validate-8aed1fbf passed all six configured checks with zero findings, including both npm-dependent checks. No check was disabled, no sandbox rule was loosened, and no runtime source was changed.
- Delivery is being run from the same task worktree under the main host. The task session report-schema incompatibility and nested-check npm failures remain recorded for separate investigation, outside the instruction split.

## Closed: merged, 2026-09-26T18:49:52Z

- Delivery r-20260926T184600-delivery-8a5ded3b passed all six configured checks and recorded commit 4e7f9146e1e9bdecbe8458cbeef59959be8081ac. Checked task merge succeeded with build and structural validate both exit 0; task closed as merged and its worktree removed.

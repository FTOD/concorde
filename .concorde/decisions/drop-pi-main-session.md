# Decision log: drop-pi-main-session

Goal: Stop supporting pi on the main-session side: the main agent and task sessions run on Claude Code only, while pi stays a worker backend; remove pi main-session guidance, the pi extension and run view, pi task sessions with their rounds and session reports, and the pi headless main sessions of the end-to-end tools, from Specs, glossary, code, prompts, installer, docs and tests

## Brief (main agent, 2026-09-29)

Developer's decisions this task carries out:

- For now Concorde's main-session side supports Claude Code only: the main agent is a Claude Code
  session, and since a task session always runs on the main agent's program, task sessions are
  Claude Code sessions only. The developer rarely uses pi now and wants the design simpler.
- pi stays a **worker backend** unchanged: `pi -p` workers, the permission extension generated
  from a grant, `backend: "pi"` in `.concorde/workers.json` and pi being the default worker
  backend all stay. Do not touch worker-side pi support.
- No backward compatibility or migration shims (rapid-iteration rule).

What to remove or rewrite (find everything; this list is a start, not the whole scope):

- pi main-session guidance and installation: the pi project skill / pi extension install in
  Distribution, `src/concorde/main_session/pi_extension.ts` and `pi_runs.ts` (the `concorde_run`
  and `concorde_task_session` tools and the run view), and their build outputs.
- pi task sessions: `src/concorde/tasks/pi_session.py`, `pi_session.ts`, `pi_session_policy.ts`,
  the `--answer`, `--stop`, `--wait` options of `task session` if they exist only for pi, the
  session rounds and session reports, and the Harness's pi boundary extension for task sessions
  (keep the worker permission extension).
- Glossary: remove `concept.run-view`, `concept.session-round`, `concept.session-report`; rewrite
  `concept.main-agent`, `concept.task-session`, `concept.session-boundary`,
  `concept.headless-session`, `concept.main-session-guidance` and any other entry that names pi as
  a main-session or task-session program.
- Specs of Main session, Task session, Tasks, Coordination, root Module, Tracing (trace nodes of
  session rounds), Harness (session boundary on pi), Distribution, E2E and its Headless sessions
  (drop `pi -p` main sessions) and Dogfood scenarios, Dogfooding; prompts under
  `prompts/main-session/`, `prompts/development/`, `prompts/dogfooding/`; `docs/`; `AGENTS.md` and
  `CLAUDE.md` where they mention pi main sessions; tests.
- The Specs should say explicitly that the main agent and task sessions run on Claude Code only
  for now, while workers may run on pi.

Left to the session: exact wording, how to restructure Specs whose content shrinks, and which
tests to delete versus adapt. Escalate if removing something would also remove worker-side pi
support or if a Spec promise outside this scope must change.

Context: this is the first of two tasks. The next task (opened after this one merges) adds a
project-level stdio MCP server for task and trace management with non-blocking lock acquisition
and a `register_wait` that wakes the session through Claude Code channels. Do not start that
work here.

## Task session (2026-09-29)

- Decided: `concorde task session` always starts a Claude Code task session; it no longer reads the
  main session's program, so `--answer`, `--stop`, `--wait` and the `client_unknown` and
  `session_busy` refusals go. Reason: a task session runs on the main agent's program, which is now
  Claude Code only.
- Decided: the session trace (`concorde-session-trace`) drops its `program` field and the trace
  node kind `round` and metadata key `program` go from Tracing, since only Claude Code sessions
  remain and they have no rounds. No compatibility for pi sessions in older history (rapid
  iteration).
- Decided: the checkout's `.pi/settings.json` (pi dev session loading the extension and skills) is
  removed; `scenario.concorde.pi-extension-in-checkout` goes and the development-skills test checks
  the `.claude/skills/<name>` links instead.
- Decided: the E2E tools' pi work (scripts/e2e, tests/concorde/e2e, specs/concorde/e2e) is done by a
  helper subagent of this session under my brief, reviewed by me before commit.
- Found outside the task's Modules (to escalate together at the end): `detect_client` /
  `CONCORDE_CLIENT` live in `src/concorde/harness/models.py` and the Workers Spec
  (module.workers); the pi rendering of workflows (`src/concorde/workflows/scripts/pi.js`, the pi
  step and report agents, `.concorde/workflows/pi/`) belongs to module.workflows. Left untouched
  for now.
- Decided: the installer no longer amends a project's `AGENTS.md`; its only stated reason was that
  pi reads AGENTS.md before CLAUDE.md. `scenario.distribution.agents-md` and
  `req.distribution.agents-md-block` go. Projects installed earlier keep a stale block until the
  developer removes it (no migration, rapid iteration).
- Decided: `install-concorde.py --pi` and `concorde update --pi` are removed with the receipt's
  `pi` field; `pi_runtime` stays. Distribution scenarios: `install-pi`, `update-add-pi` removed;
  `update-pi` -> `update-pi-runtime`, `update-keeps-pi-choices` ->
  `update-keeps-pi-runtime-choice`; `install-later-files-bound` is now tested by simulating an
  older install that lacked the brownfield workflow.
- Decided: `prompts/main-session/common/` (snippets shared by the Claude Code and pi task-session
  prompts) is inlined into the one task-session prompt.
- Decided: `docsite/tests/repository/run-checks.py` stops copying the deleted `.pi/settings.json`
  (a one-line consequence of the deletion; the file belongs to the docsite checks, outside the
  task's Modules, and is listed in the escalation).
- Spec rewrites are split among helper subagents of this session per Module group (Coordination;
  Harness, Tracing, Distribution; root, Execution, Dogfooding, docs) under one shared brief; I
  review every change before committing.
- Decided: the checkout's `AGENTS.md` ("Developing Concorde with pi") is deleted: it was the pi
  twin of `CLAUDE.md`, describing `.pi/settings.json`, the pi extension and
  `concorde_task_session`, and nothing else reads it. Its references go from the Dogfooding and
  Views checks' inputs (`.concorde/checks/module.dogfooding.json`, `module.views.json`), the
  docsite repository check's copy list, and the pytest timing fingerprint (now `CLAUDE.md`).
  `module.views` is outside the task's Modules; listed in the escalation.

## Escalated to the main agent, 2026-09-29T13:44:20Z

- **task-session** task session (task drop-pi-main-session): `modules_outside_task`
  Everything in the task's Modules is done and committed (fdc97452; full suite 763 passed, build --check clean). Removing pi from the main-session side reaches four Modules the task does not list. (1) module.workers: specs/concorde/execution/workers/module.md and launch.md still link the removed concept.run-view (the only 2 spec-validation errors, so delivery is blocked); detect_client and CONCORDE_CLIENT in src/concorde/harness/models.py are now unused (only their own test in tests/concorde/harness/workers/test_models.py and env settings in test support use them); the Workers Spec describes reading the main session's program ('Concorde's pi extension sets it to pi') with a client-detection scenario; scenarios pi-fenced-run and pi-runtime-missing start 'from a pi main session'; src/concorde/harness/progress.py mentions the run view. (2) module.workflows: the build still renders pi-subagents workflow scripts and the pi step/report agents (generated/workflows/pi/, workflow step/report --stdin, glossary concept.step-agent and concept.workflow 'rendered for Claude Code and pi'), which the installer no longer installs and no main session runs; the E2E deterministic driver and the workflow tests run that pi rendering under a stand-in, so removing it means moving them to the Claude Code rendering. (3) module.spec: docstrings in src/concorde/spec/initialize.py and validation.py and one scenario in spec-tooling/spec/scenarios.md mention pi files installed with --pi. (4) module.views: I already removed the deleted .pi/settings.json and AGENTS.md from docsite/tests/repository/run-checks.py and AGENTS.md from .concorde/checks/module.views.json, because the checks would otherwise fail on missing files.
  Not handled here (decision): The task's Modules do not include module.workers, module.workflows, module.spec or module.views, and whether to remove the pi workflow rendering changes what module.workflows promises.
  Options: A: add module.workers, module.spec and module.views to this task; remove detect_client/CONCORDE_CLIENT and fix the Workers Spec (run-view links, main-session program text, pi-main-session wording) and the Spec-tooling mentions here; leave the pi workflow rendering to a follow-up task on module.workflows; B: as A, and also add module.workflows and remove the pi workflow rendering here, moving the E2E deterministic driver and workflow tests to the Claude Code rendering; C: add only module.workers and fix just the two dangling concept.run-view links; everything else goes to follow-up tasks
  Recommendation: A: it unblocks delivery and removes the dead client detection with small, contained changes, while the workflow rendering and its test driver are a separate decision better taken in their own task

```json
{
  "level": "task-session",
  "actor": "task session (task drop-pi-main-session)",
  "code": "modules_outside_task",
  "detail": "Everything in the task's Modules is done and committed (fdc97452; full suite 763 passed, build --check clean). Removing pi from the main-session side reaches four Modules the task does not list. (1) module.workers: specs/concorde/execution/workers/module.md and launch.md still link the removed concept.run-view (the only 2 spec-validation errors, so delivery is blocked); detect_client and CONCORDE_CLIENT in src/concorde/harness/models.py are now unused (only their own test in tests/concorde/harness/workers/test_models.py and env settings in test support use them); the Workers Spec describes reading the main session's program ('Concorde's pi extension sets it to pi') with a client-detection scenario; scenarios pi-fenced-run and pi-runtime-missing start 'from a pi main session'; src/concorde/harness/progress.py mentions the run view. (2) module.workflows: the build still renders pi-subagents workflow scripts and the pi step/report agents (generated/workflows/pi/, workflow step/report --stdin, glossary concept.step-agent and concept.workflow 'rendered for Claude Code and pi'), which the installer no longer installs and no main session runs; the E2E deterministic driver and the workflow tests run that pi rendering under a stand-in, so removing it means moving them to the Claude Code rendering. (3) module.spec: docstrings in src/concorde/spec/initialize.py and validation.py and one scenario in spec-tooling/spec/scenarios.md mention pi files installed with --pi. (4) module.views: I already removed the deleted .pi/settings.json and AGENTS.md from docsite/tests/repository/run-checks.py and AGENTS.md from .concorde/checks/module.views.json, because the checks would otherwise fail on missing files.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The task's Modules do not include module.workers, module.workflows, module.spec or module.views, and whether to remove the pi workflow rendering changes what module.workflows promises."
  },
  "options": [
    "A: add module.workers, module.spec and module.views to this task; remove detect_client/CONCORDE_CLIENT and fix the Workers Spec (run-view links, main-session program text, pi-main-session wording) and the Spec-tooling mentions here; leave the pi workflow rendering to a follow-up task on module.workflows",
    "B: as A, and also add module.workflows and remove the pi workflow rendering here, moving the E2E deterministic driver and workflow tests to the Claude Code rendering",
    "C: add only module.workers and fix just the two dangling concept.run-view links; everything else goes to follow-up tasks"
  ],
  "recommendation": "A: it unblocks delivery and removes the dead client detection with small, contained changes, while the workflow rendering and its test driver are a separate decision better taken in their own task",
  "causes": []
}
```

## Main agent's answer to escalation #1 (2026-09-29)

Decision: option A, taken by the main agent without the developer (ordinary scope: it follows
directly from the developer's decision to drop pi on the main-session side, and only splits the
work). The task session may change module.workers, module.spec and module.views in this task:
remove `detect_client` / `CONCORDE_CLIENT` and their tests and settings, fix the Workers Spec
(the dangling `concept.run-view` links, the client-detection text and scenario, the scenarios that
start "from a pi main session", the run-view mention in `harness/progress.py`) and the
Spec-tooling mentions of pi files installed with `--pi`. The task record's module list cannot be
amended by any `task` command, so this entry is the authorization. Worker-side pi support stays
untouched.

The pi workflow rendering (module.workflows: `generated/workflows/pi/`, the pi step and report
agents, `workflow step/report --stdin`, the glossary's `step-agent` and `workflow` wording, and
the E2E deterministic driver and workflow tests that run it) is left out of this task: the main
agent opens a follow-up task on module.workflows after this one merges.
- Carried out the main agent's answer to escalation #1 (option A): removed `detect_client` /
  `CONCORDE_CLIENT` with `scenario.workers.backend-from-client` and its test, and the
  `client` parameter of the test support's `OperationProject.run`; fixed the Workers Spec (run-view
  links, main-session program text, scenarios no longer start "from a pi main session") and
  `harness/progress.py`; Spec tooling's docstrings and `scenario.spec.installation-follows-record`
  now speak of files a newer Concorde installs instead of pi files (tests use `.claude/` paths).
  The pi workflow rendering is left for the follow-up task. spec-validation: success, 0 findings;
  full suite 762 passed, 4 skipped.
- task-validation blocked: check.task-session.tests still ran the deleted tests/concorde/tasks/test_pi_session.py (pytest exit 5, no tests ran). Repaired by removing it from .concorde/checks/module.task-session.json.

## Closed: merged, 2026-09-29T14:04:58Z

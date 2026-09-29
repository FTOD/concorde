# Decision log: execution-tools-spec

Goal: Define Tool alongside Worker, group deterministic execution tools, and reconcile Workflow/Operation/Worker/Tool Specs including workflow portability

## Scope and decisions

- The developer authorized adding Tool as a peer of Worker and reconciling the agreed execution model across the Specs.
- Use one task worktree for direct maintenance. EnterWorktree is not exposed in this pi session, so every source edit uses the task's absolute path and every command runs with that worktree as its explicit directory.
- Add the canonical Tool concept to the shared vocabulary and a Tools composite containing Check execution. Keep Check execution's identity, paths, code bindings and consumer dependencies; composition changes the docsite reading tree without combining permissions.
- Workflow is the orchestration layer above Operations. One authored JavaScript procedure already renders to Claude Code and pi-subagents workflows, so describe that existing ability and its adapter limits, not an unimplemented general converter.
- Operations combine host control logic, workers and Tools; zero-worker Operations remain valid. Workers names the host lifecycle code, distinct from an AI worker. That code calls Check execution after clean audits.
- Review Tasks, Spec core and Harness as distinct lifecycle/specification/confinement responsibilities, not Tools merely because they contain deterministic code. Private host helpers remain with their current owner.
- Fix stale Check execution text claiming its service is not written, and conflicting Workflow/Operation wording about who may sequence Operations. No runtime or wire-contract change is intended.

## Spec review

Reviewed the complete root, Workflows, Operations, Agents, Workers and Check execution Specs against the agreed model. This was a direct review by the editing agent, not an independent model review.

- Define Tool once in the root vocabulary, beside Worker, and import it where used. Separate the execution hierarchy from agent responsibility levels and Module composition.
- Make Workflows explicitly orchestrate Operations. Retain one authored procedure and the existing Claude Code/pi adapters, with equivalent steps, arguments, branches, admitted inputs and decision points; do not imply conversion of arbitrary plans or removal of Operation hosts.
- Keep worker lifecycle and Tool calls inside Operations; distinguish platform relay/command-runner agents from Concorde workers. Deterministic Operations remain Operations.
- Keep Checks as a host-side service with actual callers named. Fix the stale implementation claim, preserve its boundary limitations and input-bound evidence, and preserve child ownership under Tools.
- Correct Workers' caller description to include existing reading runs without tasks as well as writing runs in task worktrees.
- Existing result/error contracts and scenarios remain compatible; no new wire shape, dispatcher or agent permission is introduced.

## Verification

- `registry --write` followed by `registry --check`: current; a second refresh made no change.
- Changed metadata and registry match canonical JSON formatting on the second pass.
- `build --check` and `validate`: pass, zero findings.
- Final `.venv/bin/python -m pytest`: 575 passed, 4 skipped.
- Docsite validation: 30 Modules, 110 documents; final production build passes with internal link and anchor checks. Published Checks sidebar shows Tools and Check execution at their expected routes.
- Validate Operation `r-20260926T180446-validate-2d9b962a`: ready, all 16 configured checks passed, no blockers or warnings; host result and check evidence inspected.
- Spec step committed as `1ae8a46f0ea2fd045cf3c30e83d1c339ad0df6bb` after inspecting the staged diff.
- Delivery Operation `r-20260926T180706-delivery-d2283804`: ready, all 16 checks passed again; evidence bundle and delivery commit `46e626a4961d119e3d87ff36ea6ba64ed270b448` inspected. Delivery changed only the evidence bundle.
- `task merge execution-tools-spec` fast-forwarded local main to `46e626a4961d119e3d87ff36ea6ba64ed270b448`; main's build and validate both passed. Task closed as merged, task worktree removed, primary working tree clean. No push or publication performed.

## Closed: merged, 2026-09-26T18:08:30Z

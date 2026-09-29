# Decision log: spec-diagram-guidance

Goal: Improve Spec readability by making diagrams an active authoring choice for relationships and behaviour, prompted by the root Concorde Usage / A normal path. Read DEVELOPING.md, canonical principles, and complete affected Specs. Update canonical protocol/module.md authoring guidance and protocol/templates/module.md, shared worker spec-format prompt and spec-review checklist coherently: use diagrams wherever they make relationships, order, branching, state or data clearer; select sequence diagrams for multi-actor normal paths, activity/flow diagrams for branches and retries, state diagrams for lifecycle, component/context/deployment/data-model views when appropriate. All diagrams remain D2; checked diagrams use only declared static relations and the semantic subset, all other views use d2 illustrative. Explicitly allow Usage diagrams next to normal paths, with design diagrams in Design. Preserve explanatory prose, one clear question per diagram, consistent terminology, no diagram quotas or invented promises; review missing helpful diagrams as concrete advisory readability findings unless meaning is actually insufficient. Add a concise D2 illustrative sequence diagram next to root specs/concorde/module.md A normal path, covering user-facing task lifecycle (primary worktree, task worktree, execution, validation, delivery, main-agent merge), complementary to the existing deeper Design sequence. Keep scope focused; this is editorial guidance under existing Protocol semantics, no new diagram language or checker. Refresh protocol manifest and bound project copy as required. Verify generated prompts, D2 render/docsite, required checks and full suite per DEVELOPING.md; commit, task-validation, delivery, concorde_report. Main session will review and merge.

## Main-session scope and editorial decisions

The developer requested stronger diagram guidance for Spec readability and pointed to the root normal path. Update the canonical guide, template, shared authoring prompt and review checklist, and demonstrate the guidance in that root Usage section. Keep existing D2 syntax, checked/illustrative authority and prose requirements; this is an editorial improvement without a new Protocol rule or checker. Prefer concrete diagram choices by the reader question, not diagram counts. Missing a useful view alone warrants advisory feedback; actual insufficient meaning follows existing review severity.

The MCP search exposed no concorde_task_session tool, so use the documented CONCORDE_CLIENT=pi CLI fallback. Reference initialization succeeded before starting the task session. Exploratory searches encountered a nonexistent .pi directory and an unset optional PI_SESSION_NAME; these do not block the work, and PI_SESSION_ID identifies the main session.

## Task-session authoring decisions

- Keep this an editorial change under Protocol 14.0.0: broaden the existing diagram guidance, template, common authoring prompt and review checklist without changing declarations, checks or contracts. Existing checked/illustrative semantics already cover every requested view.
- Place one illustrative sequence immediately after the root normal-path paragraph. Show task-level roles and worktree locations, execution, validation, delivery and the main agent merging; retain the deeper Design sequence for internal collaboration details.
- Use existing build, structural, publication and test checks rather than add tests that merely match editorial wording. Inspect the generated authoring/reviewer prompts and render the actual new diagram as publication evidence.
- Preparation succeeded: all reference submodules are initialized, dependencies installed and baseline build passed. uv fell back from hardlinks to copies; npm reported existing deprecated dependencies and 31 audit vulnerabilities. These dependency warnings do not block the editorial task; no dependency or lockfile change is in scope. Sandbox placeholder files shown by Git are not task changes and will never be staged.

## Developer correction: process views and lightweight workflows

The developer corrected the emphasis: showing a process is the reason to use a flow-oriented diagram, not the number of interacting parties or the normal-path label. Formal sequence diagrams can be heavy. They prefer diagrams like Archify workflow Agent Tool Call (https://tt-a1i.github.io/archify/gallery.html#proof-agent-tool-call). Main session fetched the gallery and exact JSON IR: actions/steps, directional edges, optional responsibility lanes and phases, a visible main path with branches/recovery separated. Use that as the visual model for lightweight workflow diagrams, with sequence diagrams when message order itself benefits from lifelines. This supersedes the original goal wording that prioritized sequence diagrams for multi-actor normal paths, including the root example: make it a lightweight workflow, not a mandatory sequence. Stopped round 1 to incorporate the correction before validation; this was intentional steering, not a failure. Keep D2 as existing Spec format and express the pattern with illustrative D2.

## Task-session response to developer correction

- Supersede the earlier sequence choice with a lightweight D2 workflow. Canonical guidance, template, common authoring prompt and reviewer checklist now start with process progression, independent of actor count; sequence diagrams explain participant message ordering.
- Demonstrate the template with placeholder steps rather than invent a service promise. Show the root path in two responsibility/worktree groups with step edges; retain the deeper Design sequence unchanged. Use D2 grids for a compact layout because default layout stretched the first draft to 2413 SVG units wide.
- The new root and template diagrams compile with D2 v0.9.0. Inspect SVG text and geometry as well as full publication output; this task model cannot view image attachments, so do not claim a visual screenshot review. Build and protocol-manifest refresh succeeded; the bound copy and digest are updated without a Protocol version change.

## Verification preparation result

- Structural validation passed with zero errors/warnings; full Python suite passed, 623 passed and 4 skipped.
- `npm --prefix docsite run check` stopped at its first typecheck (exit 2): `sidebars.specs.ts(1,22): error TS2307: Cannot find module './.generated/specs-sidebar.json' or its corresponding type declarations.` The fresh worktree has not staged publication output. Build the docsite to generate its sidebar, then rerun the complete docsite check; no source change is needed. Full log: task worktree `.concorde/diagram-guidance/docsite-check.log`.

## Publication verification

- Full docsite check passed after staging: TypeScript, 239 tests in 20 files, publication validation (31 Modules / 115 documents), and production build. Docusaurus could not check for an update because the sandbox protects the user config store; publication itself succeeded.
- The ad hoc published-page inspection used the wrong output path (`.../module/index.html`) and failed with FileNotFoundError. This site publishes `.../module.html`; inspect that actual path. Prompt inspection passed for specify, code-to-spec, review-spec, panel-spec and both generated/bound Protocol guides.

- Follow-up page assertion initially expected SVG labels inline in HTML and failed (`AssertionError: enter or delegate`). The publisher correctly uses an external SVG image. Reading the actual image referenced by the normal-path section confirms all workflow labels; HTML marks it illustrative/non-normative and gives its published dimensions as 799 by 638. No product defect or source repair was needed.
- Move ad hoc validation/render files into ignored `.concorde/runs/diagram-guidance-verification/` before delivery so they are not staged as project sources. Retain their logs as local evidence.

## Verified change and readiness

Committed the inspected nine-file change as `39fb96e1` (Clarify Spec diagram choices and illustrate the task workflow). The only working-tree entries afterwards are sandbox-protected placeholders. `build --check` passes, the generated and bound guide bytes match, and `task-validation` run `r-20260927T164540-task_validation-ac960d30` reports ready: 9 changed paths, all 23 configured checks passed, zero warnings. Run delivery now to revalidate and commit its evidence as required.

## Main-session review

Reviewed the source diffs and generated prompt inclusions. The revised guidance follows the developer correction: process views use lightweight action/step graphs with optional lanes; sequence views explain message order. The root example groups primary and task worktrees and returns delivery to main-agent merge. It introduces no new behaviour, relation or diagram language. Verified generated specify/code-to-spec and ordinary/panel review prompts include the shared guidance. Read task-validation result: ready, no blocking findings, warnings or confirmations. Accept for checked merge after the session delivers.

## Delivery

Delivery run `r-20260927T165040-delivery-a4226a76` succeeded after independently repeating all 23 configured checks, zero warnings. Delivery commit: `2257c840fcb4f1463f8767ca70674b26e555eccc` (parent `39fb96e1c7243c5df92156221df8079dd35cff64`). It commits the readiness/delivery evidence; no tracked source remains dirty. No escalation or implementation issue remains. The main agent owns final review and checked merge.

## Closed: merged, 2026-09-27T16:56:12Z

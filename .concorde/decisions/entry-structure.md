# Decision log: entry-structure

Goal: Free the Module entry from a mandatory section skeleton in the Spec Protocol, its checks, template and Spec-writing prompts, prefer workflow over sequence diagrams, and rewrite the root Spec as purpose, core concepts (merging core-concepts.md), overview diagrams, then details

## Brief (main agent, 2026-09-30)

### Why
The developer criticized the root Spec (`specs/concorde/module.md`): (1) its Usage section is
useless; (2) how the main agent opens and delegates a task is unimportant yet comes first — every
Spec should start with its purpose, then its core concepts, then diagrams of the system's main
functions and flows; (3) a forced Design section is pointless: the whole Module Spec is the design,
something a developer can understand quickly; (4) `specs/concorde/core-concepts.md` should be merged
into the root Spec; (5) the sequence diagram is too heavy, a workflow diagram is preferred. They
asked not only to fix the root Spec but to find and fix what in the Spec Protocol and the
Spec-writing prompts caused this.

Main agent's root-cause analysis (verify and extend it):
- `protocol/format.md` "Reading structure" and `protocol/checks.md` (`CHK.document.sections`,
  `CHK.document.prose`, enforced in `src/concorde/spec/syntax.py` `READING_SECTIONS` /
  `entry_section_problems`) require exactly Purpose, Usage and Design; `protocol/module.md` "The
  entry" asks Usage to follow entry points and a representative input first, which for the root
  meant a command walk-through; Design became a catch-all that pushed the core ideas behind it.
- `protocol/module.md` "Document roles" licenses a topic for "the words several Modules share",
  which is how `core-concepts.md` came to exist.
- The diagram table in `protocol/module.md` and `prompts/workers/common/spec-format.md` send
  "participant message ordering" to a sequence diagram, so cross-Module interactions default to one.
- The template `protocol/templates/module.md`, `src/concorde/spec/initialize.py`
  (`initial_module_text`), `prompts/workers/common/spec-format.md`,
  `prompts/workers/spec-review/checklist.md`, `prompts/workers/code-to-spec.md` and
  `prompts/workers/specify.md` all repeat the three-section skeleton. Check the rest of `prompts/`
  (e.g. `survey.md`, `panel-spec.md`, `prompts/protocol/`, `scaffold` output in
  `src/concorde/scaffold/command.py`) and `docs/` for the same assumption.

### Developer's decisions (AskUserQuestion, 2026-09-30)
1. **Nothing is enforced**: the Protocol requires no level-2 section in an entry — Purpose is only a
   recommendation, Usage and Design are not required. Remove the section check (`CHK.document.sections`
   and the Usage/Design part of `CHK.document.prose`; keep only what still makes sense, e.g. no
   check at all, or a warning-free rule set — decide and log it). Whether the ban on a
   `Relationships` section survives is yours to decide in the spirit of "nothing enforced"; log it.
2. The Protocol **recommends** the reading order: purpose → core concepts (the Module's own terms,
   explanation anchors in the entry) → overview diagrams of main structure, functions and flows with
   short prose → details (parts, collaborations with children and providers — the `contains`/`uses`
   meaning anchors —, entry points, errors, design reasons). The whole entry is the design; the
   design still never moves to a separate topic, and concept explanations belong in the owning
   entry, not a separate concepts topic. The semantic reader requirements (a newcomer can explain the
   problem, when to use it, a normal interaction, stopping conditions, why the design holds) stay.
3. **Diagrams: workflow by default**: any process, including cross-Module interactions, is a
   workflow diagram with lanes per participant when useful; a sequence diagram only when the
   interleaving of messages is itself the point. Update the Protocol table, template and prompts.
   Replace the root's sequence diagram; the other 4 entries with sequence diagrams are converted by
   later tasks, not here.
4. **Root Spec**: remove the command walk-through (`concorde task open retry-limit …`) and the
   command → Module table from the root; command-level detail belongs to Main session / Tasks,
   whose Specs already cover it (check; if something would be lost, move it there only if it is
   not already stated — that touches other Modules, so escalate instead of editing them). The root
   keeps at most a concept-level workflow diagram of a task's life. Merge `core-concepts.md` into
   `module.md` (delete the topic, drop it from `owns`, move the concept anchors, repoint the 14
   glossary `explanation`s and every link to `core-concepts.md`).
5. The other 30 entries are restructured by later tasks after this one merges — **not here**. They
   must remain valid under the new rules.

### Left to the session
Exact Protocol wording, version bump (run `protocol-manifest --write --bind-project`), how the
check list changes, the test changes, the root's new heading structure and diagrams (render each D2
diagram and look at it before keeping it). Remember the Spec core Module's own Spec describes these
checks and must follow. Report back with a short summary of the Protocol change so the main agent
can brief the restructuring tasks for the other entries.

## Task session decisions (2026-09-30)

### Protocol 15.1.0: no required entry sections
- **Checks removed entirely.** `CHK.document.sections` and `CHK.document.prose` are deleted from
  `protocol/checks.md`, `model.yaml` and the validator (`entry_section_problems`,
  `READING_SECTIONS`, `FORBIDDEN_SECTIONS` in `src/concorde/spec/syntax.py`). No replacement rule:
  "Purpose is plain prose" would re-impose a Purpose section, and an empty entry is already refused
  by the nonempty-reading rule of `CHK.document.pair`. Reason: the developer chose "nothing
  enforced".
- **The `Relationships` ban is dropped too**, in the spirit of "nothing enforced". Writing guidance
  keeps it as advice: how a Module fits with the rest is part of its explanation, and a separate
  list that only repeats it adds nothing.
- **Version 15.1.0** (manifest, README, principles, model.yaml, `PROTOCOL_VERSION`), bound with
  `protocol-manifest --write --bind-project`. Minor bump because it only relaxes: every 15.0
  specification stays valid. `protocol/migration.md` has a "Version 15.1" section.
- **Writing guidance (`protocol/module.md`)**: "The entry" now says the whole entry is the design,
  no section is required, and a writer SHOULD follow purpose → core concepts → overview diagrams →
  details; operational walk-throughs stay with the Module that owns the commands. The former Usage
  and Design guidance survives as "How the Module is used" and "Why it is built this way" (content
  requirements, not sections). "Document roles" no longer licenses a topic for "the words several
  Modules share": a Module's own concepts SHOULD be explained in its entry. The `#diagrams` anchor
  is kept (linked from `writing.md` and `views.md`).
- **Diagrams**: the table's process row is a workflow diagram with lanes per participant, covering
  hand-offs between participants; the sequence row reads "Sequence diagram, only then" for when the
  interleaving of messages matters. `views.md`'s illustrative example is now a two-lane workflow
  instead of a sequence diagram.
- **Template** `protocol/templates/module.md` rewritten as Purpose / Core concepts / Overview /
  a detail heading of the writer's choice, stating that the headings are only the recommended order.

### Files outside the task's Modules (changed; please confirm)
The task's Modules are concorde, spec, spec-review, adoption and specification, but three other
Modules' files had to follow the Protocol change. I changed them rather than blocking, because
each is a direct consequence of developer decision 1 and changes no promise of its own:
- **module.workers**: `prompts/workers/common/spec-format.md`, which the brief itself named (entry
  and diagram bullets).
- **module.views**: the docsite loader `docsite/plugins/scoped-content/reading-format.ts` enforced
  the same Purpose/Usage/Design + no-Relationships rule (`requireReading`); left in place it would
  refuse the new root entry and fail `check.views.repository-regressions`. Removed the rule,
  replaced its vitest case in `docsite/tests/scoped-registry.test.ts` by "accepts an entry of any
  section structure", and updated the loader bullet in `specs/concorde/spec-tooling/views/pipeline.md`.
- **module.distribution**: `tests/concorde/distribution/test_distribution.py` injected a
  structural error by renaming `## Design`; it now appends a Mermaid block (`CHK.view.marked`).
  The same substitution was made in the adoption, initialize and spec-review tests (own Modules).

### Left unchanged on purpose
- `src/concorde/spec/initialize.py` (root stub) and `src/concorde/scaffold/command.py`
  (module.scaffold, child stubs and `parent_reading`, which appends child paragraphs under the
  root stub's `## Design`) still write Purpose/Usage/Design headings. They stay valid, and changing
  the root stub alone would make the scaffold append a second, separate Design section; changing
  both belongs with module.scaffold, whose requirement `req.scaffold…` says every entry it creates
  "SHALL say in its Usage and Design sections" that nothing is specified. Follow-up for the
  restructuring tasks (module.scaffold + module.spec).
- Example finding texts such as "Usage names the retry limit before defining it." in spec-review
  contracts/tests are sample worker output, not guidance; left as they are.

### Root Spec (`specs/concorde/module.md`)
- **New structure**: Purpose → Core concepts (Modules and Specs; the people and agents; context and
  boundaries, the five kinds as one list with opening anchors; evidence and errors) → Overview (The
  levels of work, The life of a task, The Modules) → How it is built (Spec first, Two halves one
  seam, Agents at both ends programs between, Modules that serve both halves, Errors as a chain,
  Around the framework) → The children (the nine `contains` anchors, unchanged) → Files of the root.
- **Kept the heading "The levels of work"** so the 14 links from other Modules
  (`../module.md#the-levels-of-work`) still resolve without editing them; its table is trimmed to
  four columns and the "calls go only downward" rules moved to "Agents at both ends".
- **Removed** the "A normal path" walk-through (`concorde task open retry-limit …`), the command →
  Module table and the old Usage/Design headings. Checked that nothing is lost: every command in
  the table is specified by its owner (Spec core `grant`/`spec-validation`, Spec MCP server, Tasks,
  Main session incl. `project-mcp`, Execution/Commands/Workflows), and the walk-through's content
  (open, brief, task session, runs, validation, delivery, merge, escalation, small change, unbound
  runs) is covered by Main session, Tasks and Task sessions. No escalation was needed.
- **Sequence diagram replaced** by an illustrative three-lane workflow "The life of a task" (Main
  agent / Task session / Execution); round trips drawn as two-way edges so labels do not collide.
- **New checked diagram "The Modules"**: Coordination {Main session, Tasks}, Execution {Workers},
  Harness, Tracing, Issues, Spec tooling {Spec core} with only declared `uses` edges; it replaces
  the tiny illustrative Harness diagram. No `direction` (outside the semantic subset). All three
  diagrams rendered with `d2 --layout elk` and inspected.
- **core-concepts.md merged and deleted**: removed from `owns`, registry rewritten, the 14 glossary
  `explanation`s repointed to `specs/concorde/module.md#…`. No other document linked it.

### task-validation r-20260929T174125-task_validation-539de8db: blocked (2 checks)
- `check.spec-mcp.tests` (module.spec-mcp): `test_validate_returns_the_command_envelope` injected
  a structural error by renaming `## Usage`; now appends a Mermaid block, as the other tests do.
- `check.views.repository-regressions` (module.views): `production-build.test.ts` asserted that
  every entry page renders Purpose, Usage and Design in that order; the assertion is removed with
  the rule (the root no longer has Usage or Design). Both files belong to Modules outside the task,
  changed for the same reason as the loader (consequence of decision 1).

### Delivered
task-validation r-20260929T174737-task_validation-00d38149: ok (ready). delivery
r-20260929T175321-delivery-994cb0fe: ok, delivery commit 16673298 on concorde/entry-structure.
The scaffold follow-up named above concerns `req.scaffold.stub-unspecified` ("SHALL say in its
Usage and Design sections").

## Closed: merged, 2026-09-29T17:59:43Z

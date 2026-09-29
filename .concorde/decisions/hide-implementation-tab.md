# Decision log: hide-implementation-tab

Goal: Stop showing implementation documents as a docsite tab: keep publishing their pages with every identity addressable, reachable from links and from a folded list on their Module's page, but out of the site navigation

## Brief (main agent, 2026-09-30)

### Why
The developer noticed they almost never read implementation documents (a Module's
`requirements.md`, `scenarios.md`, `contracts.md`) and asked whether the docsite should stop
showing them. The main agent advised against removing the pages: review findings, validation
errors and failing checks name `req.…` / `scenario.…` identities that readers must be able to open;
Module documents link to them (e.g. Views' own "[contracts](contracts.md)"), and the docsite build
checks links; and the Protocol's publication obligation (`protocol/views.md`, "Publication
obligations") requires every stable identity to be addressable. The developer approved this plan:

### Developer's decision
- Remove the **Implementation documents** tab from the docsite navigation; the tabs become user
  documents, Module documents and the custom docs (Spec Protocol).
- Keep **publishing** every implementation document's page with all identities anchored, reachable
  from links in Module documents, from term/identity links and by URL, but not in any sidebar.
- On each Module's page, list its implementation documents in a **folded** block at the bottom (the
  existing `docsite/src/components/ContentProvenance.tsx` already has a folded "Implementation
  documents (n)" block — reuse or adapt it, your call).
- **No Protocol change**: the Protocol prescribes no pages, sidebars or tabs. Change the Views
  Module's Spec (its entry currently promises two reading collections, the second being
  Implementation documents; also its requirements/scenarios/contracts as affected) and the docsite
  code and tests accordingly.

### Left to the session
Routes (keep existing URLs of implementation pages stable if practical, so no link breaks), how the
hidden pages show where they belong (e.g. a breadcrumb or a "Precise promises of <Module>" header
linking back), the site manifest, test changes. Build the docsite (`npm --prefix docsite run build`)
and look at the result before delivering.

### Coordination note
Task `entry-structure` is running in parallel on the Protocol and root Spec (Modules concorde, spec,
spec-review, adoption, specification). It may rewrite `protocol/*.md` and `specs/concorde/module.md`
but not Views. Do not edit files outside Views' realization; escalate if you need to.

## Non-ok result during preparation (main agent, 2026-09-30)

`python3 scripts/development/init-references.py` in this worktree failed at
`git submodule init -- references/pi` (exit 128): `error: could not lock config file
/home/zhenyu/concorde/.git/config: File exists`. The lock was an empty, read-only
`.git/config.lock` (created 01:41:25) left by Claude Code's Bash sandbox of the `entry-structure`
task session, which ro-binds `/dev/null` onto `.git/config.lock` to keep `.git/config` read-only and
thereby creates the file on the host; it is not a Git lock and stays after the command. The main
agent chained the session start after the failing script, so this session started before its
references were initialized. The main agent then removed the empty placeholder (checked 0 bytes
first) and re-ran the script, which initialized every reference. Consequence for this task: none;
the references are now present. Follow-up: a Concorde defect (any running or past task session
blocks shared Git config writes for the next task's preparation) to record as an Issue in a later
task.

## Correction of the entry above (main agent, 2026-09-30)

Reading Claude Code's sandbox runtime (`references/sandbox-runtime/src/sandbox/linux-sandbox-utils.ts`,
`cleanupBwrapMountPoints`) shows the placeholder is **not** left behind: the runtime removes each
`--ro-bind /dev/null` mount point after the sandboxed command, deferring only while another sandbox
of the same process runs. The `.git/config.lock` existed because the `entry-structure` session was
running a long sandboxed command (`build --check` then `task-validation`) at that moment. Removing
it while that bwrap ran detached its bind, so for the rest of that one command `.git/config` was
not write-protected inside that session's sandbox; nothing indicates it was written.
The defect is Concorde's: `scripts/development/init-references.py` runs `git submodule init` for
every task although the submodule URLs live in the repository-wide `.git/config` that every
worktree shares and are already registered; `git submodule init` takes the config lock even when
nothing changes, so preparing a task fails whenever any task session is running a sandboxed
command. Fix direction: skip `git submodule init` when `submodule.<name>.url` is already set (a
read takes no lock), and never delete a lock the main agent did not create. `init-references.py`
is bound to `module.concorde`, which `entry-structure` holds, so the fix runs after it.

## Task session decisions (2026-09-30)

- **Routes unchanged.** Implementation pages keep their canonical routes (`/specs/<path>`); only the
  `implementationDocumentsSidebar` and the "Implementation documents" navbar tab are gone. No link
  breaks, and the site manifest (schema 23, `readingCollection` per page) is unchanged.
- **Hidden pages show the Module documents sidebar.** Their front matter sets
  `displayed_sidebar: moduleDocumentsSidebar`, so a reader keeps the Module tree for orientation,
  but no sidebar item lists them. Search still indexes them, since identities from review findings
  and errors are what readers look up.
- **Where a hidden page belongs.** The provenance bar of an implementation page shows "Of the Module
  <title>" (a `nav` labelled "Owning Module") linking to the owner's entry, replacing the earlier
  "Module documents: <title>" link.
- **Folded list at the bottom of the entry only.** The "Implementation documents (n)" `<details>`
  moved out of the provenance bar into a new `ImplementationDocuments` component rendered by a
  `DocItem/Footer` wrapper after the reading, on the Module's entry page only (topics no longer
  carry it). A shared `useScopedPage` hook finds the current page for both wrappers.
- **Spec changes (Views only).** Entry Usage rewritten; `req.views.reading-collections` keeps
  role → collection; new `req.views.implementation-documents-unlisted`;
  `scenario.views.reading-collections` and `…-single` rewritten (the latter now "The navigation does
  not depend on implementation documents"); `scenario.views.user-docs` tab order; pipeline Staging,
  Navigation, Provenance and Build hooks sections; "Spec tabs" wording became "Module documents
  tab" (also in `req.views.custom-docs-order`, contracts and the user-docs admission message, now
  "the Spec pages").
- **Non-ok result:** the first `npm --prefix docsite run build` failed with "Materialized Spec
  source identity differs; prepare publication again" because I edited the Views Spec while it ran;
  rebuilt after the Spec edits.
- **Non-ok result:** one `spec-validation` run was `invalid` (CONCORDE-CHECK-001, `specs/.mcp.json`
  not a regular file): the Bash sandbox had left `.claude/` placeholder directories in
  `specs/concorde/spec-tooling/views/` and `docsite/` after I `cd`'d there. Removed them; the next
  run succeeded. Not a Concorde defect.

## Escalated to the main agent, 2026-09-29T17:58:29Z

- **task-session** task session (task hide-implementation-tab): `user_guide_names_removed_tab`
  docs/using-concorde.md line 761, in the list 'The site's tabs come in a fixed order', says: '2. **Module documents** and **Implementation documents**, generated from your Specs.' After this task there is no Implementation documents tab, so the user guide is wrong once merged. The fix is one line, e.g. '2. **Module documents**, generated from your Specs; each Module's entry ends with a folded list of its implementation documents, which no tab lists.' The table of document kinds at line 45 stays correct. Everything else in the task is done, committed (6f259a9a) and under task-validation.
  Not handled here (decision): docs/ is the realization realization.concorde.user-documents of module.concorde, outside this task's Module module.views, and the brief says not to edit files outside Views' realization but to escalate; task entry-structure is also working on module.concorde in parallel.
  Options: Let this task change that one line of docs/using-concorde.md, then deliver; Deliver without it; the main agent makes the one-line change on main after merging, as an approved small change; Leave it to a later task
  Recommendation: Let this task change the line: it is a direct consequence of this task's goal, one line, and entry-structure touches protocol/ and specs/concorde/module.md, not docs/.

```json
{
  "level": "task-session",
  "actor": "task session (task hide-implementation-tab)",
  "code": "user_guide_names_removed_tab",
  "detail": "docs/using-concorde.md line 761, in the list 'The site's tabs come in a fixed order', says: '2. **Module documents** and **Implementation documents**, generated from your Specs.' After this task there is no Implementation documents tab, so the user guide is wrong once merged. The fix is one line, e.g. '2. **Module documents**, generated from your Specs; each Module's entry ends with a folded list of its implementation documents, which no tab lists.' The table of document kinds at line 45 stays correct. Everything else in the task is done, committed (6f259a9a) and under task-validation.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "docs/ is the realization realization.concorde.user-documents of module.concorde, outside this task's Module module.views, and the brief says not to edit files outside Views' realization but to escalate; task entry-structure is also working on module.concorde in parallel."
  },
  "options": [
    "Let this task change that one line of docs/using-concorde.md, then deliver",
    "Deliver without it; the main agent makes the one-line change on main after merging, as an approved small change",
    "Leave it to a later task"
  ],
  "recommendation": "Let this task change the line: it is a direct consequence of this task's goal, one line, and entry-structure touches protocol/ and specs/concorde/module.md, not docs/.",
  "causes": []
}
```

## Main agent's answer to escalation #1 (2026-09-30)

Decided without the developer (ordinary scope): this task changes the one line of
`docs/using-concorde.md` that names the removed tab. `entry-structure` has since merged into main
(`090c764b`) and touched Views files (docsite loader rule `requireReading`, its vitest case,
`pipeline.md`, the production-build order assertion) and `docs/using-concorde.md`, so the session
first merges main into the task branch, resolves any conflict keeping both changes, then edits the
line, reruns task-validation and delivery.

## After the answer to escalation #1 (task session, 2026-09-30)

- Merged main (2b664e76, with entry-structure) into the task branch as the main agent asked; Git
  merged without conflicts (2a2fddf2). Both sides survive: entry-structure's removal of the
  Purpose/Usage/Design loader rule and order assertion, and this task's navigation changes.
- Because entries no longer need a Design section, the production-build check that the folded list
  closes the entry now compares it with the entry's last level-2 heading and the end of the
  article instead of `id="design"`.
- Changed `docs/using-concorde.md`'s tab list, item 2, to "Module documents, generated from your
  Specs. No tab lists implementation documents: each Module's entry ends with a folded list of its
  own.", as decided.

## Closed: merged, 2026-09-29T18:11:43Z

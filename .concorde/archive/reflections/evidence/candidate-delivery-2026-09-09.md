# Candidate delivery log: two host-created change worktrees (2026-09-09)

Requested by the developer: complete the two remaining candidate changes and merge them into `main`,
resolving conflicts autonomously and recording every choice made where the sources were
inconsistent or a Spec left room for interpretation.

| Change | Worktree | Branch | Task |
| --- | --- | --- | --- |
| `change.2424f47e-0a88-4577-aca3-3dbff45b8a1b` | `/tmp/concorde-worktree-kvzq7yak/project` | `concorde/2424f47e-…` | Framework overview diagram: show that Spec-context resolution of Project Specs depends on the Concorde Spec Protocol |
| `change.a7e23b87-1232-42e9-ba05-b1097645d139` | `/tmp/concorde-worktree-23ryoxpl/project` | `concorde/a7e23b87-…` | Docsite navigation mirroring registered Spec source paths, readable canonical routes, legacy-route compatibility, shared documents shown once |

## Observations that differed from the request's premise

1. **Neither candidate contained any work product.** Both worktrees held only the host-written
   `AGENTS.md`/`CLAUDE.md` guidance blocks. Change `2424f47e` was recorded as `specify / blocked`
   with outcome `child_blocked` and no gap history, no authored Specs, no reviews; change `a7e23b87`
   was `created / active` with no bound target. The statement that the blocked change was "basically
   done" is not reflected in the files. Both changes were therefore implemented from scratch in their
   worktrees.
2. **Both candidates were behind `main`** (`2fc1992` and `a861f1f` versus `d40f8b8`). Merging `main`
   into each was a fast-forward with no content conflicts. The only conflict was the host guidance
   block appended to `AGENTS.md` (uncommitted, stashed for the merge): `main` had rewritten
   `AGENTS.md` (`72cc22e`). Resolution: take `main`'s `AGENTS.md` and re-append the unchanged
   guidance block; `CLAUDE.md` applied cleanly.
3. **Change `2424f47e` carried the constraint "Retain the worktree; do not deliver or merge. Delivery
   requires a separate request."** The developer's request in this session is that separate request;
   the constraint is treated as superseded.
4. **Concorde lifecycle reviews were not run.** Change `2424f47e` had recorded a required Spec review
   for `domain.concorde` (`review_requirements`). Running it requires the model-driven dev-loop.
   Per the developer's instruction to complete and merge directly, both changes are verified with the
   deterministic checks (`validate`, docsite tests and production build, Python suite, Archify
   showcase validation) and merged with plain Git rather than `concorde-deliver`; no Spec or code
   review evidence exists for them in `.concorde/worktree.json`.

## Design choices made without an explicit Spec answer

### Framework overview diagram (`2424f47e`)
- Relationship direction and wording: `spec-protocol → contexts`, label `Defines resolution rules`.
  The Protocol is the source of the rules; Spec contexts are the consumer. The existing
  `project-specs → contexts: Resolves Specs` edge is retained.
- Adjacent prose: one sentence in `specs/concorde/ontology.md` "Architecture overview" now says the
  context Service resolves registered Specs "under the Protocol's organization and resolution rules".

### Docsite navigation (`a7e23b87`)
- **Common root stripping.** Canonical routes drop the leading `specs/` segment only when every
  registered document lives under `specs/` (true for Concorde). The task's example
  (`concorde/workflow/delivery.md`) implies this; a project with documents outside `specs/` keeps
  full paths so nothing is ambiguous.
- **Sidebar labels are file names** (`delivery.md`), not page titles, to make entries "recognizable"
  by path as requested; the page title remains the Markdown H1.
- **No category links in the source tree.** A directory category does not link to the Domain main
  Spec inside it, because Docusaurus would then hide that document from the listing and it must stay
  directly findable by file name. Domain main-Spec selection is preserved through the secondary
  by-target navigation, the root redirect and the embedded overview.
- **Secondary by-target navigation uses link items.** Docusaurus does not allow one document id in
  two sidebar positions, so the "Specs by target" group (Domain scopes and components, as before)
  uses `link` entries to the canonical routes; a Domain's first entry links to its main Spec.
- **Legacy routes become redirect stubs written by the plugin's post-build hook**
  (`/specs/<target-id>/<hash16>.html` with a meta refresh and canonical link). No
  `@docusaurus/plugin-client-redirects` is installed and no network is available, so the site writes
  the stubs itself; `validateScopedBuild` verifies each stub exists and names its canonical route.
- **Build manifest and global data schema version 14 → 15.** The page shape changed (one page per
  document with `targets` and `aliases`), so the version is bumped rather than silently reusing 14.
  The publication Specs are updated accordingly.
- **Link rewriting simplification.** With one canonical page per document, the former "prefer the
  same target, reject ambiguous shared destinations" rule has no cases left; a relative link resolves
  to the single registered page or fails as unregistered.
- **Shared documents** are published once (canonical page listing every membership) and still appear
  under every referencing target in the by-target navigation; the relationship graph is unchanged.

### Further choices made during the docsite implementation
- A page without a Markdown H1 takes its title from the primary membership's target, else the first
  membership's target (the old rule assumed one target per page).
- The by-target navigation lists each target's documents in that target's own registered order,
  so a shared document that is published earlier globally still appears where its target declared it.
- `docsite/src/pages/graph.tsx` selected the Profile 8 graph by `schema_version === 14`; it now
  checks 15, otherwise the site would silently fall back to the legacy feature-graph page.
- The "two documents map to the same canonical route" guard is kept although stripping a fixed
  prefix and suffix from unique paths cannot collide; the alias-collision and `projections/` guards
  are the reachable ones and are tested.

## Incidents during delivery
- `scripts/development/check-docsite-types.py` (the configured `check.publication-types`) ran
  `npm ci` in the docsite worktree because the dependency identity marker was missing there. The
  worktree's `docsite/node_modules` was a symlink to the primary checkout's directory, and `npm ci`
  emptied the primary checkout's `docsite/node_modules` through that link before installing a real
  copy in the worktree. The primary checkout's directory was restored by copying the fresh install
  back (816 packages, identity marker included); nothing tracked by Git was affected. Lesson: never
  symlink `node_modules` into a worktree where that check may run.
- `docusaurus serve` (local preview only) answers `/concorde/diagrams/<hash>.html` with a 301 to
  `/diagrams/<hash>` (dropping the base URL) and finally serves the site home, so the embedded
  overview iframe shows the site itself in a local preview screenshot. The iframe source and the
  static diagram copy are unchanged by this delivery; the built output contains
  `build/diagrams/<hash>.html`, which a static host such as GitHub Pages serves directly. Recorded as
  a pre-existing preview limitation, not fixed here.

## Spec sentences replaced

See the two per-change sections: for `2424f47e` one sentence in `specs/concorde/ontology.md`; for
`a7e23b87` the route/navigation/manifest paragraphs of `specs/concorde/services/publication-boundary.md`,
the Page/route/sidebar/rewriteLinks/postBuild/manifest paragraphs of
`specs/concorde/modules/spec-publication.md`, and the Page/Route/shared-truth sentences of
`specs/concorde/publication/ontology.md`. Every MUST sentence, `concorde-document` block, Ontology
table and `concorde-participants` block is unchanged.

## Verification and delivery record

### `2424f47e` (diagram) — delivered
- Commit `61801f0` on `concorde/2424f47e-…`, fast-forwarded into `main`.
- Diagram edit: connection `spec-protocol → contexts`, label `Defines resolution rules`, with
  `toSide: top` and a `via` waypoint `[[850,100],[850,300]]` (two Archify geometry repairs: the
  automatic route crossed the "Initializes registry" label, then the entry segment was diagonal).
  Archify showcase receipt 9/9 checks, 0 errors, 0 warnings; all five declared diagrams re-rendered.
- Prose edit: `specs/concorde/ontology.md` Architecture overview sentence, as described above.
- Checks: `validate` clean in the worktree and in `main` after the merge; docsite vitest 28 files /
  135 tests (including the production build); rendered overview inspected from a Playwright
  screenshot (`scratchpad/framework-overview.png`).
- The host guidance blocks in `AGENTS.md`/`CLAUDE.md` were unstaged before committing so no local
  control content entered the delivered tree.

### `a7e23b87` (docsite navigation) — delivered
- Commit `bb7ba5f` on `concorde/a7e23b87-…`, then `main` (with the diagram change) merged into the
  branch as `103bc6d`, and `main` fast-forwarded to it.
- 15 files: `docsite/plugins/scoped-content/{model,materialize,index}.ts`,
  `docsite/src/{components/ContentProvenance,components/ScopedGraph,pages/graph,pages/index}.tsx`,
  `docsite/README.md`, four docsite tests, and the three publication Specs.
- Checks on the merged tree: `validate` clean; docsite vitest 28 files / 142 tests (135 → 142,
  including the production build and the new alias-stub and route tests); `tsc --noEmit` clean;
  `check-docsite-types.py` exit 0; Python suite 682 tests / 8 skipped in the worktree. Re-run in
  `main` after the fast-forward (see the final report).
- Verified over HTTP on the built site: canonical `/specs/concorde/workflow/delivery` → 200; legacy
  `/specs/domain.workflow/13dfa626f9aa7ece` → redirect stub naming the canonical route; sidebar
  screenshots `scratchpad/docsite-nav-delivery.png` and `docsite-nav-ontology.png`.
- Worktree removed after delivery with `git worktree remove --force`; the branch is kept, matching
  the host's own delivery cleanup, and `.concorde/worktrees.json` was refreshed.

### Final state of `main` (`103bc6d`)
- `python3 scripts/concorde.py build --check`: no differences; `validate`: success, no findings;
  `git diff --check`: clean.
- Python suite: 682 tests, OK, 8 skipped. Docsite: vitest 28 files / 142 tests, `tsc --noEmit`
  clean, `check-docsite-types.py` exit 0.
- `git worktree list` shows only the primary worktree; both `concorde/<change-id>` branches remain
  as fully merged references.

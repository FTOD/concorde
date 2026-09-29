# Decision log: glossary-grouped-page

Goal: Render the glossary page grouped: core terms of the root Module first, then one section per top-level area of the Module tree, with an A-Z index of every term for lookup by name

## Decisions taken without the developer

- **Group granularity.** Options: one group per owning Module (about 30 small groups), or one
  group per Module the root contains, holding every concept owned in its subtree (9 groups).
  Chose the latter, as the goal states and the developer agreed; the index and each entry's
  "Owned by" line still name the exact owner.
- **Heading levels and table of contents.** Groups are level-2 headings anchored
  `terms.<module id>`, concepts level-3 headings keeping their identity anchors; the page's
  `toc_max_heading_level` drops from 3 to 2 so the table of contents lists the 9 groups instead
  of 156 terms. Concept anchors are unchanged, so every term link still resolves.
- **Sort order.** Titles now sort with letter case ignored (then exactly), so a lowercase title
  such as `configure-workers` or `pi runtime` sorts under its letter instead of after `Z`.
- **Owner outside the root's tree.** Such a concept gets the group of its own topmost Module,
  appended after the root's contained Modules. Concorde has none; the rule keeps the page total.

## Results

- `spec-validation` first failed with `CHK.external.exists` for
  `references/pi-packages/packages/pi-permission-system/` because the reference submodules were
  not initialised in the new worktree; ran `scripts/development/init-references.py`, then it
  passed.

## Closed: merged, 2026-09-28T18:59:19Z

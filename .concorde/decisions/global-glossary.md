# Decision log: global-glossary

Goal: Replace per-Module Terminology tables and import rows with one project glossary (JSON, rendered under the root) whose entries carry an owner enforced by audit, whose linked entries are selected into worker context, with a first-use link rule

## Decisions taken by the developer (2026-09-28, recorded for reference)

- All terms become global: one project glossary in JSON, rendered as a page under the root.
- Ownership stays per entry (`owner`), enforced after the fact by the worker write audit (option a).
- Term links are the only selection rule; a warning check reports unlinked uses (first use).
- A worker receives one-sentence definitions; an explanation still needs `uses`/`contains`.
- This is a major Protocol change: `imports`, the Terminology tables and their checks go away, and
  concept identities become global slugs.

## Design decisions taken without the developer

1. **Location.** The glossary is declared by the root Module's entry: an optional `glossary` field
   (project-relative path) in the `module` block, allowed only on a Module without a parent and
   declared by at most one Module; it is mirrored in the registry like every other field. Options:
   a fixed path beside the root entry (implicit, ambiguous with several roots), a registry-only field
   (the registry is a mirror, not a declaration site), or a root declaration (explicit, checked).
   Chose the declaration because A2 wants every fact declared once at a fixed site.
2. **Entry shape.** `{id, title, owner, definition, explanation}` plus optional `retired`,
   `external_conflict`, `narrows`, `supersedes`, `contrasts`, `relates`. Relations whose source is a
   concept move into its entry, because the entry is now the concept's defining site (A2). Relations
   whose source is a realization or Module stay in document metadata.
3. **Explanation stays required** (`explanation`: `<reading path>#<anchor>` in a document the owner
   owns), as `meaning` was, so A1 still holds and `relies_on` of a concept still selects the
   document that explains it (the developer's point 3: explanation through `uses`).
4. **Identities** become `concept.<slug>`; titles are unique project-wide (normalized). The one
   existing duplicate title (`Build manifest` in views and distribution) is renamed.
5. **Selection.** Terms(M) = the concepts M owns, the concepts linked from the reading of every
   document in Spec(M), and the concepts named by declarations in those documents (relies_on,
   relates targets), closed over the concepts an entry's definition links and its relations target.
   This closure is an explicit, bounded exception to A7's one-level rule: it adds sentences, never
   documents.
6. **Delivery.** The context record gains a `terms` array (id, title, owner, definition and the
   selecting declarations); the grant carries the union for its bound Modules and the context
   identity covers it; the worker brief lists the terms. The glossary file itself is readable and
   writable only to task types whose SpecScope level is write (specify, code-to-spec), because a
   Spec-writing worker must edit it.
7. **Unlinked-use check** (warning): a single-word title is recognised only as written (for example
   `Worker`), a multi-word title in any letter case, with an optional plural `s`, outside code,
   headings, links and anchors; one warning per document and concept that the document never links.
   Matching single words case-insensitively would flag ordinary words such as run, build, case and
   task in almost every document.
8. **Main-agent edits** of the glossary are not audited per entry (only worker writes are), as the
   main agent is not bound by a grant.

## Decisions taken during implementation (without the developer)

9. **Unlinked-use matching refined.** A first run flagged 1,276 uses, many of them Module names
   (`Tasks`, `Issues`, `Workflows`) and sentence-initial verbs (`Run`, `Build`). The check now masks
   Module titles, lets the longest overlapping title win (`Task` inside `Task type` is no use),
   ignores a one-word title as the first word of a sentence, list item or table cell, and matches
   one-word titles without a plural. Stated in `CHK.term.unlinked` and its limits row.
10. **Migration of this project's Specs was mechanical, then reviewed.** A one-off script moved the
    153 concepts into `specs/concorde/glossary.json` (ids `concept.<slug of title>`, anchors renamed
    to the new ids), removed every Terminology section and the 31 vocabulary includes, rewrote
    concept links to term links, then linked the first unlinked use of each term per document
    (1,125 links) and rewrapped the prose those links pushed past 100 columns. The duplicate title
    `Build manifest` became `Site build manifest` for Views; the Views prose the auto-linker had
    pointed at Distribution's term was corrected by hand. Options: link by hand (days of work) or
    leave 1,276 warnings; chose mechanical linking plus review of the known meaning conflict.
11. **`relies_on` and term links.** `CHK.relies-on.linked` no longer counts a term link as a
    relied-upon promise, otherwise every word linked in a `uses` explanation would force the
    provider's explaining document into context. Protocol check statement amended.
12. **Grant record** gains `terms` (whole glossary entries) and `glossary` (its path, so the audit
    knows which file to hold by entry); the Spec MCP `boundary` tool keeps its contract
    (`context_identity`, `entries`) and `context` returns `terms`. Context record schema 3 → 4.
13. **Initialization** creates an empty glossary beside the root entry and declares it, so the first
    `specify` task can add concepts without writing the root's block.
14. **The glossary is exempt from `CHK.binds.unbound` and never bindable**, like a document member.
15. **Docsite port delegated** to a subagent (Sonnet), limited to `docsite/`; its work was re-run
    here (tsc, 257 vitest tests, production build). Its decisions: glossary route
    `/specs/<dir>/glossary` as the last item of the root Module's sidebar category; glossary
    relations are shape-checked but not rendered. It also fixed a latent per-line link rewriting
    bug. Non-ok result: its production-build test expected hrefs without the site's base URL;
    fixed here.
16. **Non-ok result: two links corrupted by the first auto-link pass** (a term link inserted inside
    a link whose text wrapped across lines: `harness/pi.md`, `execution/workers/module.md`). Found
    by the docsite build. Repaired by hand, and the root cause fixed: Spec core's link and
    unlinked-use scanners now match links over the whole prose instead of line by line.
17. **Main session terms (developer's follow-up request).** The developer chose injection at
    session start. Claude Code caps a SessionStart hook's output at 10,000 characters and this
    glossary renders to ~29,000, so the mechanism was adjusted: the installed `CLAUDE.md` block
    imports the glossary with `@<path>` (loaded at launch, uncapped, always current;
    `init --apply` adds it for the first glossary), and the pi extension appends the rendered terms
    to every prompt's system prompt, in main and task sessions. Guidance (skill "Project terms",
    CLAUDE.md block, task-session guidance) and this checkout's CLAUDE.md, AGENTS.md and
    DEVELOPING.md require using each term exactly as defined. The pi extension handler itself is
    exercised only through its pure helper (`glossaryText`), as the rest of the extension is.
18. **Non-ok result: first task-validation blocked** — `specs/concorde/glossary.json` reported
    `unbound`, since readiness had its own accounted-path rule. Fixed: the glossary is accounted
    for like a Spec document member (readiness contract version 2 → 3; no participant declares a
    version). A glossary change still selects every Module's checks, because every Module's Spec
    scope holds the glossary file; kept deliberately (conservative, and a term change can break the
    docsite build). Second task-validation: ready, 23 checks passed.

## Closed: merged, 2026-09-28T04:51:34Z

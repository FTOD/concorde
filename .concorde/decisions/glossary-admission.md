# Decision log: glossary-admission

Goal: Admit to the glossary only terms that are not common sense and are used beyond their owner Module: state the admission criterion in the Protocol with a CHK.concept.local warning, carry it into DEVELOPING.md and the Spec-writing prompts, and remove the 55 entries the developer approved, with their term links and references

## Decisions taken without the developer

- **List adjusted to main.** The developer approved 57 deletions; `configure-workers` and
  `Model picker` had already left the glossary on main (worker-configuration change), so 55 were
  removed and 100 entries remain. External context, added on main meanwhile, is a root-owned core
  term and stays.
- **Protocol version.** The criterion and `CHK.concept.local` were added without a version bump,
  as earlier wording changes to the Protocol were; the manifest was regenerated and rebound.
- **Scope of `CHK.concept.local`.** A use is a term link in a document another Module owns,
  another Module's `relies_on` or metadata `relates`, or a link or relation of a concept another
  Module owns. Unlinked mentions do not count (`CHK.term.unlinked` covers them). Concepts of the
  Module declaring the glossary are exempt. Before the deletions it reported exactly 30 entries,
  all on the approved list.
- **What the "common sense" half enforces.** No check decides it; the Protocol text, DEVELOPING.md,
  the main-session skill, the spec-format and code_to_spec prompts and the spec-review checklist
  (`terminology` dimension) state it.
- **Removed references.** Term links to removed entries became plain text (bold kept); their
  `<a id="concept.…">` anchors were removed, explanation prose kept; `relies_on` entries and
  metadata `relates` naming them were removed, as were relations of kept entries targeting them
  (Decomposition proposal and Workflow mode → Decision, Task record → Task state, Main-session
  guidance → Escalation policy, Read-only check boundary → Check scratch).
- **Checked diagrams.** Shapes of removed concepts and their edges were dropped from the checked
  diagrams of Tasks, Check execution, Commands, Scaffold, Spec MCP, Spec core and Main session.
  Adoption's diagram, drawn almost entirely from removed terms (Survey, Code to spec, Spec
  description, Decision, Answers), was marked `illustrative` rather than emptied. Commands' table
  realization now `lists` Execution command directly (new metadata `relates`) instead of realizing
  the removed Command catalog.
- **Shorter titles surfacing.** Removing a longer title exposed shorter terms inside it to
  `CHK.term.unlinked`: Views' own "site build manifest" is renamed "site manifest" throughout its
  documents, keeping it apart from Distribution's Build manifest; Code review's "code review
  finding" became "finding of the report"; Spec review's requirement links Spec.
- **Line wrapping.** Paragraphs whose links became plain text keep their shorter lines; they were
  not reflowed, to keep the diff reviewable. Rendering is unaffected.

## Results

- The first test run after the Protocol edits failed (16 tests) with `build source changed since
  the last build: protocol/checks.md`; `build` and `protocol-manifest --write --bind-project`
  fixed it.
- The first spec-validation after pruning was `invalid`: 6 `CHK.registry.mirror` (fixed with
  `registry --write`), 14 `CHK.view.nodes` (diagrams, above) and 6 `CHK.term.unlinked` (above);
  it then passed with no findings.

## Closed: merged, 2026-09-28T19:22:44Z

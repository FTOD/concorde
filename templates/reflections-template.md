# Reflections: [PROJECT NAME]

**Canonical path**: `.concorde/reflections/log.md`

<!-- concorde-reflection-high-water: R-000 -->

The project's one reflection log: every difficulty or problem a coding agent met while planning or
implementing any feature, attributed to the feature that was being worked on and naming the source
the problem concerns (any feature, module architecture, interface, guidance, tool, or file).
Ordinary recording appends entries and occurrences. Explicit rename/documentation reconciliation may
rewrite entry text and references like other maintained docs/specs while preserving every stable,
unique `R-NNN` identifier, required structure, maintainer decision, and problem meaning. New entries
first reserve their identity through the installed helper's atomic `--allocate-id` operation and use
only its `allocated_id`; the high-water marker retires allocated and removed IDs permanently.
Maintainers may explicitly archive or remove closed entries without renumbering or reusing IDs.
Reflection-triage/v3 also
removes an open entry automatically after its `small` `fast-loop` plan is validated, merged, marked
`merged`, and accepted by the helper's `--remove-merged` gate. Every other route/effort/status keeps
the entry for maintainer disposition. This file is the sole persisted
authority for entry identity, status, notes, occurrences, and prose; no attempt artifact,
feature file, module architecture, interface, diagram, code, or test copies or cites that content.
Delivery presents entries transiently and rejects copied `R-NNN` identifiers; no operation removes
this tracked control-state file.

<!--
  Grammar (Concorde Reflection Log v1). One H3 per entry, sequential identifiers, never reused:

  ### R-NNN · <short title>
  - **Phase**: plan | tasks | implement | analyze | converge      (phase that first recorded it)
  - **Date**: YYYY-MM-DD
  - **Feature**: <stable ID of the selected feature>
  - **Kind**: specification | architecture | guidance | tooling | environment | implementation
  - **Concerns**: <stable ID or project-relative path, optional #fragment or :line>
  - **Expected**: <what the concerned source says should hold>
  - **Observed**: <what actually happened>
  - **Effect**: assumed | worked-around | deferred | blocked
  - **Action**: <what the agent did: assumption, workaround, deferral, or stop reason>
  - **Improvement**: <the change to the concerned authority that would remove the problem>
  - **Intervention**: <why automation cannot close this entry, and the maintainer decision or action required; write "当前不需要你的介入" when none is needed>
  - **Status**: open | resolved | dismissed                         (maintainer-owned once set)
  - **Note**: <required when Status is not open: why, and the resolving change>
  - **Occurrences**:                                                 (optional; on re-encounter, never a new entry)
    - <phase> <date> <feature-id> — <context>

  Rules: record in the phase the problem is met; do not silently repair a protected or out-of-scope
  feature file, module architecture, interface, diagram, or another feature's code — record the
  problem and route an explicit owning task instead;
  never copy an entry identifier, status, note, occurrence, or prose into another persisted artifact;
  update an existing entry rather than duplicate it; never derive a new ID from remaining entries;
  never let an agent manually delete an entry, renumber IDs, or reverse a maintainer's Status or
  Note; only explicit maintainer direction or the deterministic v3 helper may remove an entry, and
  the helper removes only an eligible merged-small entry without adding Status/Note; cite evidence paths
  instead of pasting secrets or bulk output; keep
  Expected/Observed/Action under about 150 words together. Old resolved or dismissed entries may be
  moved under a "## Archive" heading in this file.
-->

# Reflections: [PROJECT NAME]

The project's one reflection log: every difficulty or problem a coding agent met while planning or
implementing any feature, attributed to the feature that was being worked on and naming the source
the problem concerns (any feature, module, contract, guidance, tool, or file in the project).
Agents append entries and occurrences; maintainers resolve or dismiss them in place; acceptance cites
a feature's open entries in its design reference; no operation removes this file.

<!--
  Grammar (Concorde Reflection Log v1). One H3 per entry, sequential identifiers, never reused:

  ### R-NNN · <short title>
  - **Phase**: plan | tasks | implement | analyze | converge      (phase that first recorded it)
  - **Date**: YYYY-MM-DD
  - **Feature**: <stable ID of the feature or sub-feature selected when recorded>
  - **Kind**: specification | architecture | guidance | tooling | environment | implementation
  - **Concerns**: <stable ID or project-relative path, optional #fragment or :line>
  - **Expected**: <what the concerned source says should hold>
  - **Observed**: <what actually happened>
  - **Effect**: assumed | worked-around | deferred | blocked
  - **Action**: <what the agent did: assumption, workaround, deferral, or stop reason>
  - **Improvement**: <the change to the concerned authority that would remove the problem>
  - **Status**: open | resolved | dismissed                         (maintainer-owned once set)
  - **Note**: <required when Status is not open: why, and the resolving change>
  - **Occurrences**:                                                 (optional; on re-encounter, never a new entry)
    - <phase> <date> <feature-id> — <context>

  Rules: record in the phase the problem is met; never edit abstract.md, feature design.md,
  implementation.md, any module design.md, module.md, a contract, a view, a diagram, or another
  feature's code in response — record instead;
  update an existing entry rather than duplicate it; never delete, renumber, or reverse a
  maintainer's Status or Note; cite evidence paths instead of pasting secrets or bulk output; keep
  Expected/Observed/Action under about 150 words together. Old resolved or dismissed entries may be
  moved under a "## Archive" heading in this file.
-->

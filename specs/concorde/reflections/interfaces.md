```concorde-document
{
  "id": "document.reflections.interfaces",
  "owner": "module.reflections",
  "main_visible": true
}
```

# Reflection triage boundary

A Reflection records a problem and human comments independently of implementation. Its stable
R-NNN identity is allocated monotonically by `.concorde/reflections/index.json`
(`{schema_version: 1, high_water}`). The canonical record is `.concorde/reflections/<bucket>/R-NNN.md`,
with frontmatter `id, title, phase, date, feature, kind, concerns, status` and optional
`resolution_note`. The historical field `feature` accepts a registered Module or one of its local
scenario ids. Required sections are Context, Expected, Observed, Impact, Evidence, Triage Analysis,
Proposed Resolution, Intervention Rationale, User Comments and Occurrences. Original problem and
human comments are preserved by triage.

Status is `open|resolved|dismissed`. The bucket directory is the only record of triage state:
`pending` holds an untriaged problem, and `planned` or `needs-comments` hold a completed one,
according to whether a developer must comment. Investigation fills the triage sections and moves
the record into its bucket in one deterministic action.

Public `concorde-reflections-triage` takes the common `invocation@3` envelope and a `request@1`
containing `target_id`, `action status|record-gaps|investigate|implement|merge|close`,
`reflection_ids` (unique string array), and optional `task, focus_id, constraints, change_id`.

## Status and attribution

### scenario.reflections.status-query — Read-only status query returns typed metadata only

- GIVEN a registered record id attributed to a Module or scenario
- WHEN a caller requests status for that id
- THEN the response returns only typed metadata: `id, target_id, status, triage, bucket`, and nullable `plan_status` and `verification`
- AND triage and bucket are derived from the record's bucket directory
- AND no record body, source code or log is exposed

### scenario.reflections.list-open-gaps — Status lists the current change's open gap history

- GIVEN a managed change with open gap history for the selected target, including participating component gaps for a coordinating Module
- WHEN status is requested for that target
- THEN the response includes `gap_records`, each with `id` (a digest), `target_id`, `task`, `phase`, the existing structured gap, `status open|resolved`, and nullable `reflection_id`
- AND status without a managed change returns an empty `gap_records` list

## Capturing development gaps

### scenario.reflections.capture-gap — record-gaps promotes a selected open gap into a pending Reflection

- GIVEN nonempty `gap_ids` selected from the current change's open gap history and `reflection_ids` is empty
- WHEN record-gaps is invoked
- THEN a pending Reflection is created for each gap using the existing allocator, record parser and buckets
- AND the record stores the validated gap target as its attribution, the gap's question, blocked step and needed contract, and its originating context, change and phase as evidence
- AND the source gap remains open and keeps its history
- AND the record stores the Module's unique `module.md` as its collection entry in `concerns`, independently of registry document order

### scenario.reflections.repeat-capture-reuses-link — Repeating an already-captured gap returns the existing link

- GIVEN a gap already linked to a Reflection by an earlier record-gaps call
- WHEN record-gaps is invoked again with the same gap id
- THEN the response reuses and returns the existing linked id
- AND no duplicate record is created

### scenario.reflections.reject-invalid-gap-selection — record-gaps rejects a foreign, resolved or implicit selection

- GIVEN a gap id that is foreign to the selected target's ownership or already resolved, or an omitted or empty `gap_ids` list
- WHEN record-gaps is invoked
- THEN the request fails as an invalid or stale reference
- AND no record is created or reused

record-gaps's explicit, non-implicit selection contract is a Module requirement; see
[req.reflections.explicit-gap-selection](module.md#req.reflections.explicit-gap-selection) and
[req.reflections.no-implicit-gap-selection](module.md#req.reflections.no-implicit-gap-selection).

`concerns` is provenance, not inferred ownership. The owning target or a coordinating Module
containing that component may capture a gap; foreign or resolved gaps are rejected. Pure
read/assessment requests never trigger capture. Existing scenario-owned records are selected with
the current owning `target_id` and optional `focus_id`, preserving their historical `feature`
field. The public metadata above is sufficient for selection without reading control files.

## Included provider definitions

When a consumer encounters a defective or missing provider guarantee, its blocked-step gap stays
attributed to the selected task/consumer. `needed_contract` and the evidence identify the canonical
definition's sole owner, document and included source digest when known. Capturing that gap retains
both roles rather than relabeling a foreign scenario as consumer-owned. Investigation may propose
an owner-routed repair through Development; capture alone grants no provider Spec/code access.
Context or definition changes require fresh assessment and do not silently close the record.

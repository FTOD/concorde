```concorde-document
{
  "id": "document.reflection.boundary",
  "targets": ["service.reflections"],
  "main_visible": true
}
```

# Reflection service

## feature.reflections.triage

A Reflection records a problem and human comments independently of implementation. Its stable R-NNN
identity is allocated monotonically by .concorde/reflections/index.json {schema_version:1,high_water}.
The canonical record is .concorde/reflections/<bucket>/R-NNN.md, with frontmatter id,title,phase,date,
feature,kind,concerns,status,triage; optional human_intervention and resolution_note. The historical
field `feature` accepts a registered target or one of its local Feature/API IDs. Required sections
are Context, Expected, Observed, Impact, Evidence, Triage Analysis, Proposed Resolution, Intervention
Rationale, User Comments and Occurrences. Original problem and human comments are preserved by triage.

status is open|resolved|dismissed. triage is pending|complete; complete triage requires
human_intervention required|not-required. Buckets are pending, needs-comments or planned according to
triage/intervention state. The host owns relocation. Resolved/dismissed records need a human disposition
and resolution_note before deterministic removal; Git history preserves the record.

Public concorde-reflections-triage takes the common invocation@3 envelope and a request@1 containing
target_id, action status|investigate|implement|merge|close, reflection_ids (unique string array), and
optional task,focus_id,constraints,change_id. Mutations require explicit nonempty reflection_ids, all
attributed to the selected target or its local focus IDs. Status returns only typed metadata: id,
target_id,status,triage,bucket,nullable plan_status and nullable verification. It exposes no record
body, source code or logs to ambient cognition. Merge removes records only after existing Git merge
checks; it does not perform a Git merge.

Investigation of a component is a read-only implementation stage. Its concorde-reflection-selection@1
contains exact HEAD and records [{id,path,digest,content}]; only the component's explicitly owned code
is readable. A Domain cannot own code and is an unsupported investigation target; select a participating component.
If its ownership is unclear, a separately bound context-solving task can identify the missing facts.
The result returns exactly selected findings in order: reflection_id,verified_commit,observed_state
(reproduced|not-reproduced), verification,analysis,resolution,intervention_rationale,human_intervention,
route (fast-loop|plan|dismiss|blocked), effort (small|medium|large), files,steps,validation,risks and
protocol_change. Verification must match admitted HEAD; record and code bytes must remain unchanged.
Files stay within component ownership. Non-reproduced requires dismissal recommendation and human
intervention; fast-loop requires small effort. Section values may not inject document-level headings.

The host preserves reports and writes evidence-bound plans in configured plans_dir. Config controls
require_approval; new or changed resolutions do not inherit stale approval. Implementation requires
reproduction, no outstanding human intervention and an approved route/plan. It composes a fresh
`concorde-dev-loop` with intended behavior only; investigation text/code/logs are excluded from Spec-stage inputs.
Success marks the plan implemented while leaving human disposition of the report independent.
Protocol changes in Concorde require the explicit evolve-protocol workflow.

## Main routing view

Reflection record selection, status, investigation coordination, approval and disposition remain on
`service.reflections`; this Service has no separately registered child Module. When an approved
resolution becomes ordinary product work, its typed route selects the responsible target named by
the Reflection rather than granting this Service access to that target's Spec.

## Explicit promotion of development gaps

The `record-gaps` action selects nonempty gap_ids from the current change's open gap history and
requires reflection_ids=[]. It creates pending specification Reflections using the existing allocator,
record parser and buckets. Each record stores the validated gap target as feature ownership, its
question/blocked step/needed contract and originating context/change/phase as evidence. The first
registered document is the collection entry in concerns, not inferred ownership. The owning target
or a coordinating Domain containing that component may capture it; foreign or resolved gaps are
rejected. Repeating capture reuses the linked ID. The existing gap remains open and retains its
history; capture is distinct from investigation, approval, implementation and human disposition.
Pure read/assessment requests never trigger capture. Existing Feature/API-owned records are selected
with the current owning target_id and optional focus_id, preserving their historical feature field.

The read-only reflections-triage `status` response exposes `gap_records`, each with id (a digest),
target_id, task, phase, the existing structured gap, status=open|resolved, and nullable reflection_id.
It lists current change history owned by the selected target, including participating component gaps
for a coordinating Domain. Use the returned id values as record-gaps gap_ids; IDs remain stable across
context-only retries and are not calculated by the caller. Status without a managed change returns
an empty list. record-gaps requires a nonempty explicit list and reflection_ids=[]: omitted/empty
lists never mean all; unknown or resolved IDs fail as stale_reference. A repeated capture returns
the existing link. The public metadata is sufficient for selection without reading control files.

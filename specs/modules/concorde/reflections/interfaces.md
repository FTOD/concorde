```concorde-document
{
  "id": "document.reflections.interfaces",
  "targets": [
    "module.reflections"
  ],
  "main_visible": true
}
```
# Reflection service

## feature.reflections.triage

A Reflection records a problem and human comments independently of implementation. Its stable R-NNN
identity is allocated monotonically by .concorde/reflections/index.json {schema_version:1,high_water}.
The canonical record is .concorde/reflections/<bucket>/R-NNN.md, with frontmatter id,title,phase,date,
feature,kind,concerns,status; optional resolution_note. The historical
field `feature` accepts a registered target or one of its local Feature/interface IDs. Required sections
are Context, Expected, Observed, Impact, Evidence, Triage Analysis, Proposed Resolution, Intervention
Rationale, User Comments and Occurrences. Original problem and human comments are preserved by triage.

status is open|resolved|dismissed. The bucket directory is the only record of triage state: pending
holds an untriaged problem, and planned or needs-comments hold a completed one, according to whether a
developer must comment. Investigation fills the triage sections and moves the record into its bucket in
one deterministic action; a record whose triage sections contradict its bucket, or that lies outside
every bucket, is rejected. Resolved/dismissed records need a human disposition
and resolution_note before deterministic removal; Git history preserves the record.

Public concorde-reflections-triage takes the common invocation@3 envelope and a request@1 containing
target_id, action status|record-gaps|investigate|implement|merge|close, reflection_ids (unique string array), and
optional task,focus_id,constraints,change_id. Report mutations require explicit nonempty reflection_ids, all
attributed to the selected target or its local focus IDs; record-gaps instead requires nonempty
gap_ids and reflection_ids=[], as specified below. Status returns only typed metadata: id,
target_id,status,triage,bucket (triage and bucket are derived from the record's bucket directory),
nullable plan_status and nullable verification. It exposes no record
body, source code or logs to ambient cognition. Merge removes records only after existing Git merge
checks; it does not perform a Git merge.

Investigation of a component is a read-only implementation stage. Its concorde-reflection-selection@1
contains exact HEAD and records [{id,path,digest,content}]; only the component's explicitly owned code
is readable. A Module without referenced Implementation Specs is an unsupported code-investigation target; select a Module with explicit file bindings.
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
The independent Protocol standard is outside the registered Module ownership available to a
reflection investigation. A result that requires changing that standard cannot be applied through
this Module-bound investigation.

## Main routing view

Reflection record selection, status, investigation coordination, approval and disposition remain on
`module.reflections`; this Module has no separately registered child Module. When an approved
resolution becomes ordinary product work, its typed route selects the responsible target named by
the Reflection rather than granting this Module access to that target's Spec.

## Explicit promotion of development gaps

The `record-gaps` action selects nonempty gap_ids from the current change's open gap history and
requires reflection_ids=[]. It creates pending specification Reflections using the existing allocator,
record parser and buckets. Each record stores the validated gap target as feature ownership, its
question/blocked step/needed contract and originating context/change/phase as evidence. The Module’s unique local `module.md` is the collection entry in concerns, independently of
registry document order; concerns is provenance, not inferred ownership. The owning target
or a coordinating Module containing that component may capture it; foreign or resolved gaps are
rejected. Repeating capture reuses the linked ID. The existing gap remains open and retains its
history; capture is distinct from investigation, approval, implementation and human disposition.
Pure read/assessment requests never trigger capture. Existing Feature/interface-owned records are selected
with the current owning target_id and optional focus_id, preserving their historical feature field.

The read-only reflections-triage `status` response exposes `gap_records`, each with id (a digest),
target_id, task, phase, the existing structured gap, status=open|resolved, and nullable reflection_id.
It lists current change history owned by the selected target, including participating component gaps
for a coordinating Module. Use the returned id values as record-gaps gap_ids; IDs remain stable across
context-only retries and are not calculated by the caller. Status without a managed change returns
an empty list. record-gaps requires a nonempty explicit list and reflection_ids=[]: omitted/empty
lists never mean all; unknown or resolved IDs fail as stale_reference. A repeated capture returns
the existing link. The public metadata is sufficient for selection without reading control files.

Read-only reflection investigation receives the selected Module contract and explicitly granted
code files. It receives no Implementation Spec bodies or file permissions for those documents.
Code-writing tasks separately receive their referenced Implementation Specs.

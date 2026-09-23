# Pi session requirements

The Module-wide obligations of [Pi session](module.md). Each is stated once; the
[scenarios](scenarios.md) show them in concrete situations.

## The concorde tool

### req.session.public-only — The tool offers exactly its catalog

The `concorde` tool SHALL accept exactly the capabilities listed in the catalog embedded in its session entry.

### req.session.unchanged-input — The tool adds no decision of its own

The `concorde` tool SHALL place the caller's `input` into the capability request as its `data` without adding, removing or changing any field.

Every admission, permission and acceptance decision belongs to the Host; the tool's own refusals
are limited to an unknown capability, a missing `input` and a selection that failed verification.

### req.session.failure-is-error — Non-success is never reported as success

The `concorde` tool SHALL return a tool error for every run whose launcher was cancelled, exited non-zero, printed no envelope, or printed an envelope with status `blocked` or `failed`.

## Selection

### req.session.private-selection — Selections name exact current bytes

Session selection SHALL refuse any entry, catalog, launcher or source path that is missing, aliased, outside the candidate or different from the candidate's current build.

### req.session.no-selection-fallback — No substitute build

A private session entry or a tester SHALL NOT load, verify against or run any entry, catalog, launcher or interpreter other than those of its selected candidate.

### req.session.selection-reverified — Selections are checked before use

A private session entry SHALL verify its selection before it registers the `concorde` tool and again before every tool call.

### req.session.selection-not-evidence — A selection claims nothing about execution

A session selection SHALL NOT carry or be reported as evidence that Pi loaded an entry, that a tool ran or that a model executed.

## Task subagents

### req.session.single-definition — One definition per Task subagent

Every Task subagent SHALL have exactly one canonical definition, from which its Pi projection is rendered.

A projection that differs from its definition is refused by the build, never used as a second
authority.

### req.session.family-boundary — Task subagents have no stage contract

A Task subagent SHALL NOT receive a domain stage input type, a stage result type or a single-Module grant.

### req.session.no-delegation — Task subagents do not delegate

A Task subagent definition SHALL exclude the `subagent` tool.

### req.session.tester-commands-only — The tester runs commands only through its tool

The tester SHALL be able to use no tool other than `read`, `grep`, `find`, `ls`, `test_command`, `structured_output` and `contact_supervisor`.

### req.session.tester-failure-visible — A failed tester command is a failed tool call

The tester command tool SHALL fail every call whose command exited non-zero, was cancelled, raised an error or left an incomplete evidence export.

### req.session.maintenance-source-only — The maintenance worker works only on Concorde

The maintenance guard SHALL block every tool call of a maintenance worker whose working directory is not a Concorde source checkout.

### req.session.frozen-continuation — Launch instructions are fixed

A Task subagent's instructions and extension list SHALL be fixed when it is launched and never reloaded while it runs.

## Source-only assets

### req.session.source-only — Source maintenance assets are marked source-only

The maintenance worker definition, the coordinator instructions and the maintenance and brief lifecycle extensions SHALL be classified source-only, so that no installed layout contains them.

### req.session.coordinator-user-session-only — Coordinator instructions reach only the source user session

The coordinator instructions SHALL be loaded only by the source user session, never by a Task subagent or an Agent.

## Task brief

### req.session.brief-once — A brief is injected once per compaction

The brief lifecycle SHALL inject the current task brief at most once for each completed compaction and never for a compaction that did not complete.

# Issues requirements

The Module-wide obligations of Issues. The [entry](module.md) explains them; the
[scenarios](scenarios.md) show them in concrete situations.

## Reporting

### req.issues.report-control — Reporting does not control execution

Accepting an Issue report SHALL NOT stop the reporting worker, start a repair or change the outcome of the worker's task.

A worker can report several problems and still complete its task. Whether a problem stops the task
is stated separately, by a Blocker in the worker's result.

### req.issues.scope — Issues never widen authority

Reporting, selecting or solving an Issue SHALL NOT widen any worker's Spec, implementation or command Grant.

The reporting tool writes only through the Host, the owner a report names must already be in the
reporter's context, and a solve stays bound to the Module the Issue is about.

### req.issues.host-writes — Only the Host writes Issue records

Every write to a file under `.concorde/issues/` SHALL go through the Host's Issue store.

### req.issues.references — Results reference only known reports

A stage result SHALL reference only Issue reports made in the same worker run or explicitly admitted as that worker's input.

## Records

### req.issues.retention — Reports are never rewritten

The Issue store SHALL NOT modify or remove an accepted report, including when the Issue is closed or reopened.

Restoring a solve's own unfinished close does not touch reports either: it removes only the
disposition that solve added, as described under
[the closing journal](solving.md#concept.issues.journal).

## Solving

### req.issues.verified-resolution — Resolution needs current verification

The solve workflow SHALL write a `resolved` disposition only after Issue-specific and ordinary reviews completed without blocking findings on the Module's current Specs and implementation files.

### req.issues.bounded-decisions — Solving is bounded

One solve SHALL launch the Issue solver at most six times for an unchanged set of inputs and clarification.

### req.issues.journal-first — The journal precedes the close

The Host SHALL save the closing journal in the candidate before it writes a solver disposition to the Issue.

### req.issues.ready-boundary — Solving stops before delivery

A successful solve SHALL end at a ready candidate without delivering it or changing the primary branch.

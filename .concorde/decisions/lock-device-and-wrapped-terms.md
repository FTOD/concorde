# Decision log: lock-device-and-wrapped-terms

Goal: Match /proc/locks holders by device and inode so stop_task never signals an unrelated process, and make CHK.term.unlinked report multi-word terms wrapped across lines, linking the uses it then finds

## Brief (main agent, 2026-10-02)

Two Issues recorded by task flaky-close-and-title-wrap. Read each with
`python3 scripts/concorde.py issues show <id>` first.

- I-bf5871eb5db656db9d125248ebafe458 (module.tracing, medium, obvious-fix), first: locks.holder_pids
  matches /proc/locks entries by inode alone, without the device, so stop_task could SIGTERM an
  unrelated process. Match on device and inode (major:minor:inode as /proc/locks gives it), with a
  test covering a same-inode entry on another device.
- I-74f24f06b9025c9e8571d48f5b7bf019 (module.spec, low, preferred-fix): CHK.term.unlinked does not
  report a multi-word term whose use wraps across lines. Fix the check as the Protocol asks. The
  fix is expected to raise about ten real warnings in Specs of other Modules. The main agent
  allows this task to make exactly those changes there, linking each term's first use (or
  rephrasing where the word is not the term), since no other task is open and each is a
  mechanical link; touch nothing else in those Modules, and list every file changed in the report.

Done when spec-validation reports no warning. Verify with build --check, spec-validation and the
full suite, then task-validation and delivery, and report.

## Task session decisions (2026-10-02)

- I-bf5871eb5db656db9d125248ebafe458: holder_pids now compares (major, minor, inode) of each
  FLOCK entry, major and minor parsed as hexadecimal, against os.major/os.minor of st_dev and
  st_ino. The table path became the module constant `locks.LOCK_TABLE` so the test can feed a
  crafted table. Added scenario.tracing.lock-table-holders (entries on another major, another
  minor, another inode, a POSIX lock and a waiter are not holders) and reworded the tracing
  contract's observer sentence to "the file's device and inode". Reason: the brief asks for a
  device-and-inode match with a test; the contract named only the inode.
- I-74f24f06b9025c9e8571d48f5b7bf019: term_uses no longer skips a match holding a line break; a
  wrapped use is reported on the line it starts on, its end column the end of that line.
  Scenario scenario.spec.term-unlinked gained that sentence.
- Turning wrapped uses on raised the 10 warnings the Issue lists, but one,
  dogfooding/module.md:184 ("in a task\n`concorde task escalate` records"), was no use: the two
  words were apart by inline code, which prose_text blanked with spaces, so `[\s-]+` matched
  across it (the same false positive was possible on one line, "task `x` records", and across a
  link). Fixed in module.spec rather than rephrasing dogfooding: prose_text now blanks code,
  links and anchors with "\0" (syntax.BLANK), which no title's word separator matches; paragraph
  splitting and the sentence-start test treat it as a space as before, and _links keeps its space
  blanking. Test added; the scenario names "a title's words apart by code or a link" as no use.
  dogfooding/module.md is therefore unchanged.
- The other 9 uses were linked at their first use, the paragraph from the line before reflowed to
  100 columns, except execution/checks/module.md:206, where "task records" was the verb
  "records", rephrased to "writes its timings into the trace".

## Report 1 to the main agent (spec-review quality criteria), 2026-10-02T04:05:02Z

Delivered: ff6ac2cd (concorde: deliver lock-device-and-wrapped-terms) on concorde/lock-device-and-wrapped-terms; steps 5db814af and ede5651b. task-validation ready; build --check no differences; spec-validation success with no warning; full suite 955 passed, 5 skipped. Resolves (added with task resolve): I-bf5871eb5db656db9d125248ebafe458, I-74f24f06b9025c9e8571d48f5b7bf019.

I-bf58 (obvious-fix): locks.holder_pids matches (major, minor, inode), major/minor hex, against st_dev and st_ino; table path is now locks.LOCK_TABLE. New scenario.tracing.lock-table-holders with a test (another major, another minor, another inode, POSIX entry, waiter: none named), plus a live-lock test. Tracing contract sentence now says "the file's device and inode".

I-74f2 (preferred-fix, the reporting fix chosen as the Issue preferred): term_uses reports a wrapped title on the line it starts on; scenario.spec.term-unlinked says so. Decision beyond the Issue's sketch: one of the 10 listed warnings, dogfooding/module.md:184 ("in a task\n`concorde task escalate` records"), was a false positive. The two words were separated by inline code that prose_text blanked with spaces. I fixed this in module.spec instead of editing dogfooding: code, links and anchors are now blanked with "\0" (syntax.BLANK), so a title's words never match across them. This also happened on a single line. Paragraph splitting and the sentence-start test behave as before, link parsing is unchanged, and there is a new test plus a scenario clause. dogfooding/module.md is unchanged.

Files changed in other Modules (one link each at the first use, paragraph reflowed to 100 columns): specs/concorde/coordination/main-session/contracts.md (task records), specs/concorde/e2e/cases/module.md (brownfield workflow), specs/concorde/execution/commands/delivery/module.md (run store), specs/concorde/execution/workers/module.md (run lock), specs/concorde/issues/interface.md (main agent), specs/concorde/issues/module.md (Concorde repository), specs/concorde/module.md (deny rules), specs/concorde/spec-tooling/spec-mcp/contracts.md (main agent). Rephrased, not linked: specs/concorde/execution/checks/module.md, where "task records" was the verb ("records into the trace" became "writes its timings into the trace"). Own Modules: src/concorde/tracing/locks.py, src/concorde/spec/syntax.py, tests/concorde/tracing/test_locks.py, tests/concorde/spec/test_checks.py, specs/concorde/tracing/{contracts,scenarios}.md, specs/concorde/spec-tooling/spec/scenarios.md.

Open: nothing. Decisions are recorded in the decision log.

## Closed: merged, 2026-10-02T04:05:23Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit ff6ac2cd26d415eeb821d102a514e9eac30498cd into main and closed it as merged. Nobody answers a report after that.

# Decision log: run-liveness-lock

Goal: Decide whether a run's runner still lives from a lock the runner holds on its run directory for the run's whole life, not from its process identifier, which is only meaningful in the runner's own PID namespace (a runner started in a sandboxed shell records pid 2, which the host reads as kthreadd, so the pi run view counts a long-dead run as running)

## Decisions taken without the developer

1. **Liveness signal.** Options: (a) keep the process identifier and also record the PID namespace
   and start time, (b) a per-run `flock` held by the runner. Chose (b): it works from every PID
   namespace that sees the run store, survives PID reuse, and the kernel releases it however the
   runner ends. (a) cannot help an observer inside a sandbox look at a runner on the host.
2. **Lock target.** Locked the run directory itself (flock on an O_RDONLY directory descriptor)
   instead of adding a lock file, so the run store gains no new file. `status.json` could not be
   used because it is replaced atomically.
3. **Node side.** Node has no flock, so the pi run view reads `/proc/locks` once per refresh and
   matches the run directory's inode number. It compares only the inode, not the device, because
   the device in `/proc/locks` differs from `stat`'s on btrfs subvolumes. Shared (READ) entries are
   ignored because they are probes. Where `/proc/locks` is missing, it falls back to the recorded
   process identifier. A run whose `result.json` exists counts as alive, so a run that ended
   properly between two reads is not reported as `failed`.
4. **Worker pairing (in scope, same root cause).** Every sandboxed runner is process 2 in its
   namespace, so pairing workers by `host_pid` would mix up the workers of concurrent sandboxed
   runs. Worker progress files now record `operation_run_id`, and the view pairs workers by it.
5. **No compatibility shim** (rapid-iteration rule). Runners started by branch code from before
   this change hold no run lock. Until those task branches merge main, the new view shows their
   live runs as ended. Seen now: `r-20260928T191139-task_validation-199d7683` of task
   glossary-admission. Merge safety is not affected, because `task merge` waits on the workspace
   lock, not on run state.
6. Left alone: the Tasks and Workflows scenario wording "whose runner process no longer exists / has
   ended". It stays true (the runner ended) and those Modules are outside this task. Their tests
   were adjusted to hold the run lock, and `scenario.tasks.interrupted` now also covers a stale
   `host_pid` of 1.
7. pi task-session rounds still use `supervisor_pid`: the supervisor is started by the pi extension
   itself, in the extension's own PID namespace. Not changed.

## Verification

- Real PID-namespace check (`unshare --user --pid --fork --mount-proc`): a holder that is PID 1 in
  its own namespace → host `run_state` = running and TS `runnerAlive` = true; after it ends → lost
  and false.
- Primary run store: the stale run `r-20260928T163919-task_validation-c5b5a4b4` (host_pid 2):
  old `alive(pid)` true, new `runnerAlive` false.
- build --check, spec-validation (0 findings), full pytest suite: 687 passed, 4 skipped.

## Closed: merged, 2026-09-28T19:26:39Z

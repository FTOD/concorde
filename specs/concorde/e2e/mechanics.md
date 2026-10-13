# End-to-end testing mechanics

This document gives the exact mechanics behind two promises of
[End-to-end testing](module.md), for the people who change them:

- How the [owners case](module.md#owners-case) holds the task's workspace lock around a launch and
  finds the run that launch started.
- How `run` [chooses the workflow result](module.md#running-a-workflow) it prints.

## The owners case's lock and launch

<a id="the-owners-cases-lock-and-launch"></a>

The case starts each run while it holds the task's [workspace
lock](../glossary.json#concept.workspace-lock).
The **launcher** of a run is the process that starts it:

- For the unowned run, the process the case itself starts.
- For the owned run, the first session's `claude` process.

The case judges only the run its own launch started.
It finds that run in the [run store](../glossary.json#concept.run-store) as the new run of the task
whose runner descends from the launcher.
The runner is the process the [run progress file](../glossary.json#concept.run-progress-file)'s
`host_pid` names.
Another run of the same workspace, launched by any other process, is never taken for it.
So the case reads the process tree of the operating system, Linux's `/proc`.
It must share the launcher's PID namespace.
A launcher whose commands run in a PID namespace of their own, such as a sandbox's, never has its run
found. The case then stops with `live_timeout`.
So the run cannot start its work before the case sees its launch completed.
The case takes that lock as Execution's runs take it.
The case holds an exclusive file lock on `locks/workspaces/<task>.lock`.
That path is under the `.concorde` named by the task worktree's
[workspace binding](../glossary.json#concept.workspace-binding).
When a run still holds the lock, the case waits at most the case's limit.
When the case leaves the phase, however the phase ends, it releases the lock.
For an owned run, the case first waits until the owner ends the turn in which it launched the run.
The case still holds the lock during this wait.
For either run, the case then waits until the run is in the
[run store](../glossary.json#concept.run-store), waiting in its lobby.
Only then does it release the lock.
The launching turn and the run's arrival share one deadline: the case's limit counted from the
launch.
So the case holds the lock at most that long after the launch.
The run therefore ends only after the launching turn ends.
Within the time the case judges, the run's end reaches the owner as a wake, never as the launching
tool's own answer.

The run queues for the lock as Execution's
[`--wait <seconds>`](../execution/module.md#waiting-for-a-busy-workspace) lets it.
Its wait is twice the case's limit, 1200 seconds, so it outlasts every hold of the case.
When the case holds the lock, the run's wait never expires
([requirements](requirements.md#req.e2e.owners-queue)).
Another run can take the lock after the case releases it and hold it past the run's wait.
If this causes a refusal with `workspace_busy`, the run does no work, so there is no run end to
judge.
In that case, the case stops with `workspace_busy` naming that run's result.

After the release, the case waits for the run's result at most the run's wait, 1200 seconds.
That wait always outlasts what remains of the run's own wait for the lock.
So a refusal for a busy workspace always arrives before the case's deadline.

## Choosing the run's result

<a id="choosing-the-runs-result"></a>

Before it starts, `run` counts the saved results of the
[workflow record](../glossary.json#concept.workflow-record).
It takes only a result saved since.
When the record holds no more saved results after the run than before it, the tool fails with
`no_result` naming both counts.
When the newest saved result is missing, it fails with `no_result` naming the missing file.
So a result an earlier run of the task saved is never printed as this run's
([requirements](requirements.md#req.e2e.own-result)).

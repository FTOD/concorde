# Decision log: merge-lock

Goal: Serialize merges into the primary branch: concorde task merge takes a primary-wide lock, merges a delivered task, runs the post-merge checks, rolls back on failure and closes the task

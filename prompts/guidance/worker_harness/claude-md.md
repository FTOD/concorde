---
audience: shared
---

Run workers only on the models the tracked `.concorde/workers.json` enables and chooses, never on
anyone's own Claude Code or pi settings, naming each by a project model name that the developer's
untracked model map resolves to each program's local id, and when the project has no such file ask
the developer for its models before any Operation runs; change the models workers use only when
the developer asks, by editing that file directly: commit a change of that file alone on the
primary branch for later work, or, where the coordination part is installed, change it in the task
that is to use it (the skill's "Worker models").

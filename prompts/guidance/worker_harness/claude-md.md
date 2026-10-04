---
audience: shared
---

Run workers only on the models the tracked `.concorde/workers.json` enables and chooses. Never run
them on anyone's own Claude Code or pi settings. Name each model by a project model name that the
developer's untracked model map resolves to each program's local id. When the project has no such
file, ask the developer for its models before any Operation runs. Change the models workers use
only when the developer asks, by editing that file directly. For later work, commit a change of
that file alone on the primary branch. Or, where the coordination part is installed, change it in
the task that is to use it (the skill's "Worker models").

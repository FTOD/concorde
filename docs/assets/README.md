# README screenshots

These are real Chromium screenshots of Concorde interfaces, not mockups or edited application
content. The docsite image was refreshed from the local verified Protocol-10 production build on
2026-09-19. The other images retain their 2026-09-10 observations as identified below.

| File | Source and visible state |
| --- | --- |
| `concorde-docsite.png` | Local Protocol-10 production build, `/specs/concorde/module`, showing the Module Specs, Implementation Specs, Spec Protocol and Agent Graphs tabs, the provenance bar, the Module tree and the root entry's Purpose and Terminology. This is local build evidence, not a claim that deployment has occurred. |
| `concorde-module-graph.png` | Historical screenshot of the retired standalone docsite graph, filtered to `composes`. Retained as history; the current docsite has no Graph tab and the README no longer presents this image as an active feature. |
| `concorde-studio.png` | The graph and input pane of LangGraph Studio connected to this checkout's local Agent Server, with `concorde-main` selected and the README's `describe-policy` input entered in View Raw. No run has been submitted in this screenshot. |

The Studio screenshot uses its local connection without hosted LangSmith tracing. Dismissible
service notices were closed through the UI. Run interactions require LangSmith sign-in; the
README's policy preview was separately verified through the CLI-to-Studio transport and returned
`status: described`. The screenshot does not claim an agent execution or a completed development
change.

To refresh these images, follow the README's launch instructions, open the corresponding views,
and capture the current interface. Preserve the distinction between the published site and
Studio's input versus completed-run states.

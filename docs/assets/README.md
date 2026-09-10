# README screenshots

Captured on 2026-09-10 from Concorde itself using Chromium. These are real interface screenshots;
they contain no generated mockups or edited application content.

| File | Source and visible state |
| --- | --- |
| `concorde-docsite.png` | [Published Spec Module](https://ftod.github.io/concorde/specs/concorde/spec/module), showing the Module tree, source provenance, purpose and requirements. |
| `concorde-module-graph.png` | [Published architecture graph](https://ftod.github.io/concorde/graph), filtered to `composes`. Nodes were dragged apart using the graph's normal controls to make the labels readable. |
| `concorde-code-graph.png` | Official Understand Anything Viewer 2.9.0, running locally against this checkout's existing `.ua/knowledge-graph.json`. Learn mode shows the project layers and the available tour. |
| `concorde-studio.png` | The graph and input pane of LangGraph Studio connected to this checkout's local Agent Server, with `concorde-main` selected and the README's `describe-policy` input entered in View Raw. No run has been submitted in this screenshot. |

The code graph is an existing analysis snapshot, with metadata dated 2026-09-10 and source commit
`38490c289f08f82de29deb1310e6b79ab4eed32b`. Its summaries and tour are analysis output, not authored
Specs or evidence of current code conformance. A fresh `ua-graph` export derives Module structure
from the Spec registry and does not reproduce this code analysis or tour.

The Studio screenshot uses its local connection without hosted LangSmith tracing. Dismissible
service notices were closed through the UI. Run interactions require LangSmith sign-in; the
README's policy preview was separately verified through the CLI-to-Studio transport and returned
`status: described`. The screenshot does not claim an agent execution or a completed development
change.

To refresh these images, follow the README's launch instructions, open the corresponding views,
and capture the current interface. Preserve the distinction between the published site, an
existing code-analysis snapshot, and Studio's input versus completed-run states.

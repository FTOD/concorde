---
name: concorde-step
description: Runs one Concorde workflow step (concorde workflow step --stdin) without a model and returns its step outcome
runner:
  type: external-cli
  command: .concorde/bin/concorde
  args: [workflow, step, --stdin]
  promptDelivery: stdin
async: true
systemPromptMode: replace
inheritProjectContext: false
inheritGlobalContext: false
inheritSkills: false
---

Concorde runs one workflow step: it starts or awaits the Operation run named by the JSON step
request in the prompt and prints the step outcome.

---
name: concorde-report
description: Reports a Concorde workflow's result (concorde workflow report --stdin) without a model
runner:
  type: external-cli
  command: .concorde/bin/concorde
  args: [workflow, report, --stdin]
  promptDelivery: stdin
async: true
systemPromptMode: replace
inheritProjectContext: false
inheritGlobalContext: false
inheritSkills: false
---

Concorde builds a workflow's result from the task record named by the JSON request in the prompt
and prints it.

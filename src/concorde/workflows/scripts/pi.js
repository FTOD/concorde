// pi adapter: every step is carried by the command-runner agent `concorde-step`, which runs
// `concorde workflow step --stdin` without a model and waits until the run has ended; its
// standard output, the step outcome, is the child's output. The report is carried the same way
// by `concorde-report`, which runs `concorde workflow report --stdin`. What counts is what the
// hosts recorded.

if (!args || !args.task || !args.module || !args.mode) {
  throw new Error("concorde workflow needs args { task, module, mode } and optionally answers, retry and restart")
}

function parsed(result) {
  if (!result || !result.output) return null
  try {
    const value = JSON.parse(result.output)
    return value && value.error && !value.state ? null : value
  } catch (error) {
    return null
  }
}

function step(key, argv) {
  // Optional fields are left out when they hold their default.
  const request = { task: args.task, workflow: WORKFLOW, mode: args.mode, key: key, argv: argv }
  if (args.answers && args.answers[key]) request.answers = args.answers[key]
  if (args.retry && args.retry.indexOf(key) >= 0) request.retry = true
  if (args.restart && args.restart[key]) request.restart = args.restart[key]
  return runs.run(key, { agent: "concorde-step", task: JSON.stringify(request) }).then(parsed)
}

function report(lost) {
  const request = { task: args.task, lost: lost ? [lost] : [] }
  return runs.run("report", { agent: "concorde-report", task: JSON.stringify(request) }).then(function (result) {
    let value = null
    try {
      value = JSON.parse(result.output)
    } catch (error) {
      value = { status: "unknown", summary: String(result && result.output) }
    }
    return {
      workflow: WORKFLOW,
      task: args.task,
      reported: { status: value.status, summary: value.summary },
      result: ".concorde/tasks/" + args.task + ".workflow.json",
    }
  })
}

function note(text) {
  console.log(text)
}

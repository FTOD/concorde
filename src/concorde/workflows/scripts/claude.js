// Claude Code adapter: every step is carried by a small subagent that runs `concorde workflow
// step` with Bash, repeats it while the run is still going (exit status 3, at most nine minutes
// per call, under Bash's ten-minute limit), and returns the step outcome it printed. What counts
// is what the hosts recorded: the final report is built by `concorde workflow report`.

if (!args || !args.task || !args.module || !args.mode) {
  throw new Error("concorde workflow needs args { task, module, mode } and optionally answers, retry and restart")
}
const CONCORDE = args.concorde || ".concorde/bin/concorde"

function quote(word) {
  return "'" + String(word).replace(/'/g, "'\\''") + "'"
}

const STEP_SCHEMA = {
  type: "object",
  required: ["key", "state"],
  properties: {
    key: { type: "string" },
    run_id: { type: ["string", "null"] },
    state: { type: "string" },
    status: { type: ["string", "null"] },
    summary: { type: ["string", "null"] },
    decision_points: { type: "integer" },
    created_modules: { type: "array", items: { type: "object" } },
    ready: { type: ["boolean", "null"] },
    error: { type: ["object", "null"] },
  },
}

function relay(command, lines, label, schema) {
  return agent(
    [
      "Run exactly this command with the Bash tool, from the current working directory:",
      "",
      command,
      "",
    ].concat(lines).join("\n"),
    { label: label, schema: schema, model: "haiku", effort: "low" }
  )
}

function step(key, argv) {
  const request = {
    task: args.task,
    workflow: WORKFLOW,
    mode: args.mode,
    key: key,
    argv: argv,
    answers: (args.answers && args.answers[key]) || null,
    retry: Boolean(args.retry && args.retry.indexOf(key) >= 0),
    restart: (args.restart && args.restart[key]) || null,
  }
  // Only the request is quoted, so that the permission rule for `concorde workflow step` matches.
  const command = CONCORDE + " workflow step --json " + quote(JSON.stringify(request)) + " --wait 540"
  return relay(
    command,
    [
      "It prints one JSON object. Exit status 3 means the run is still going: run exactly the same",
      "command again, as many times as it takes. Once it exits with status 0 or 1, return the",
      "fields of the JSON object it printed last, unchanged. Run no other command and change no file.",
    ],
    "step " + key,
    STEP_SCHEMA
  )
}

function report(lost) {
  const command =
    CONCORDE + " workflow report --task " + quote(args.task) + (lost ? " --lost " + quote(lost) : "")
  return relay(
    command,
    [
      "It prints the workflow result as one JSON object, whatever its exit status. Return its",
      "status and summary unchanged. Run no other command and change no file.",
    ],
    "report",
    {
      type: "object",
      required: ["status", "summary"],
      properties: { status: { type: "string" }, summary: { type: "string" } },
    }
  ).then(function (value) {
    return {
      workflow: WORKFLOW,
      task: args.task,
      reported: value,
      result: ".concorde/tasks/" + args.task + ".workflow.json",
    }
  })
}

function note(text) {
  log(text)
}

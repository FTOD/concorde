// Claude Code adapter: every step is carried by small subagents, each running `concorde workflow
// step` once with Bash and returning the step outcome it printed. One call waits at most
// WAIT_SECONDS, under the Bash tool's default two-minute limit, and the script itself, not a
// model, asks again while the run is still going: the same key only waits, it never starts the
// run twice. An outcome that does not match the step it asked for counts as no answer, and the
// script asks again, a few times at most: a relay that retyped the command wrongly or returned
// nothing is not the step's result. What counts is what the hosts recorded: the final report is
// built by `concorde workflow report`, and a step left without an answer carries what its agents
// relayed last.

if (!args || !args.task || !args.module || !args.mode) {
  throw new Error("concorde workflow needs args { task, module, mode } and optionally answers, retry and restart")
}
const CONCORDE = args.concorde || ".concorde/bin/concorde"
const WAIT_SECONDS = 100
// At most this many calls for one step, about five and a half hours of waiting.
const MAX_CALLS = 200
const RUN_ID = /^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$/
// At most this many relays in a row that are no answer before a step counts as lost.
const RELAYS = 3
// For each step left without an answer, the last thing its agents relayed.
const relayed = {}

function quote(word) {
  return "'" + String(word).replace(/'/g, "'\\''") + "'"
}

const STEP_SCHEMA = {
  type: "object",
  required: ["key", "state"],
  properties: {
    key: { type: "string" },
    run_id: { anyOf: [{ type: "null" }, { type: "string", pattern: "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$" }] },
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

// A relayed outcome is used only when it names the step asked for and a real run (or none, for a
// refused step); anything else is treated as no answer, and the report says the step was lost.
function checked(outcome, key) {
  if (!outcome || typeof outcome.key !== "string") return null
  if (outcome.key.split("@")[0].split("#")[0] !== key) return null
  if (outcome.run_id !== null && outcome.run_id !== undefined && !RUN_ID.test(outcome.run_id)) return null
  return outcome
}

function step(key, argv) {
  // Optional fields are left out when they hold their default, so there is less to copy.
  const request = { task: args.task, workflow: WORKFLOW, mode: args.mode, key: key, argv: argv }
  if (args.answers && args.answers[key]) request.answers = args.answers[key]
  if (args.retry && args.retry.indexOf(key) >= 0) request.retry = true
  if (args.restart && args.restart[key]) request.restart = args.restart[key]
  // Only the request is quoted, so that the permission rule for `concorde workflow step` matches.
  const command =
    CONCORDE + " workflow step --json " + quote(JSON.stringify(request)) + " --wait " + WAIT_SECONDS
  let calls = 0
  let misses = 0
  function once() {
    calls += 1
    return relay(
      command,
      [
        "Copy the command character for character, quotes included. Run it once, in the",
        "foreground: it returns within two minutes. It prints one JSON object, whatever its exit",
        "status. Return the fields of that object exactly as printed. Do not run it again, run no",
        "other command and change no file.",
      ],
      "step " + key + (calls > 1 ? " (" + calls + ")" : ""),
      STEP_SCHEMA
    ).then(function (outcome) {
      const answer = checked(outcome, key)
      if (!answer) {
        misses += 1
        relayed[key] = outcome || null
        return misses < RELAYS && calls < MAX_CALLS ? once() : null
      }
      misses = 0
      delete relayed[key]
      if (answer.state === "running" && calls < MAX_CALLS) return once()
      return answer
    })
  }
  return once()
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
    const result = {
      workflow: WORKFLOW,
      task: args.task,
      reported: value,
      result: ".concorde/tasks/" + args.task + ".workflow.json",
    }
    // Unverified: what a step agent said, not what a host recorded, kept so that a refusal of
    // the step command (such as a mistyped request) is not lost from the error chain.
    if (lost && relayed[lost]) result.relayed = { key: lost, attempts: RELAYS, outcome: relayed[lost] }
    return result
  })
}

function note(text) {
  log(text)
}

// Claude Code adapter: every step is carried by small subagents, each calling the project MCP
// server's tool `workflow_step` once and returning the step outcome it answered. The server runs
// the workspace's own `concorde workflow step` as a process of its own, so no run depends on a
// relaying agent's turn or on a background command the session may end: a run started by the
// server lives until it ends. One call waits at
// most WAIT_SECONDS, and the script itself, not a model, asks again while the run is still going:
// the same key only waits, it never starts the run twice, up to MAX_CALLS calls for one step, a guard
// against a run that never ends. An outcome that does not match the step it asked for counts as no
// answer, and the script asks again, a few times at most: a relay that copied the request wrongly
// or returned nothing is not the step's result. What counts is what the hosts recorded: the final
// report is built by `concorde workflow report`, and a step left without an answer carries what its
// agents relayed last.

// The workflow runs in the bound workspace it is started in: the step tool works on the worktree
// the session started in, and the report command runs from the current working directory, whose
// workspace binding names the workspace.
// Every workflow takes mode, answers, retry and restart; a procedure checks its own arguments.
if (!args || !args.mode) {
  throw new Error("concorde workflow " + WORKFLOW + " needs args { mode } and optionally answers, retry and restart")
}
const CONCORDE = args.concorde || ".concorde/bin/concorde"
// The project MCP server's tool, as Claude Code names it for the server registered as `concorde`.
const STEP_TOOL = "mcp__concorde__workflow_step"
const WAIT_SECONDS = 100
// At most this many calls for one step, about five and a half hours of waiting: a runaway guard,
// after which the step resolves to the last outcome that said its run was still running.
const MAX_CALLS = 200
const RUN_ID = /^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$/
const DIGEST = /^@[0-9a-f]{8}$/
const STATES = ["running", "finished", "lost", "refused"]
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
    blocking: { type: ["object", "null"] },
    data: { type: "object" },
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

// A step agent's prompt: one call of the step tool with these arguments, nothing else.
function stepPrompt(argumentsText) {
  return [
    "Call the MCP tool " + STEP_TOOL + " exactly once, with exactly these arguments:",
    "",
    argumentsText,
    "",
    "If the tool is not loaded yet, load it first with ToolSearch and the query",
    "\"select:" + STEP_TOOL + "\". Copy the arguments character for character. The tool answers",
    "within two minutes with one JSON object, or with an error. Return the fields of that object",
    "exactly as answered. Do not call it again, use no other tool and change no file.",
  ].join("\n")
}

// A relayed outcome is used only when it names the step key asked for (the base key, the restart
// label after # and, for an answered step, an answers digest after @, which the script checks by
// its shape), a step outcome's state and a real run, or none only for a refused step or one still
// waiting to start; anything else is treated as no answer, and the report says the step was lost.
function checked(outcome, request) {
  if (!outcome || typeof outcome.key !== "string") return null
  const key = request.key + (request.restart ? "#" + request.restart : "")
  if (request.answers) {
    if (outcome.key.slice(0, key.length) !== key || !DIGEST.test(outcome.key.slice(key.length))) return null
  } else if (outcome.key !== key) {
    return null
  }
  if (STATES.indexOf(outcome.state) < 0) return null
  if (outcome.run_id === null || outcome.run_id === undefined) {
    if (outcome.state !== "refused" && outcome.state !== "running") return null
  } else if (!RUN_ID.test(outcome.run_id)) {
    return null
  }
  return outcome
}

function step(key, argv) {
  // Optional fields are left out when they hold their default, so there is less to copy.
  const request = { workflow: WORKFLOW, mode: args.mode, key: key, argv: argv }
  if (args.answers && args.answers[key]) request.answers = args.answers[key]
  if (args.retry && args.retry.indexOf(key) >= 0) request.retry = true
  if (args.restart && args.restart[key]) request.restart = args.restart[key]
  let calls = 0
  let misses = 0
  // The last outcome that said the run was still running, which the step resolves to at the cap.
  let last = null
  function once() {
    calls += 1
    // The request travels as an object: nothing is quoted for a shell.
    const argumentsText = JSON.stringify({ request: request, wait: WAIT_SECONDS })
    return agent(stepPrompt(argumentsText), {
      label: "step " + key + (calls > 1 ? " (" + calls + ")" : ""),
      schema: STEP_SCHEMA,
      model: "haiku",
      effort: "low",
    }).then(function (outcome) {
      const answer = checked(outcome, request)
      if (!answer) {
        misses += 1
        relayed[key] = outcome || null
        if (misses >= RELAYS) return null
        if (calls < MAX_CALLS) return once()
        delete relayed[key]
        return last
      }
      misses = 0
      delete relayed[key]
      // A retry asks for one new run: once an outcome names the step's run, asking again only
      // waits for it, and a rerun that failed between two calls is not started once more.
      if (answer.run_id) delete request.retry
      if (answer.state !== "running") return answer
      last = answer
      return calls < MAX_CALLS ? once() : answer
    })
  }
  return once()
}

function report(lost) {
  // The workflow and mode name the result of a workspace whose first step was lost before
  // anything was recorded.
  const command =
    CONCORDE + " workflow report --workflow " + quote(WORKFLOW) + " --mode " + quote(args.mode) +
    (lost ? " --lost " + quote(lost) : "")
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
    // The whole result is saved beside the workspace's workflow record; `concorde workflow
    // report` prints it again at any time.
    const result = { workflow: WORKFLOW, reported: value }
    // Unverified: what a step agent said, not what a host recorded, kept so that a refusal of
    // the step command (such as a mistyped request) is not lost from the error chain.
    if (lost && relayed[lost]) result.relayed = { key: lost, attempts: RELAYS, outcome: relayed[lost] }
    return result
  })
}

function note(text) {
  log(text)
}

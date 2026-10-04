// Runs a rendered Concorde workflow script under a stand-in for Claude Code's workflow runtime.
//
// Standard input: {"script": <path>, "args": {...},
//                  "outcomes": {<key>: <step outcome> | null}, "report": {status, summary}}
// A step whose key has no outcome gets null (its agent "returned nothing"). With
// "execute": {"cwd": <dir>, "concorde": <command>} every agent does what its prompt asks in that
// directory and returns what came back: a step agent's call of the project MCP server's
// `workflow_step` is played by the command that tool runs, `<concorde> workflow step --json
// <request> --wait <wait>`, run without a shell (`concorde` defaults to the script's
// args.concorde, then to .concorde/bin/concorde), and the report
// agent runs the command its prompt names, as it would with its Bash tool. Standard output:
// {"meta": <Claude meta>, "calls": [{"key", "request", "tool", "arguments" | "lost", "options",
//  "prompt"}], "notes": [...], "result": <what the script returned>, "error": <message or null>}.

import { spawnSync } from "node:child_process"
import { readFileSync } from "node:fs"

const input = JSON.parse(readFileSync(0, "utf-8"))
const source = readFileSync(input.script, "utf-8")
const calls = []
const notes = []
const served = {}

// The outcome for a step: a list gives one element per call, its last one from then on.
function next(key) {
  const outcome = input.outcomes[key]
  if (!Array.isArray(outcome)) return outcome
  const index = Math.min(served[key] || 0, outcome.length - 1)
  served[key] = (served[key] || 0) + 1
  return outcome[index]
}

// A step prompt names the tool on its first line and its arguments, as JSON, on its third.
function toolOf(text) {
  const match = text.split("\n")[0].match(/^Call the MCP tool (\S+) /)
  return match ? match[1] : null
}

function argumentsOf(text) {
  return JSON.parse(text.split("\n")[2])
}

function lostOf(text) {
  const match = text.match(/--lost '([^']*)'/)
  return match ? match[1] : null
}

// The command a relay prompt names: the line after "Run exactly this command ..." and a blank one.
function commandOf(text) {
  return text.split("\n")[2]
}

function parsed(done) {
  try {
    return JSON.parse(done.stdout)
  } catch (error) {
    return null
  }
}

// Runs the prompt's command through the shell and returns the JSON object it printed, or null.
function executed(prompt) {
  return parsed(
    spawnSync("/bin/sh", ["-c", commandOf(prompt)], { cwd: input.execute.cwd, encoding: "utf-8" })
  )
}

// Plays the step tool: runs the step command it runs, without a shell so that no path is split,
// and answers what that printed, or null.
function stepped(values) {
  const concorde = input.execute.concorde || (input.args && input.args.concorde) || ".concorde/bin/concorde"
  const argv = ["workflow", "step", "--json", JSON.stringify(values.request), "--wait", String(values.wait)]
  return parsed(spawnSync(concorde, argv, { cwd: input.execute.cwd, encoding: "utf-8" }))
}

const match = source.match(/^export const meta = (\{[\s\S]*?\n\})\n/)
if (!match) throw new Error("the Claude script does not start with an export const meta block")
const meta = JSON.parse(match[1])
const body = source.slice(match[0].length)

const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
let result = null
let error = null
try {
  const agent = function (prompt, options) {
    if (options.label === "report") {
      calls.push({ key: "report", lost: lostOf(prompt), options })
      if (!input.execute) return Promise.resolve(input.report)
      const value = executed(prompt)
      return Promise.resolve(value && { status: value.status, summary: value.summary })
    }
    const values = argumentsOf(prompt)
    const request = values.request
    calls.push({ key: request.key, request, tool: toolOf(prompt), arguments: values, options, prompt })
    if (input.execute) return Promise.resolve(stepped(values))
    const outcome = next(request.key)
    return Promise.resolve(outcome === undefined ? null : outcome)
  }
  const run = new AsyncFunction("agent", "log", "phase", "args", body)
  result = await run(agent, (text) => notes.push(text), () => {}, input.args)
} catch (caught) {
  error = String(caught && caught.message ? caught.message : caught)
}
process.stdout.write(JSON.stringify({ meta, calls, notes, result, error }))

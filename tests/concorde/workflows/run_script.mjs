// Runs a rendered Concorde workflow script under a stand-in for Claude Code's workflow runtime.
//
// Standard input: {"script": <path>, "args": {...},
//                  "outcomes": {<key>: <step outcome> | null}, "report": {status, summary}}
// A step whose key has no outcome gets null (its agent "returned nothing"). With
// "execute": {"cwd": <dir>} every agent runs the command its prompt names in that directory, as a
// step agent would with its Bash tool, and returns what it printed: the step outcome, or the
// status and summary of the report. Standard output:
// {"meta": <Claude meta>, "calls": [{"key", "request" | "lost", "options", "prompt"}],
//  "notes": [...], "result": <what the script returned>, "error": <message or null>}.

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

function requestOf(text) {
  const match = text.match(/--json '((?:[^']|'\\'')*)'/)
  return match ? JSON.parse(match[1].replace(/'\\''/g, "'")) : null
}

function lostOf(text) {
  const match = text.match(/--lost '([^']*)'/)
  return match ? match[1] : null
}

// The command a relay prompt names: the line after "Run exactly this command ..." and a blank one.
function commandOf(text) {
  return text.split("\n")[2]
}

// Runs the prompt's command through the shell and returns the JSON object it printed, or null.
function executed(prompt) {
  const done = spawnSync("/bin/sh", ["-c", commandOf(prompt)], {
    cwd: input.execute.cwd,
    encoding: "utf-8",
  })
  try {
    return JSON.parse(done.stdout)
  } catch (error) {
    return null
  }
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
    const request = requestOf(prompt)
    calls.push({ key: request.key, request, options, prompt })
    if (input.execute) return Promise.resolve(executed(prompt))
    const outcome = next(request.key)
    return Promise.resolve(outcome === undefined ? null : outcome)
  }
  const run = new AsyncFunction("agent", "log", "phase", "args", body)
  result = await run(agent, (text) => notes.push(text), () => {}, input.args)
} catch (caught) {
  error = String(caught && caught.message ? caught.message : caught)
}
process.stdout.write(JSON.stringify({ meta, calls, notes, result, error }))

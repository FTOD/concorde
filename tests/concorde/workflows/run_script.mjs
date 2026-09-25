// Runs a rendered Concorde workflow script under a stand-in for its client's runtime.
//
// Standard input: {"script": <path>, "client": "claude" | "pi", "args": {...},
//                  "outcomes": {<key>: <step outcome> | null}, "report": {status, summary}}
// A step whose key has no outcome gets null (its agent "returned nothing"). With
// "execute": {"command": <path of concorde>, "cwd": <dir>} a pi script's agents run the real
// commands, as its command-runner agents would: `workflow step --stdin` and `workflow report --stdin`. Standard output:
// {"meta": <Claude meta or null>, "calls": [{"key", "request" | "lost", "agent", "options"}],
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

let body = source
let meta = null
if (input.client === "claude") {
  const match = source.match(/^export const meta = (\{[\s\S]*?\n\})\n/)
  if (!match) throw new Error("the Claude script does not start with an export const meta block")
  meta = JSON.parse(match[1])
  body = source.slice(match[0].length)
}

const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
let result = null
let error = null
try {
  if (input.client === "claude") {
    const agent = function (prompt, options) {
      if (options.label === "report") {
        calls.push({ key: "report", lost: lostOf(prompt), options })
        return Promise.resolve(input.report)
      }
      const request = requestOf(prompt)
      calls.push({ key: request.key, request, options, prompt })
      const outcome = next(request.key)
      return Promise.resolve(outcome === undefined ? null : outcome)
    }
    const run = new AsyncFunction("agent", "log", "phase", "args", body)
    result = await run(agent, (text) => notes.push(text), () => {}, input.args)
  } else {
    const execute = input.execute
    const runs = {
      run(key, options) {
        const request = JSON.parse(options.task)
        if (execute) {
          const verb = options.agent === "concorde-report" ? "report" : "step"
          calls.push({ key: verb === "report" ? "report" : request.key, request, agent: options.agent })
          const done = spawnSync(execute.command, ["workflow", verb, "--stdin"], {
            cwd: execute.cwd, input: options.task, encoding: "utf-8",
          })
          return Promise.resolve({ ok: done.status === 0, output: done.stdout, stderr: done.stderr })
        }
        if (options.agent === "concorde-report") {
          calls.push({ key: "report", lost: request.lost[0] || null, agent: options.agent })
          return Promise.resolve({ ok: true, output: JSON.stringify(input.report) })
        }
        calls.push({ key: request.key, request, agent: options.agent })
        const outcome = next(request.key)
        if (outcome === undefined || outcome === null) return Promise.resolve({ ok: false, output: "" })
        return Promise.resolve({ ok: true, output: JSON.stringify(outcome) })
      },
    }
    const console_ = { log: (text) => notes.push(text) }
    const run = new AsyncFunction("runs", "console", "args", body)
    result = await run(runs, console_, input.args)
  }
} catch (caught) {
  error = String(caught && caught.message ? caught.message : caught)
}
process.stdout.write(JSON.stringify({ meta, calls, notes, result, error }))

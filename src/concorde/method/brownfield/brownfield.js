// The brownfield workflow: describe a project whose code came before its Specs, in one bound
// workspace (a task worktree).
//
// args: { module, mode: "interactive" | "no-ask", answers: { <base key>: [answer, ...] },
//         retry: [<base key>, ...] }
// The adapter defines step(key, argv), report(lost) and note(text), and the build the constants
// WORKFLOW and LAST_STEP ("delivery", as Method registers it). A step outcome is the
// contract.workflows.step value, or null when the step agent returned nothing; what a run hands
// this script is in the outcome's data, under the step output convention. Every stop ends with
// report(), which builds the result from what the hosts recorded.

if (!args.module) {
  throw new Error("the brownfield workflow needs args { module, mode }: the Module to describe")
}

const INTERACTIVE = args.mode === "interactive"

function ok(outcome) {
  return Boolean(outcome) && outcome.state === "finished" && outcome.status === "ok"
}

// A step its workflow record refused, or refused because its workspace was retired: the report
// cannot see it, so its refusal travels with the result.
function unrecorded(outcome) {
  return Boolean(outcome && outcome.error) &&
    ["step_rejected", "step_unrecorded", "workspace_retired"].includes(outcome.error.code)
}

// Whether the procedure must end here whatever the mode: nothing came back, the step is not
// recorded, or its run has not ended (a step agent gave up waiting).
function broken(outcome) {
  return !outcome || unrecorded(outcome) || outcome.state === "running"
}

// Whether an interactive run ends here, to have the step repaired or its decision points settled
// above the task.
function interactiveStop(outcome) {
  return INTERACTIVE && (!ok(outcome) || outcome.decision_points > 0)
}

function finish(outcome, key) {
  if (!outcome) return report(key)
  if (unrecorded(outcome)) {
    return report(key).then(function (value) {
      value.rejected = outcome
      return value
    })
  }
  return report(null)
}

// Providers before the Modules that use them (req.method.brownfield-providers-first): the uses
// among the created Modules condensed into strongly connected groups; each time, of the groups
// whose used groups are all placed, the one whose first Module the scaffold lists first, its
// Modules in the scaffold's order.
function providersFirst(created) {
  const index = {}
  created.forEach(function (item, i) { index[item.id] = i })
  const uses = created.map(function (item) {
    return (item.uses || [])
      .filter(function (target) { return target in index && target !== item.id })
      .map(function (target) { return index[target] })
  })
  // Tarjan's algorithm: group[v] numbers the strongly connected group of the v-th created Module.
  const group = []
  const seen = []
  const low = []
  const stack = []
  const onStack = []
  let counter = 0
  let groups = 0
  function visit(v) {
    seen[v] = low[v] = counter++
    stack.push(v)
    onStack[v] = true
    for (const w of uses[v]) {
      if (seen[w] === undefined) {
        visit(w)
        low[v] = Math.min(low[v], low[w])
      } else if (onStack[w]) {
        low[v] = Math.min(low[v], seen[w])
      }
    }
    if (low[v] === seen[v]) {
      let w
      do {
        w = stack.pop()
        onStack[w] = false
        group[w] = groups
      } while (w !== v)
      groups++
    }
  }
  created.forEach(function (_, v) { if (seen[v] === undefined) visit(v) })
  // The groups' members in the scaffold's order, and the other groups each one uses.
  const members = []
  const needs = []
  for (let g = 0; g < groups; g++) {
    members.push([])
    needs.push([])
  }
  created.forEach(function (_, v) {
    members[group[v]].push(v)
    for (const w of uses[v]) {
      if (group[w] !== group[v]) needs[group[v]].push(group[w])
    }
  })
  // The groups form no cycle, so some group whose providers are all placed is always left.
  const ordered = []
  const placed = []
  for (let n = 0; n < groups; n++) {
    let next = null
    for (let g = 0; g < groups; g++) {
      if (placed[g] || !needs[g].every(function (h) { return placed[h] })) continue
      if (next === null || members[g][0] < members[next][0]) next = g
    }
    placed[next] = true
    for (const v of members[next]) ordered.push(created[v].id)
  }
  return ordered
}

note("Surveying " + args.module)
const survey = await step("survey", ["survey", "--modules", args.module])
if (broken(survey) || !ok(survey) || interactiveStop(survey)) return await finish(survey, "survey")

note("Scaffolding the proposed Modules")
const scaffold = await step("scaffold", ["scaffold", "--input", survey.run_id])
if (broken(scaffold) || !ok(scaffold)) return await finish(scaffold, "scaffold")

// Scaffold hands the Modules it created, each with the uses among them (req.scaffold.step-output).
const described = providersFirst((scaffold.data || {}).created_modules || []).concat([args.module])
for (const id of described) {
  note("Describing " + id)
  const outcome = await step("describe:" + id, ["code_to_spec", "--modules", id])
  if (broken(outcome) || interactiveStop(outcome)) return await finish(outcome, "describe:" + id)
}

note("Reviewing the Specs")
const reviewed = await step("spec_review", ["spec_review", "--modules", described.join(",")])
if (broken(reviewed) || (INTERACTIVE && !ok(reviewed))) return await finish(reviewed, "spec_review")

note("Validating the workspace")
const validation = await step("validate", ["task-validation"])
// A validation that found the workspace not ready ends ok and declares itself blocking
// (req.validation.step-output).
if (broken(validation) || !ok(validation) || validation.blocking || (validation.data || {}).ready !== true) {
  return await finish(validation, "validate")
}

note("Delivering the workspace")
// An adoption describes existing code, so scenarios need no new verifying test to be delivered.
const delivery = await step(LAST_STEP, ["delivery", "--adoption"])
return await finish(delivery, LAST_STEP)

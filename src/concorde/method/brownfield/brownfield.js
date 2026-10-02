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

// Providers before the Modules that use them, otherwise in the scaffold's order.
function providersFirst(created) {
  const ordered = []
  const placed = {}
  let progress = true
  while (ordered.length < created.length && progress) {
    progress = false
    for (const item of created) {
      if (placed[item.id]) continue
      const ready = item.uses.every(function (target) { return placed[target] || target === item.id })
      if (ready) {
        ordered.push(item.id)
        placed[item.id] = true
        progress = true
      }
    }
  }
  for (const item of created) {
    if (!placed[item.id]) ordered.push(item.id)  // a cycle: keep the scaffold's order
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

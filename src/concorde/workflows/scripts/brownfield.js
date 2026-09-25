// The brownfield workflow: describe a project whose code came before its Specs, in one task.
//
// args: { task, module, mode: "interactive" | "no-ask", answers: { <base key>: [answer, ...] },
//         retry: [<base key>, ...] }
// The adapter defines step(key, argv), report(lost) and note(text). A step outcome is the
// contract.workflows.step value, or null when the step agent returned nothing. Every stop ends
// with report(), which builds the result from what the hosts recorded.

const INTERACTIVE = args.mode === "interactive"

function ok(outcome) {
  return Boolean(outcome) && outcome.state === "finished" && outcome.status === "ok"
}

// A step Tasks refused to record: the report cannot see it, so its refusal travels with the result.
function unrecorded(outcome) {
  return Boolean(outcome && outcome.error) &&
    (outcome.error.code === "step_rejected" || outcome.error.code === "step_unrecorded")
}

// Whether the procedure must end here whatever the mode: nothing came back, the step is not
// recorded, or its run has not ended (a step agent gave up waiting).
function broken(outcome) {
  return !outcome || unrecorded(outcome) || outcome.state === "running"
}

function needsDeveloper(outcome) {
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
if (broken(survey) || !ok(survey) || needsDeveloper(survey)) return await finish(survey, "survey")

note("Scaffolding the proposed Modules")
const scaffold = await step("scaffold", ["scaffold", "--input", survey.run_id])
if (broken(scaffold) || !ok(scaffold)) return await finish(scaffold, "scaffold")

const described = providersFirst(scaffold.created_modules).concat([args.module])
for (const id of described) {
  note("Describing " + id)
  const outcome = await step("describe:" + id, ["code_to_spec", "--modules", id])
  if (broken(outcome) || needsDeveloper(outcome)) return await finish(outcome, "describe:" + id)
}

note("Reviewing the Specs")
const reviewed = await step("spec_review", ["spec_review", "--modules", described.join(",")])
if (broken(reviewed) || (INTERACTIVE && !ok(reviewed))) return await finish(reviewed, "spec_review")

note("Validating the task")
const validation = await step("validate", ["validate"])
if (broken(validation) || !ok(validation) || validation.ready !== true) {
  return await finish(validation, "validate")
}

note("Delivering the task")
const delivery = await step("delivery", ["delivery"])
return await finish(delivery, "delivery")

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

function needsDeveloper(outcome) {
  return INTERACTIVE && (!ok(outcome) || outcome.decision_points > 0)
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
if (!survey) return await report("survey")
if (!ok(survey) || needsDeveloper(survey)) return await report(null)

note("Scaffolding the proposed Modules")
const scaffold = await step("scaffold", ["scaffold", "--input", survey.run_id])
if (!scaffold) return await report("scaffold")
if (!ok(scaffold)) return await report(null)

const described = providersFirst(scaffold.created_modules).concat([args.module])
for (const id of described) {
  note("Describing " + id)
  const outcome = await step("describe:" + id, ["code_to_spec", "--modules", id])
  if (!outcome) return await report("describe:" + id)
  if (needsDeveloper(outcome)) return await report(null)
}

note("Reviewing the Specs")
const reviewed = await step("spec_review", ["spec_review", "--modules", described.join(",")])
if (!reviewed) return await report("spec_review")
if (INTERACTIVE && !ok(reviewed)) return await report(null)

note("Validating the task")
const validation = await step("validate", ["validate"])
if (!validation) return await report("validate")
if (!ok(validation) || validation.ready !== true) return await report(null)

note("Delivering the task")
const delivery = await step("delivery", ["delivery"])
if (!delivery) return await report("delivery")
return await report(null)

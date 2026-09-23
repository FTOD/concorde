/** The one call of a solve workflow slot, built by the Host and by the workflow script alike. */
export function issueCall(layout, key) {
  if (!/^(d-[0-5]|v-[0-5]-[0-3]-[0-9]+)$/.test(key))
    throw new Error("Invalid issued Issue slot index");
  const decision = key.startsWith("d-");
  const group = decision ? 0 : Number(key.split("-")[2]);
  const role = decision
    ? "issue-solver"
    : group % 2 === 0
      ? "spec-reviewer"
      : "code-reviewer";
  const ticket = layout.ticket + ":" + key;
  const template = decision ? layout.stageSchema : layout.reviewSchema;
  const schema = {
    ...template,
    properties: { ...template.properties, invocation_id: { const: ticket } },
  };
  return {
    agent: "concorde-" + role,
    task: "Assess context.json for invocation_id " + ticket,
    cwd: layout.directory + "/slots/" + key + "/context",
    agentScope: "project",
    context: "fresh",
    async: false,
    mission: false,
    artifacts: true,
    artifactDir: "session",
    intercomBridge: { mode: "off" },
    agentContract: { version: 1 },
    outputSchema: schema,
    gate: { command: layout.slot_gate + " " + key },
  };
}

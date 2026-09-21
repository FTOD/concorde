/** Canonical portable call constructor: used by Host preflight and the native sandbox verbatim. */
export function issueCall(root, key) {
  if (!/^(d-[0-5]|v-[0-5]-[0-3]-[0-9]+)$/.test(key))
    throw new Error("Invalid issued Issue slot index");
  const decision = key.startsWith("d-");
  const group = decision ? 0 : Number(key.split("-")[2]);
  const role = decision
    ? "issue-solver"
    : group % 2 === 0
      ? "spec-reviewer"
      : "code-reviewer";
  const ticket = root.ticket + ":" + key;
  const template = decision ? root.stageSchema : root.reviewSchema;
  const schema = {
    ...template,
    properties: { ...template.properties, invocation_id: { const: ticket } },
  };
  return {
    agent: "concorde-" + role,
    task: "Assess context.json for invocation_id " + ticket,
    cwd: root.directory + "/slots/" + key + "/context",
    agentScope: "project",
    context: "fresh",
    async: false,
    mission: false,
    artifacts: true,
    artifactDir: "session",
    intercomBridge: { mode: "off" },
    agentContract: { version: 1 },
    outputSchema: schema,
    gate: { command: root.gatePrefix + " " + key },
  };
}

export function issueLayout(root, file, checksum) {
  const quote = (value) => "'" + value.replaceAll("'", "'\\''") + "'";
  return {
    ...root,
    gatePrefix: [
      root.python,
      root.package_root + "/scripts/run-operation.py",
      "--native-context",
      "issue-gate",
      file,
      checksum,
    ]
      .map(quote)
      .join(" "),
  };
}

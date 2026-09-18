import type { PluginModule } from "@docusaurus/types";
import type { CustomDocsExtension } from "../plugins/scoped-content/custom-docs";
import agentGraphs from "../concorde-only/plugin";

export default {
  // SAFETY: Docusaurus invokes this factory with LoadContext; its generic content
  // parameter is erased only at the heterogeneous plugin registration boundary.
  plugins: [agentGraphs as unknown as PluginModule],
  navbarItems: [
    { to: "/agent-graphs", label: "Agent Graphs", position: "left" },
  ],
} satisfies CustomDocsExtension;

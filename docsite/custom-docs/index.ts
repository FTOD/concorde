import type {PluginModule} from '@docusaurus/types';
import type {CustomDocsExtension} from '../plugins/scoped-content/custom-docs';
import agentFlows from '../concorde-only/plugin';

export default {
  plugins: [agentFlows as unknown as PluginModule],
  navbarItems: [{to: '/agent-flows', label: 'Agent Flows', position: 'left'}],
} satisfies CustomDocsExtension;

import {execFileSync} from 'node:child_process';
import {existsSync, readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import type {LoadContext, Plugin} from '@docusaurus/types';
import type {FlowData} from './types';

export default function agentFlows(context: LoadContext): Plugin<FlowData> {
  const root = resolve(context.siteDir, '..');
  const python = process.env.CONCORDE_PYTHON ?? (existsSync(resolve(root, '.venv/bin/python'))
    ? resolve(root, '.venv/bin/python') : 'python3');
  let loaded: FlowData;
  return {
    name: 'concorde-agent-flows',
    loadContent() {
      loaded = JSON.parse(execFileSync(python, [resolve(__dirname, 'flows.py')], {
        cwd: root, encoding: 'utf8', timeout: 30000,
      })) as FlowData;
      return loaded;
    },
    async contentLoaded({content, actions}) {
      const data = await actions.createData('flows.json', JSON.stringify(content));
      actions.addRoute({path: context.baseUrl + 'agent-flows', exact: true,
        component: resolve(__dirname, 'page.tsx'), modules: {data}});
    },
    getPathsToWatch() {
      return [resolve(__dirname, '**/*'), resolve(root, 'src/concorde/development/*.py'),
        resolve(root, 'src/concorde/harness/*.py'), resolve(root, 'src/concorde/reflections/*.py'), resolve(root, 'capabilities/*.py')];
    },
    postBuild() {
      for (const source of loaded.sources) {
        const digest = createHash('sha256').update(readFileSync(resolve(root, source.path))).digest('hex');
        if (digest !== source.digest) throw new Error(`Agent Flow source changed during publication: ${source.path}`);
      }
    },
  };
}

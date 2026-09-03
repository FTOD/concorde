import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const moduleHierarchy = JSON.parse(
  readFileSync(resolve(__dirname, '.generated/architecture-sidebar.json'), 'utf8'),
);

/** The declared module hierarchy is the whole Architecture navigation; the root module is its top level. */
const sidebars: SidebarsConfig = {architectureSidebar: moduleHierarchy};

export default sidebars;

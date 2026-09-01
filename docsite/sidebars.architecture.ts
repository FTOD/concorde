import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const moduleHierarchy = JSON.parse(
  readFileSync(resolve(__dirname, '.generated/architecture-sidebar.json'), 'utf8'),
);

const sidebars: SidebarsConfig = {
  architectureSidebar: [{
    type: 'category', label: 'Architecture',
    link: {type: 'generated-index', slug: '/', description: 'Module architecture landing pages and their owned views.'},
    items: moduleHierarchy,
  }],
};

export default sidebars;

import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const moduleFeatureHierarchy = JSON.parse(
  readFileSync(resolve(__dirname, '.generated/features-sidebar.json'), 'utf8'),
);

const sidebars: SidebarsConfig = {
  featuresSidebar: [{
    type: 'category',
    label: 'Features',
    link: {type: 'generated-index', slug: '/', description: 'Direct feature files grouped by their owning module hierarchy.'},
    items: moduleFeatureHierarchy,
  }],
};
export default sidebars;

import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const moduleFeatureHierarchy = JSON.parse(
  readFileSync(resolve(__dirname, '.generated/features-sidebar.json'), 'utf8'),
);

/** The module hierarchy of direct features is the whole Features navigation; the root module is its top level. */
const sidebars: SidebarsConfig = {featuresSidebar: moduleFeatureHierarchy};
export default sidebars;

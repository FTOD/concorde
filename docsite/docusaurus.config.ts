import {resolve} from 'node:path';

import type {Config, PluginModule} from '@docusaurus/types';
import type {Options as ClassicOptions} from '@docusaurus/preset-classic';

import concordeContent from './plugins/concorde-content';
import {remarkConcordeLinks} from './plugins/concorde-content/links';
import {buildRegistry} from './plugins/concorde-content/registry';

const projectRoot = resolve(__dirname, '..');
const linkPlugin = [remarkConcordeLinks, {projectRoot, getRegistry: () => buildRegistry(projectRoot)}] as const;

const config: Config = {
  title: 'Concorde',
  tagline: 'Architecture-aware specification workflows',
  favicon: 'img/favicon.svg',
  url: 'https://concorde.dev',
  baseUrl: '/',
  organizationName: 'concorde',
  projectName: 'concorde',
  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',
  markdown: {hooks: {onBrokenMarkdownLinks: 'throw'}},
  trailingSlash: false,
  staticDirectories: ['static', '../generated'],
  presets: [[
    'classic',
    {
      docs: {
        path: '../docs', routeBasePath: 'docs', sidebarPath: './sidebars.docs.ts', include: ['**/*.md'],
        showLastUpdateAuthor: false, showLastUpdateTime: false, numberPrefixParser: false,
        beforeDefaultRemarkPlugins: [linkPlugin],
      },
      blog: false,
      theme: {customCss: './src/css/custom.css'},
      sitemap: false,
    } satisfies ClassicOptions,
  ]],
  plugins: [
    [concordeContent as unknown as PluginModule, {projectRoot}],
    ['@docusaurus/plugin-content-docs', {
      id: 'architecture', path: '../architecture', routeBasePath: 'architecture', sidebarPath: './sidebars.architecture.ts',
      include: ['**/*.md'], showLastUpdateAuthor: false, showLastUpdateTime: false,
      numberPrefixParser: false, beforeDefaultRemarkPlugins: [linkPlugin],
    }],
    ['@docusaurus/plugin-content-docs', {
      id: 'features', path: '../specs', routeBasePath: 'features', sidebarPath: './sidebars.features.ts',
      include: ['**/spec.md'], showLastUpdateAuthor: false, showLastUpdateTime: false,
      numberPrefixParser: false, beforeDefaultRemarkPlugins: [linkPlugin],
    }],
    ['@easyops-cn/docusaurus-search-local', {
      hashed: true, indexDocs: true, indexBlog: false, docsRouteBasePath: ['/architecture', '/docs', '/features'],
      docsDir: ['../architecture', '../docs', '../specs'],
    }],
  ],
  themeConfig: {
    navbar: {
      title: 'Concorde',
      items: [
        {type: 'docSidebar', sidebarId: 'architectureSidebar', docsPluginId: 'architecture', label: 'Architecture', position: 'left'},
        {type: 'docSidebar', sidebarId: 'docsSidebar', label: 'Documentation', position: 'left'},
        {type: 'docSidebar', sidebarId: 'featuresSidebar', docsPluginId: 'features', label: 'Features', position: 'left'},
      ],
    },
    footer: {style: 'dark', copyright: `Concorde project documentation · ${new Date().getUTCFullYear()}`},
    colorMode: {respectPrefersColorScheme: true},
  },
};

export default config;

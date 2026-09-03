import {resolve} from 'node:path';

import type {Config, PluginModule} from '@docusaurus/types';
import type {Options as ClassicOptions} from '@docusaurus/preset-classic';

import concordeContent from './plugins/concorde-content';
import {remarkConcordeLinks} from './plugins/concorde-content/links';
import {buildRegistry} from './plugins/concorde-content/registry';

const projectRoot = resolve(__dirname, '..');
const canonicalLinks = {projectRoot, getRegistry: () => buildRegistry(projectRoot)};
const linkPlugin = [remarkConcordeLinks, canonicalLinks] as const;
const architectureLinkPlugin = [remarkConcordeLinks, {
  ...canonicalLinks, stagedRoot: resolve(__dirname, '.generated/content/architecture'), canonicalSourceBase: 'specs',
}] as const;
const featureLinkPlugin = [remarkConcordeLinks, {
  ...canonicalLinks, stagedRoot: resolve(__dirname, '.generated/content/features'), canonicalSourceBase: 'specs',
}] as const;
const homeLinkPlugin = [remarkConcordeLinks, {
  ...canonicalLinks, stagedRoot: resolve(__dirname, '.generated/content/home'), canonicalCollectionId: 'home',
}] as const;

const config: Config = {
  title: 'Concorde',
  tagline: 'Architecture-aware specification workflows',
  favicon: 'img/favicon.svg',
  url: 'https://ftod.github.io',
  baseUrl: '/concorde/',
  organizationName: 'FTOD',
  projectName: 'concorde',
  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',
  markdown: {hooks: {onBrokenMarkdownLinks: 'throw'}},
  trailingSlash: false,
  staticDirectories: ['static', '.generated/static', '../generated'],
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
      id: 'home', path: '.generated/content/home', routeBasePath: '/', sidebarPath: false,
      include: ['README.md'], showLastUpdateAuthor: false, showLastUpdateTime: false,
      numberPrefixParser: false, beforeDefaultRemarkPlugins: [homeLinkPlugin],
    }],
    ['@docusaurus/plugin-content-docs', {
      id: 'architecture', path: '.generated/content/architecture', routeBasePath: 'architecture', sidebarPath: './sidebars.architecture.ts',
      include: ['**/*.md'], showLastUpdateAuthor: false, showLastUpdateTime: false,
      numberPrefixParser: false, beforeDefaultRemarkPlugins: [architectureLinkPlugin],
    }],
    ['@docusaurus/plugin-content-docs', {
      id: 'features', path: '.generated/content/features', routeBasePath: 'features', sidebarPath: './sidebars.features.ts',
      include: ['**/*.md'], showLastUpdateAuthor: false, showLastUpdateTime: false,
      numberPrefixParser: false, beforeDefaultRemarkPlugins: [featureLinkPlugin],
    }],
    ['@easyops-cn/docusaurus-search-local', {
      hashed: true, indexDocs: true, indexBlog: false, docsRouteBasePath: ['/', '/architecture', '/docs', '/features'],
      docsDir: ['.generated/content/home', '.generated/content/architecture', '../docs', '.generated/content/features'],
    }],
  ],
  themeConfig: {
    navbar: {
      title: 'Concorde',
      items: [
        {type: 'docSidebar', sidebarId: 'featuresSidebar', docsPluginId: 'features', label: 'Features', position: 'left'},
        {type: 'docSidebar', sidebarId: 'docsSidebar', label: 'Documentation', position: 'left'},
        {type: 'docSidebar', sidebarId: 'architectureSidebar', docsPluginId: 'architecture', label: 'Architecture', position: 'left'},
        {href: 'https://github.com/FTOD/concorde', position: 'right', className: 'header-github-link', 'aria-label': 'GitHub repository'},
      ],
    },
    footer: {style: 'dark', copyright: `Concorde project documentation · ${new Date().getUTCFullYear()}`},
    colorMode: {respectPrefersColorScheme: true},
  },
};

export default config;

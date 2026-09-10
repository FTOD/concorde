import {resolve} from 'node:path';

import type {Config, PluginModule} from '@docusaurus/types';
import type {Options as ClassicOptions} from '@docusaurus/preset-classic';

import scopedContent from './plugins/scoped-content';
import {requireScoped} from './plugins/scoped-content/model';
import {loadSiteIdentity} from './plugins/scoped-content/site-identity';

const projectRoot = resolve(__dirname, '..');
const identity = loadSiteIdentity(__dirname);
const hasProtocolDocs = identity.protocolDocs === true;
requireScoped(projectRoot);
const repositoryHost = identity.repository ? new URL(identity.repository).hostname : undefined;
const config: Config = {
  title: identity.title,
  tagline: identity.tagline ?? 'Project documentation',
  favicon: 'img/favicon.svg',
  url: identity.url,
  baseUrl: identity.baseUrl,
  organizationName: identity.organizationName,
  projectName: identity.projectName,
  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',
  markdown: {format: 'md', mermaid: true, hooks: {onBrokenMarkdownLinks: 'throw'}},
  themes: ['@docusaurus/theme-mermaid'],
  trailingSlash: false,
  staticDirectories: ['static'],
  presets: [[
    'classic',
    {
      docs: {
        path: '.generated/content/specs', routeBasePath: 'specs', sidebarPath: './sidebars.specs.ts',
        include: ['**/*.md'], numberPrefixParser: false, showLastUpdateAuthor: false, showLastUpdateTime: false,
      },
      blog: false,
      theme: {customCss: './src/css/custom.css'},
      sitemap: false,
    } satisfies ClassicOptions,
  ]],
  plugins: [
    [scopedContent as unknown as PluginModule, {projectRoot}],
    ...(hasProtocolDocs ? [
      ['@docusaurus/plugin-content-docs', {
        id: 'protocol', path: '../protocol', routeBasePath: 'protocol', sidebarPath: './sidebars.protocol.ts',
        include: ['**/*.md'], numberPrefixParser: false,
        showLastUpdateAuthor: false, showLastUpdateTime: false,
      }],
    ] : []),
    ['@easyops-cn/docusaurus-search-local', {
      hashed: true, indexDocs: true, indexBlog: false,
      docsRouteBasePath: ['/specs', ...(hasProtocolDocs ? ['/protocol'] : [])],
      docsDir: ['.generated/content/specs', ...(hasProtocolDocs ? ['../protocol'] : [])],
    }],
  ],
  themeConfig: {
    navbar: {
      title: identity.title,
      items: [
        ...(hasProtocolDocs ? [
          {type: 'docSidebar', sidebarId: 'protocolSidebar', docsPluginId: 'protocol', label: 'Spec Protocol', position: 'left'},
        ] : []),
        {type: 'docSidebar', sidebarId: 'moduleSpecsSidebar', label: 'Module Specs', position: 'left'},
        {to: '/graph', label: 'Graph', position: 'left'},
        ...(identity.repository ? [
          repositoryHost === 'github.com'
            ? {href: identity.repository, position: 'right', className: 'header-github-link', 'aria-label': 'GitHub repository'}
            : {href: identity.repository, label: 'Source', position: 'right'},
        ] : []),
      ],
    },
    footer: {style: 'dark', copyright: `${identity.title} project documentation · ${new Date().getUTCFullYear()}`},
    colorMode: {respectPrefersColorScheme: true},
  },
};

export default config;

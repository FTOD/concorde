import {readdirSync} from 'node:fs';
import {resolve} from 'node:path';

import type {Config, PluginModule} from '@docusaurus/types';
import type {Options as ClassicOptions} from '@docusaurus/preset-classic';

import concordeContent from './plugins/concorde-content';
import scopedContent from './plugins/scoped-content';
import {isScoped} from './plugins/scoped-content/model';
import {remarkConcordeLinks} from './plugins/concorde-content/links';
import {buildRegistry} from './plugins/concorde-content/registry';
import {loadSiteIdentity} from './plugins/concorde-content/site-identity';

/** Whether at least one file was staged into a generated content directory by `materializeContent`. */
function hasStagedContent(generatedContentDirectory: string): boolean {
  try {
    return readdirSync(resolve(__dirname, generatedContentDirectory)).length > 0;
  } catch {
    return false;
  }
}

const projectRoot = resolve(__dirname, '..');
const identity = loadSiteIdentity(__dirname);
const scoped = isScoped(projectRoot);
// Docusaurus refuses to load a content-docs plugin instance with zero staged documents; a project
// scaffolded from Initialization Proposal 3 output alone has a root module but no features yet.
const hasFeatures = !scoped && hasStagedContent('.generated/content/features');
const repositoryHost = identity.repository ? new URL(identity.repository).hostname : undefined;
const canonicalLinks = {projectRoot, getRegistry: () => buildRegistry(projectRoot)};
const architectureLinkPlugin = [remarkConcordeLinks, {
  ...canonicalLinks, stagedRoot: resolve(__dirname, '.generated/content/architecture'), canonicalSourceBase: 'specs',
}] as const;
const featureLinkPlugin = [remarkConcordeLinks, {
  ...canonicalLinks, stagedRoot: resolve(__dirname, '.generated/content/features'), canonicalSourceBase: 'specs',
}] as const;
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
  markdown: {format: scoped ? 'md' : 'mdx', hooks: {onBrokenMarkdownLinks: 'throw'}},
  trailingSlash: false,
  staticDirectories: ['static', ...(!scoped || hasStagedContent('.generated/static/diagrams') ? ['.generated/static'] : []), ...(!scoped ? ['../generated'] : [])],
  presets: [[
    'classic',
    {
      docs: scoped ? {
        path: '.generated/content/specs', routeBasePath: 'specs', sidebarPath: './sidebars.specs.ts',
        include: ['**/*.md'], numberPrefixParser: false, showLastUpdateAuthor: false, showLastUpdateTime: false,
      } : {
        path: '.generated/content/architecture', routeBasePath: 'architecture', sidebarPath: './sidebars.architecture.ts',
        include: ['**/*.md'], showLastUpdateAuthor: false, showLastUpdateTime: false,
        numberPrefixParser: false, beforeDefaultRemarkPlugins: [architectureLinkPlugin],
      },
      blog: false,
      theme: {customCss: './src/css/custom.css'},
      sitemap: false,
    } satisfies ClassicOptions,
  ]],
  plugins: [
    [(scoped ? scopedContent : concordeContent) as unknown as PluginModule, {projectRoot}],
    ...(hasFeatures ? [
      ['@docusaurus/plugin-content-docs', {
        id: 'features', path: '.generated/content/features', routeBasePath: 'features', sidebarPath: './sidebars.features.ts',
        include: ['**/*.md'], showLastUpdateAuthor: false, showLastUpdateTime: false,
        numberPrefixParser: false, beforeDefaultRemarkPlugins: [featureLinkPlugin],
      }],
    ] : []),
    ['@easyops-cn/docusaurus-search-local', {
      hashed: true, indexDocs: true, indexBlog: false,
      docsRouteBasePath: [scoped ? '/specs' : '/architecture', ...(hasFeatures ? ['/features'] : [])],
      docsDir: [
        scoped ? '.generated/content/specs' : '.generated/content/architecture',
        ...(hasFeatures ? ['.generated/content/features'] : []),
      ],
    }],
  ],
  themeConfig: {
    navbar: {
      title: identity.title,
      items: [
        {type: 'docSidebar', sidebarId: scoped ? 'specsSidebar' : 'architectureSidebar', label: scoped ? 'Specs' : 'Architecture', position: 'left'},
        ...(hasFeatures ? [
          {type: 'docSidebar', sidebarId: 'featuresSidebar', docsPluginId: 'features', label: 'Features', position: 'left'},
        ] : []),
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

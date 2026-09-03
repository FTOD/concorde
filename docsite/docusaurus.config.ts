import {existsSync, readdirSync} from 'node:fs';
import {resolve} from 'node:path';

import type {Config, PluginModule} from '@docusaurus/types';
import type {Options as ClassicOptions} from '@docusaurus/preset-classic';

import concordeContent from './plugins/concorde-content';
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
const hasDocs = existsSync(resolve(projectRoot, 'docs'));
// Docusaurus refuses to load a content-docs plugin instance with zero staged documents; a project
// scaffolded from Initialization Proposal 3 output alone has a root module but no features yet.
const hasFeatures = hasStagedContent('.generated/content/features');
const repositoryHost = identity.repository ? new URL(identity.repository).hostname : undefined;
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
  title: identity.title,
  tagline: identity.tagline ?? 'Project documentation',
  favicon: 'img/favicon.svg',
  url: identity.url,
  baseUrl: identity.baseUrl,
  organizationName: identity.organizationName,
  projectName: identity.projectName,
  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',
  markdown: {hooks: {onBrokenMarkdownLinks: 'throw'}},
  trailingSlash: false,
  staticDirectories: ['static', '.generated/static', '../generated'],
  presets: [[
    'classic',
    {
      docs: hasDocs ? {
        path: '../docs', routeBasePath: 'docs', sidebarPath: './sidebars.docs.ts', include: ['**/*.md'],
        showLastUpdateAuthor: false, showLastUpdateTime: false, numberPrefixParser: false,
        beforeDefaultRemarkPlugins: [linkPlugin],
      } : false,
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
    ...(hasFeatures ? [
      ['@docusaurus/plugin-content-docs', {
        id: 'features', path: '.generated/content/features', routeBasePath: 'features', sidebarPath: './sidebars.features.ts',
        include: ['**/*.md'], showLastUpdateAuthor: false, showLastUpdateTime: false,
        numberPrefixParser: false, beforeDefaultRemarkPlugins: [featureLinkPlugin],
      }],
    ] : []),
    ['@easyops-cn/docusaurus-search-local', {
      hashed: true, indexDocs: true, indexBlog: false,
      docsRouteBasePath: ['/', '/architecture', ...(hasFeatures ? ['/features'] : []), ...(hasDocs ? ['/docs'] : [])],
      docsDir: [
        '.generated/content/home', '.generated/content/architecture',
        ...(hasFeatures ? ['.generated/content/features'] : []), ...(hasDocs ? ['../docs'] : []),
      ],
    }],
  ],
  themeConfig: {
    navbar: {
      title: identity.title,
      items: [
        ...(hasFeatures ? [
          {type: 'docSidebar', sidebarId: 'featuresSidebar', docsPluginId: 'features', label: 'Features', position: 'left'},
        ] : []),
        ...(hasDocs ? [
          {type: 'docSidebar', sidebarId: 'docsSidebar', label: 'Documentation', position: 'left'},
        ] : []),
        {type: 'docSidebar', sidebarId: 'architectureSidebar', docsPluginId: 'architecture', label: 'Architecture', position: 'left'},
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

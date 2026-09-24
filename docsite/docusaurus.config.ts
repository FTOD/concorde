import { resolve } from "node:path";

import type { Config, PluginModule } from "@docusaurus/types";
import type { Options as ClassicOptions } from "@docusaurus/preset-classic";

import { customDocsConfiguration } from "./plugins/scoped-content/custom-docs";
import { userDocsConfiguration } from "./plugins/scoped-content/user-docs";

import generatedCache from "./plugins/generated-cache";
import scopedContent from "./plugins/scoped-content";
import {
  loadScopedRegistry,
  requireScoped,
} from "./plugins/scoped-content/model";
import { loadSiteIdentity } from "./plugins/scoped-content/site-identity";

const projectRoot = resolve(__dirname, "..");
const identity = loadSiteIdentity(__dirname);
const registry = loadScopedRegistry(projectRoot);
const user = userDocsConfiguration(__dirname, identity, registry);
const custom = customDocsConfiguration(__dirname, identity, registry);
requireScoped(projectRoot);
let repositoryHost: string | undefined;
try {
  repositoryHost = identity.repository
    ? new URL(identity.repository).hostname
    : undefined;
} catch {
  throw new Error(
    "docsite/site.json is invalid: repository must be a valid URL.",
  );
}
const config: Config = {
  title: identity.title,
  tagline: identity.tagline ?? "Project documentation",
  favicon: "img/favicon.svg",
  url: identity.url,
  baseUrl: identity.baseUrl,
  organizationName: identity.organizationName,
  projectName: identity.projectName,
  onBrokenLinks: "throw",
  onDuplicateRoutes: "throw",
  onBrokenAnchors: "throw",
  markdown: {
    format: "detect",
    hooks: { onBrokenMarkdownLinks: "throw" },
  },
  trailingSlash: false,
  staticDirectories: ["static"],
  presets: [
    [
      "classic",
      {
        docs: {
          path: ".generated/content/specs",
          routeBasePath: "specs",
          sidebarPath: "./sidebars.specs.ts",
          include: ["**/*.md"],
          numberPrefixParser: false,
          showLastUpdateAuthor: false,
          showLastUpdateTime: false,
        },
        blog: false,
        // With user documents their root page is the home page, so the redirect page steps aside.
        pages: user
          ? {
              exclude: [
                "**/_*.{js,jsx,ts,tsx,md,mdx}",
                "**/_*/**",
                "**/*.test.{js,jsx,ts,tsx}",
                "**/__tests__/**",
                "index.tsx",
              ],
            }
          : {},
        theme: { customCss: "./src/css/custom.css" },
        sitemap: false,
      } satisfies ClassicOptions,
    ],
  ],
  plugins: [
    generatedCache,
    ...(user ? [user.plugin] : []),
    ...custom.plugins,
    [scopedContent as PluginModule, { projectRoot }],
    [
      "@easyops-cn/docusaurus-search-local",
      {
        hashed: true,
        indexDocs: true,
        indexBlog: false,
        // The user documents' route "/" contains every other one, so it is matched last.
        docsRouteBasePath: [
          "/specs",
          ...custom.docsRouteBasePath,
          ...(user ? [user.docsRouteBasePath] : []),
        ],
        docsDir: [
          ".generated/content/specs",
          ...custom.docsDir,
          ...(user ? [user.docsDir] : []),
        ],
      },
    ],
  ],
  themeConfig: {
    navbar: {
      title: identity.title,
      // User documents come first, then the Spec tabs, then project-owned custom docs.
      items: [
        ...(user ? [user.navbarItem] : []),
        {
          type: "docSidebar",
          sidebarId: "moduleDocumentsSidebar",
          label: "Module documents",
          position: "left",
        },
        ...(registry.pages.some(
          (page) => page.readingCollection === "implementation",
        )
          ? [
              {
                type: "docSidebar" as const,
                sidebarId: "implementationDocumentsSidebar",
                label: "Implementation documents",
                position: "left" as const,
              },
            ]
          : []),
        ...custom.navbarItems,
        ...(identity.repository
          ? [
              repositoryHost === "github.com"
                ? {
                    href: identity.repository,
                    position: "right",
                    className: "header-github-link",
                    "aria-label": "GitHub repository",
                  }
                : {
                    href: identity.repository,
                    label: "Source",
                    position: "right",
                  },
            ]
          : []),
      ],
    },
    footer: {
      style: "dark",
      copyright: `${identity.title} project documentation · ${new Date().getUTCFullYear()}`,
    },
    colorMode: { respectPrefersColorScheme: true },
  },
};

export default config;

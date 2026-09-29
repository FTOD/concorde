import { useLocation } from "@docusaurus/router";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { usePluginData } from "@docusaurus/useGlobalData";

import type { Page } from "../../plugins/scoped-content/model";
import {
  canonicalRoute,
  normalizeRoute,
} from "../../plugins/scoped-content/routes";

interface GlobalData {
  pages: Page[];
}

/** The registered Spec page at the current route, if any, with every published page. */
export default function useScopedPage(): { page?: Page; pages: Page[] } {
  const location = useLocation();
  const baseUrl = useBaseUrl("/");
  // SAFETY: concorde-content publishes the validated Page index through setGlobalData.
  const data = usePluginData("concorde-content") as unknown as GlobalData;
  const pathname = canonicalRoute(location.pathname, baseUrl);
  const page = data.pages.find(
    (candidate) => normalizeRoute(candidate.route) === normalizeRoute(pathname),
  );
  return { page, pages: data.pages };
}

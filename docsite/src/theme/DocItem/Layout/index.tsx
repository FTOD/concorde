import type {WrapperProps} from '@docusaurus/types';
import {useLocation} from '@docusaurus/router';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {usePluginData} from '@docusaurus/useGlobalData';
import OriginalLayout from '@theme-original/DocItem/Layout';
import type OriginalLayoutType from '@theme/DocItem/Layout';

import type {Page} from '../../../../plugins/scoped-content/model';
import {canonicalRoute, normalizeRoute} from '../../../../plugins/scoped-content/routes';
import ContentProvenance from '../../../components/ContentProvenance';

type Props = WrapperProps<typeof OriginalLayoutType>;
interface GlobalData {pages: Page[]}

export default function LayoutWrapper(props: Props) {
  const location = useLocation();
  const baseUrl = useBaseUrl('/');
  const data = usePluginData('concorde-content') as unknown as GlobalData;
  const pathname = canonicalRoute(location.pathname, baseUrl);
  const page = data.pages.find((candidate) => normalizeRoute(candidate.route) === normalizeRoute(pathname));
  return <>
    {page && <div className="provenanceShell"><ContentProvenance page={page} /></div>}
    <OriginalLayout {...props} />
  </>;
}

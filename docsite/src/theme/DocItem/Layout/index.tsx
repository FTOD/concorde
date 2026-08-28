import React from 'react';
import {useLocation} from '@docusaurus/router';
import type {WrapperProps} from '@docusaurus/types';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {usePluginData} from '@docusaurus/useGlobalData';
import OriginalLayout from '@theme-original/DocItem/Layout';
import type OriginalLayoutType from '@theme/DocItem/Layout';

import type {ContentPage} from '../../../../plugins/concorde-content/types';
import {canonicalRoute, normalizeRoute} from '../../../../plugins/concorde-content/routes';
import ArchitectureView from '../../../components/ArchitectureView';
import CompanionLinks from '../../../components/CompanionLinks';
import ContentProvenance from '../../../components/ContentProvenance';
import FeatureDiagrams from '../../../components/FeatureDiagrams';
import FeatureRelations from '../../../components/FeatureRelations';

type Props = WrapperProps<typeof OriginalLayoutType>;
interface GlobalData {pages: ContentPage[]}

export default function LayoutWrapper(props: Props) {
  const location = useLocation();
  const baseUrl = useBaseUrl('/');
  const data = usePluginData('concorde-content') as unknown as GlobalData;
  const pathname = canonicalRoute(location.pathname, baseUrl);
  const page = data.pages.find((candidate) => normalizeRoute(candidate.route) === normalizeRoute(pathname));
  return <>
    {page && <div className="provenanceShell"><ContentProvenance page={page} /></div>}
    {page && <div className="companionLinksShell"><CompanionLinks page={page} /></div>}
    {page && <div className="featureRelationsShell"><FeatureRelations page={page} /></div>}
    {page?.architectureViewRoute && <div className="architectureViewShell"><ArchitectureView page={page} /></div>}
    {page?.diagrams?.length ? <div className="featureDiagramsShell"><FeatureDiagrams page={page} /></div> : null}
    <OriginalLayout {...props} />
  </>;
}

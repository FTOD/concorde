import React from 'react';
import {useLocation} from '@docusaurus/router';
import type {WrapperProps} from '@docusaurus/types';
import {usePluginData} from '@docusaurus/useGlobalData';
import OriginalLayout from '@theme-original/DocItem/Layout';
import type OriginalLayoutType from '@theme/DocItem/Layout';

import type {ContentPage} from '../../../../plugins/concorde-content/types';
import ArchitectureView from '../../../components/ArchitectureView';
import ContentProvenance from '../../../components/ContentProvenance';

type Props = WrapperProps<typeof OriginalLayoutType>;
interface GlobalData {pages: ContentPage[]}
const normalize = (route: string) => route === '/' ? route : route.replace(/\/$/, '');

export default function LayoutWrapper(props: Props) {
  const location = useLocation();
  const data = usePluginData('concorde-content') as unknown as GlobalData;
  const page = data.pages.find((candidate) => normalize(candidate.route) === normalize(location.pathname));
  return <>
    {page && <div className="provenanceShell"><ContentProvenance page={page} /></div>}
    {page?.architectureViewRoute && <div className="architectureViewShell"><ArchitectureView page={page} /></div>}
    <OriginalLayout {...props} />
  </>;
}

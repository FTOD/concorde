import type {ComponentProps} from 'react';
import {useLocation} from '@docusaurus/router';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {usePluginData} from '@docusaurus/useGlobalData';
import OriginalComponents from '@theme-original/MDXComponents';
import MDXHeading from '@theme/MDXComponents/Heading';

import type {ContentPage} from '../../../plugins/concorde-content/types';
import {canonicalRoute,normalizeRoute} from '../../../plugins/concorde-content/routes';
import ArchitectureView from '../../components/ArchitectureView';

/** A registered overview belongs in the main Spec's authored architecture section. */
function DomainSectionHeading(props:ComponentProps<'h2'>) {
  const location=useLocation();const base=useBaseUrl('/');
  const data=usePluginData('concorde-content') as {pages:(ContentPage&{inlineOverview?:boolean})[]}|undefined;
  const route=canonicalRoute(location.pathname,base);
  const page=data?.pages.find(p=>normalizeRoute(p.route)===normalizeRoute(route));
  return <>
    <MDXHeading as="h2" {...props}/>
    {props.id==='architecture-overview'&&page?.inlineOverview&&page.architectureDiagrams?.length
      ?<ArchitectureView page={page} showHeading={false}/>:null}
  </>;
}

export default {...OriginalComponents,h2:DomainSectionHeading};

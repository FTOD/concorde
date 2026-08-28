import Link from '@docusaurus/Link';

import type {ContentPage} from '../../plugins/concorde-content/types';

interface Companion {label: string; description: string; route: string}

/** The single companion page that pairs with this one: module summary <-> design reference, specification <-> accepted realization. */
export function companionFor(page: ContentPage): Companion | undefined {
  if (page.kind === 'architecture-source' && page.architectureKind === 'module' && page.designReferenceRoute) {
    return {
      label: 'Design reference', route: page.designReferenceRoute,
      description: 'Implementation notes, rationale, alternatives, and decisions recorded for this module.',
    };
  }
  if (page.kind === 'module-design' && page.moduleRoute) {
    return {label: 'Module summary', route: page.moduleRoute, description: 'The bounded level page this reference elaborates.'};
  }
  if (page.kind === 'feature-specification' && page.implementationRoute) {
    return {label: 'Accepted realization', route: page.implementationRoute, description: 'The hardened implementation of this specification.'};
  }
  if (page.kind === 'feature-implementation' && page.specificationRoute) {
    return {label: 'Specification', route: page.specificationRoute, description: 'The durable behavior this realization implements.'};
  }
  return undefined;
}

export default function CompanionLinks({page}: {page: ContentPage}) {
  const companion = companionFor(page);
  if (!companion) return null;
  return (
    <nav className="companionLinks" aria-label="Companion page">
      <span className="companionLinks__eyebrow">Companion page</span>
      <Link className="companionLinks__link" to={companion.route}>{companion.label}</Link>
      <span className="companionLinks__description">{companion.description}</span>
    </nav>
  );
}

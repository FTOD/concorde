import Link from '@docusaurus/Link';

import type {ContentPage} from '../../plugins/concorde-content/types';

/** A page that pairs with the current one; `route` is absent when the entry is the current page itself. */
interface Companion {label: string; description: string; route?: string}

const featureKinds = new Set<ContentPage['kind']>(['feature-tldr', 'feature-specification', 'feature-design']);

/**
 * The pages that pair with this one: module summary <-> design reference, or the three pages of one feature root
 * (TL;DR · Specification · Design reference) with the current page listed but not linked.
 */
export function companionsFor(page: ContentPage): Companion[] {
  if (page.kind === 'architecture-source' && page.architectureKind === 'module' && page.designReferenceRoute) {
    return [{
      label: 'Design reference', route: page.designReferenceRoute,
      description: 'Implementation notes, rationale, alternatives, and decisions recorded for this module.',
    }];
  }
  if (page.kind === 'module-design' && page.moduleRoute) {
    return [{label: 'Module summary', route: page.moduleRoute, description: 'The bounded level page this reference elaborates.'}];
  }
  if (featureKinds.has(page.kind)) {
    return [
      {
        label: 'TL;DR', route: page.kind === 'feature-tldr' ? undefined : page.tldrRoute,
        description: 'The self-contained quick understanding of this feature.',
      },
      {
        label: 'Specification', route: page.kind === 'feature-specification' ? undefined : page.specificationRoute,
        description: 'The durable behavior, requirements, and success criteria.',
      },
      {
        label: 'Design reference', route: page.kind === 'feature-design' ? undefined : page.designRoute,
        description: 'The accepted design that realizes this feature.',
      },
    ];
  }
  return [];
}

export default function CompanionLinks({page}: {page: ContentPage}) {
  const companions = companionsFor(page);
  if (!companions.length) return null;
  const heading = companions.length > 1 ? 'Feature pages' : 'Companion page';
  return (
    <nav className="companionLinks" aria-label={heading}>
      <span className="companionLinks__eyebrow">{heading}</span>
      {companions.map((companion, index) => (
        <span className="companionLinks__item" key={companion.label}>
          {index ? <span className="companionLinks__separator" aria-hidden="true">·</span> : null}
          {companion.route
            ? <Link className="companionLinks__link" to={companion.route} title={companion.description}>{companion.label}</Link>
            : <span className="companionLinks__current" aria-current="page">{companion.label}</span>}
        </span>
      ))}
      {companions.length === 1 && <span className="companionLinks__description">{companions[0].description}</span>}
    </nav>
  );
}

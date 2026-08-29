const normalizeRoute = (route: string) => route === '/' ? route : route.replace(/\/$/, '');

const featureRouteBase = '/features';

export function canonicalRoute(route: string, baseUrl: string): string {
  const normalizedRoute = normalizeRoute(route);
  const normalizedBase = normalizeRoute(baseUrl);
  if (normalizedBase === '/' || normalizedBase === '') return normalizedRoute;
  if (normalizedRoute === normalizedBase) return '/';
  return normalizedRoute.startsWith(`${normalizedBase}/`)
    ? normalizedRoute.slice(normalizedBase.length)
    : normalizedRoute;
}

/**
 * The published projection of a specs-relative path. A module package keeps its submodules and boundary
 * contracts beneath `architecture/` (`<module>/architecture/modules/<child>/`, `<module>/architecture/contracts/<id>/`);
 * the site drops that grouping segment so routes read `<module>/modules/<child>/` and `<module>/contracts/<id>/`.
 */
export function projectedSpecPath(relativeSpecPath: string): string {
  return relativeSpecPath.replace(/(^|\/)architecture\/(modules|contracts)\//g, '$1$2/');
}

/** A URL/filesystem-safe segment derived from the globally unique stable feature ID. */
function featureIdentitySegment(featureId: string): string {
  return encodeURIComponent(featureId);
}

/**
 * Public/staged feature hierarchy: top-level features live at the Features root and an immediate
 * sub-feature lives directly beneath its explicit parent. Module/source placement is deliberately absent.
 */
export function semanticFeaturePath(featureId: string, parentSemanticPath?: string): string {
  const segment = featureIdentitySegment(featureId);
  return parentSemanticPath ? `${parentSemanticPath}/${segment}` : segment;
}

export function semanticFeatureRoutes(semanticPath: string): {
  landing: string;
  design: string;
  implementation: string;
} {
  const landing = `${featureRouteBase}/${semanticPath}`;
  return {landing, design: `${landing}/design`, implementation: `${landing}/implementation`};
}

export function semanticFeatureStagedPath(
  semanticPath: string,
  page: 'abstract' | 'design' | 'implementation',
): string {
  return `${semanticPath}/${page}.md`;
}

export {normalizeRoute};

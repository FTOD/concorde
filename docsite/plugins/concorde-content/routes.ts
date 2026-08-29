const normalizeRoute = (route: string) => route === '/' ? route : route.replace(/\/$/, '');

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

export {normalizeRoute};

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

function identitySegment(id: string): string {
  return encodeURIComponent(id);
}

export function moduleRoute(moduleId: string): string {
  return `/architecture/${identitySegment(moduleId)}`;
}

export function featureRoute(featureId: string): string {
  return `/features/${identitySegment(featureId)}`;
}

export function moduleStagedPath(moduleId: string): string {
  return `${identitySegment(moduleId)}/architecture.md`;
}

export function featureStagedPath(featureId: string): string {
  return `${identitySegment(featureId)}.md`;
}

export {normalizeRoute};

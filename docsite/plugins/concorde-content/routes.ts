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

export {normalizeRoute};

export type WorkspaceRoute = {
  provider?: string;
  model?: string;
  health?: string;
  enabled?: boolean;
  protocol?: string;
  baseUrl?: string;
};

export function workspaceScope(search = window.location.search) {
  const raw = new URLSearchParams(search).get("workspace") || "default";
  return raw.replace(/[^a-zA-Z0-9_-]/g, "-");
}

export function providerRouteStorageKey(search = window.location.search) {
  return `rabbit_code_provider_route_${workspaceScope(search)}`;
}

function workspaceRouteCatalogStorageKey(search = window.location.search) {
  return `rabbit_code_workspace_routes_${workspaceScope(search)}`;
}

export function workspaceHomeHref(search = window.location.search) {
  const workspace = new URLSearchParams(search).get("workspace");
  return workspace ? `/workspace/home?workspace=${encodeURIComponent(workspace)}` : "/workspace/home";
}

export function readWorkspaceRoute(search = window.location.search): WorkspaceRoute {
  try {
    const value = JSON.parse(localStorage.getItem(providerRouteStorageKey(search)) || "null") as WorkspaceRoute | null;
    return value && typeof value === "object" ? value : {};
  } catch {
    return {};
  }
}

export function readWorkspaceRoutes(search = window.location.search): WorkspaceRoute[] {
  try {
    const routes = JSON.parse(localStorage.getItem(workspaceRouteCatalogStorageKey(search)) || "[]") as WorkspaceRoute[];
    return Array.isArray(routes) ? routes.filter((route) => route && typeof route === "object") : [];
  } catch {
    return [];
  }
}

export function writeWorkspaceRoute(route: WorkspaceRoute, search = window.location.search) {
  localStorage.setItem(providerRouteStorageKey(search), JSON.stringify(route));
  if (!route.provider || !route.model) {
    return;
  }
  const routes = readWorkspaceRoutes(search).filter((item) => !(item.provider === route.provider && item.model === route.model));
  localStorage.setItem(workspaceRouteCatalogStorageKey(search), JSON.stringify([...routes, route]));
}

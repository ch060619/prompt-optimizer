/* The module intentionally co-locates the public navigation API and its provider. */
/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type AnchorHTMLAttributes,
  type MouseEvent,
  type ReactNode,
} from "react";

export type NavigationOptions = { replace?: boolean };

export const AGENT_ROUTES = {
  onboarding: "/onboarding",
  workspace: "/workspace",
  workspaceHome: "/workspace/home",
  tasks: "/workspace/task",
  review: "/workspace/review",
  terminal: "/workspace/terminal",
  providers: "/workspace/providers",
  models: "/workspace/models",
  assets: "/workspace/assets",
  settings: "/workspace/settings",
  diagnostics: "/workspace/diagnostics",
  login: "/login",
  register: "/register",
} as const;

// These paths were emitted by the former prompt-management site. They are
// canonicalized once so old bookmarks cannot reopen a detached application.
export const LEGACY_ROUTE_ALIASES: Readonly<Record<string, string>> = {
  "/prompt-management": AGENT_ROUTES.assets,
  "/evaluations": AGENT_ROUTES.review,
  "/prompt-chaining": AGENT_ROUTES.tasks,
};

export function canonicalPath(pathname: string): string {
  const normalized = pathname || "/";
  return LEGACY_ROUTE_ALIASES[normalized] ?? normalized;
}

type LocationState = { pathname: string; search: string; hash: string };
type NavigationContextValue = LocationState & {
  navigate: (href: string, options?: NavigationOptions) => boolean;
};

const NavigationContext = createContext<NavigationContextValue | null>(null);

function readLocation(): LocationState {
  return {
    pathname: window.location.pathname || "/",
    search: window.location.search,
    hash: window.location.hash,
  };
}

export function NavigationProvider({ children }: { children: ReactNode }) {
  const [location, setLocation] = useState<LocationState>(readLocation);

  useEffect(() => {
    const handlePopState = () => setLocation(readLocation());
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigate = useCallback((href: string, options: NavigationOptions = {}) => {
    let target: URL;
    try {
      target = new URL(href, window.location.origin);
    } catch {
      return false;
    }
    if (target.origin !== window.location.origin) {
      return false;
    }
    const path = canonicalPath(target.pathname);
    const next = `${path}${target.search}${target.hash}`;
    const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    if (next === current) {
      return true;
    }
    const method = options.replace ? "replaceState" : "pushState";
    window.history[method]({}, "", next);
    setLocation(readLocation());
    return true;
  }, []);

  const value = useMemo(() => ({ ...location, navigate }), [location, navigate]);
  return <NavigationContext.Provider value={value}>{children}</NavigationContext.Provider>;
}

export function useNavigation(): NavigationContextValue {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error("useNavigation must be used inside NavigationProvider");
  }
  return context;
}

type AppLinkProps = AnchorHTMLAttributes<HTMLAnchorElement> & { href: string };

function shouldUseClientNavigation(event: MouseEvent<HTMLAnchorElement>): boolean {
  return event.button === 0
    && !event.defaultPrevented
    && !event.metaKey
    && !event.ctrlKey
    && !event.shiftKey
    && !event.altKey;
}

/** Internal links keep app state; external links retain normal browser behavior. */
export function AppLink({ href, onClick, target, ...props }: AppLinkProps) {
  const navigation = useContext(NavigationContext);
  const handleClick = (event: MouseEvent<HTMLAnchorElement>) => {
    onClick?.(event);
    if (!navigation || !shouldUseClientNavigation(event) || target === "_blank" || !href.startsWith("/")) {
      return;
    }
    if (navigation.navigate(href)) {
      event.preventDefault();
    }
  };
  return <a {...props} href={href} target={target} onClick={handleClick} />;
}

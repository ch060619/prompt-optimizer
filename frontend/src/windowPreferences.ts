// RC ID: RC-120. Persist the webview-facing window and system integration state.

export type WindowPanel = "plan" | "diff" | "context";
export type WindowBounds = { x: number; y: number; width: number; height: number };
export type WorkArea = { x: number; y: number; width: number; height: number };
export type WindowPreferences = {
  bounds: WindowBounds;
  activePanel: WindowPanel;
  inspectorOpen: boolean;
  theme: "light" | "dark";
  notifications: boolean;
  tray: boolean;
};

export const WINDOW_PREFERENCES_KEY = "rabbit_code_window_preferences";

const defaults: WindowPreferences = {
  bounds: { x: 80, y: 80, width: 1280, height: 820 },
  activePanel: "plan",
  inspectorOpen: true,
  theme: "light",
  notifications: true,
  tray: false,
};

export function readWindowPreferences(storage?: Storage): WindowPreferences {
  const value = readStoredValue(storage);
  return {
    bounds: normalizeBounds(value?.bounds),
    activePanel: value?.activePanel === "diff" || value?.activePanel === "context" ? value.activePanel : defaults.activePanel,
    inspectorOpen: value?.inspectorOpen !== false,
    theme: value?.theme === "dark" ? "dark" : defaults.theme,
    notifications: value?.notifications !== false,
    tray: value?.tray === true,
  };
}

export function updateWindowPreferences(update: Partial<Omit<WindowPreferences, "bounds">> & { bounds?: Partial<WindowBounds> }, storage?: Storage): WindowPreferences {
  const next = readWindowPreferences(storage);
  const updated: WindowPreferences = {
    ...next,
    ...update,
    bounds: update.bounds ? { ...next.bounds, ...update.bounds } : next.bounds,
  };
  writeStoredValue(updated, storage);
  return updated;
}

export function restoreWindowBounds(bounds: WindowBounds, workArea: WorkArea): WindowBounds {
  const width = Math.min(Math.max(720, bounds.width), Math.max(720, workArea.width));
  const height = Math.min(Math.max(520, bounds.height), Math.max(520, workArea.height));
  const visible = 80;
  const minX = workArea.x - width + visible;
  const maxX = workArea.x + workArea.width - visible;
  const minY = workArea.y - height + visible;
  const maxY = workArea.y + workArea.height - visible;
  return {
    width,
    height,
    x: clamp(bounds.x, Math.min(minX, maxX), Math.max(minX, maxX)),
    y: clamp(bounds.y, Math.min(minY, maxY), Math.max(minY, maxY)),
  };
}

export function recordViewport(storage?: Storage): WindowPreferences {
  if (typeof window === "undefined" || window.outerWidth <= 0 || window.outerHeight <= 0) {
    return readWindowPreferences(storage);
  }
  return updateWindowPreferences({
    bounds: {
      x: window.screenX,
      y: window.screenY,
      width: window.outerWidth,
      height: window.outerHeight,
    },
  }, storage);
}

export function notifyWorkspace(title: string, body: string, storage?: Storage): boolean {
  const preferences = readWindowPreferences(storage);
  if (!preferences.notifications || typeof window === "undefined") {
    return false;
  }
  window.dispatchEvent(new CustomEvent("rabbit-code:notification", { detail: { title, body } }));
  if ("Notification" in window && Notification.permission === "granted") {
    new Notification(title, { body });
  }
  return true;
}

function readStoredValue(storage?: Storage): Record<string, unknown> | null {
  const target = storage ?? (typeof window === "undefined" ? undefined : window.localStorage);
  if (!target) {
    return null;
  }
  try {
    const value = JSON.parse(target.getItem(WINDOW_PREFERENCES_KEY) || "null") as unknown;
    return value && typeof value === "object" ? value as Record<string, unknown> : null;
  } catch {
    return null;
  }
}

function writeStoredValue(value: WindowPreferences, storage?: Storage) {
  const target = storage ?? (typeof window === "undefined" ? undefined : window.localStorage);
  target?.setItem(WINDOW_PREFERENCES_KEY, JSON.stringify(value));
}

function normalizeBounds(value: unknown): WindowBounds {
  if (!value || typeof value !== "object") {
    return defaults.bounds;
  }
  const candidate = value as Record<string, unknown>;
  return {
    x: finiteNumber(candidate.x, defaults.bounds.x),
    y: finiteNumber(candidate.y, defaults.bounds.y),
    width: finiteNumber(candidate.width, defaults.bounds.width),
    height: finiteNumber(candidate.height, defaults.bounds.height),
  };
}

function finiteNumber(value: unknown, fallback: number) {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(Math.max(value, minimum), maximum);
}

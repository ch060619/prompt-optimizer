import { afterEach, describe, expect, it, vi } from "vitest";

import { WINDOW_PREFERENCES_KEY, notifyWorkspace, readWindowPreferences, restoreWindowBounds, updateWindowPreferences } from "../src/windowPreferences";

// RC ID: RC-120. Verify window placement recovery, panel persistence, theme and notification preferences.

afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe("window preferences", () => {
  it("persists panel, theme, notification and tray choices", () => {
    expect(readWindowPreferences().activePanel).toBe("plan");
    updateWindowPreferences({ activePanel: "diff", inspectorOpen: false, theme: "dark", notifications: false, tray: true });

    expect(readWindowPreferences()).toMatchObject({
      activePanel: "diff",
      inspectorOpen: false,
      theme: "dark",
      notifications: false,
      tray: true,
    });
    expect(localStorage.getItem(WINDOW_PREFERENCES_KEY)).toContain('"theme":"dark"');
  });

  it("clamps a saved window back into a partially visible monitor work area", () => {
    const restored = restoreWindowBounds(
      { x: 8000, y: -4000, width: 320, height: 2000 },
      { x: -1920, y: 0, width: 1920, height: 1080 },
    );

    expect(restored.width).toBe(720);
    expect(restored.height).toBe(1080);
    expect(restored.x).toBe(-80);
    expect(restored.y).toBe(-1000);
  });

  it("emits an in-app notification event only when notifications are enabled", () => {
    const listener = vi.fn();
    window.addEventListener("rabbit-code:notification", listener);
    expect(notifyWorkspace("Rabbit Code", "Ready")).toBe(true);
    expect(listener).toHaveBeenCalledTimes(1);

    updateWindowPreferences({ notifications: false });
    expect(notifyWorkspace("Rabbit Code", "Suppressed")).toBe(false);
    expect(listener).toHaveBeenCalledTimes(1);
    window.removeEventListener("rabbit-code:notification", listener);
  });
});

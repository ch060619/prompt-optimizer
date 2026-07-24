import { render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SiteShell } from "../src/components/SiteShell";

// RC ID: RC-259. Keep idle work surfaces and reduced-motion users off the RAF loop.

function stubMotionPreference(reduced: boolean) {
  vi.stubGlobal("matchMedia", vi.fn(() => ({
    matches: reduced,
    media: "(prefers-reduced-motion: reduce)",
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })));
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("SiteShell motion budget", () => {
  it("does not start Lenis or a RAF loop on an idle work surface", () => {
    stubMotionPreference(false);
    const requestAnimationFrame = vi.spyOn(window, "requestAnimationFrame");

    render(
      <SiteShell hideHeader rabbitVariant="mark">
        <main>Workspace content</main>
      </SiteShell>,
    );

    expect(requestAnimationFrame).not.toHaveBeenCalled();
  });

  it("skips animation setup when reduced motion is requested", () => {
    stubMotionPreference(true);
    const requestAnimationFrame = vi.spyOn(window, "requestAnimationFrame");

    render(
      <SiteShell>
        <main className="reveal-on-scroll">Marketing content</main>
      </SiteShell>,
    );

    expect(requestAnimationFrame).not.toHaveBeenCalled();
  });

  it("pauses the RAF loop while hidden and resumes when visible", () => {
    stubMotionPreference(false);
    vi.stubGlobal("ResizeObserver", class {
      observe() {}
      unobserve() {}
      disconnect() {}
    });
    let visibility: DocumentVisibilityState = "hidden";
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      get: () => visibility,
    });
    vi.spyOn(window, "scrollTo").mockImplementation(() => undefined);
    const requestAnimationFrame = vi.spyOn(window, "requestAnimationFrame").mockReturnValue(7);
    const cancelAnimationFrame = vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);

    const { unmount } = render(
      <SiteShell>
        <main className="reveal-on-scroll">Animated content</main>
      </SiteShell>,
    );

    requestAnimationFrame.mockClear();
    expect(requestAnimationFrame).not.toHaveBeenCalled();
    visibility = "visible";
    document.dispatchEvent(new Event("visibilitychange"));
    expect(requestAnimationFrame).toHaveBeenCalledTimes(1);

    unmount();
    expect(cancelAnimationFrame).toHaveBeenCalledWith(7);
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });
  });
});

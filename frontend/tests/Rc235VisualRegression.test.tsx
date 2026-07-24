import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { ErrorState, EmptyState, InstallDialog, OfflineState } from "../src/components/UiStates";

// RC ID: RC-235. Keep route, theme, and shared visual-state contracts deterministic.

const routes = [
  "/",
  "/login",
  "/register",
  "/onboarding",
  "/workspace",
  "/workspace/home",
  "/workspace/task",
  "/workspace/review",
  "/workspace/terminal",
  "/workspace/providers",
  "/workspace/models",
  "/workspace/assets",
  "/workspace/settings",
  "/workspace/diagnostics",
] as const;

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
  window.history.replaceState({}, "", "/");
});

describe("RC-235 visual regression contracts", () => {
  it.each(routes)("renders the %s route with stable content and decorative artwork", (route) => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ status: "ok" }) })));
    window.history.replaceState({}, "", route);
    const view = render(<App />);

    expect(document.querySelector("main")).not.toBeNull();
    expect(document.body.textContent?.trim().length).toBeGreaterThan(0);
    expect(document.querySelector("img, svg")).not.toBeNull();
    expect(document.querySelector('[data-rabbit-layer="decorative"] button')).toBeNull();
    view.unmount();
  });

  it.each(["light", "dark"] as const)("keeps the %s theme explicit", (theme) => {
    localStorage.setItem("rabbit_code_settings_rc235", JSON.stringify({ theme }));
    window.history.replaceState({}, "", "/workspace/settings?workspace=rc235");
    render(<App />);

    fireEvent.change(screen.getByRole("combobox", { name: "Theme" }), { target: { value: theme } });
    expect(document.documentElement).toHaveAttribute("data-theme", theme);
    expect(screen.getByRole("complementary", { name: "Settings sections" })).toBeInTheDocument();
  });

  it("keeps empty, error, offline, and loading/install states renderable", () => {
    render(
      <>
        <EmptyState title="NO PROJECTS" description="Open a directory to start." />
        <ErrorState title="PROJECT SERVICE UNAVAILABLE" description="Try again." />
        <OfflineState title="OFFLINE MODE" description="This route stays on the machine." />
        <InstallDialog open title="Install local model?" description="Verify before use." onClose={() => undefined} onConfirm={() => undefined} />
      </>,
    );

    expect(screen.getByText("NO PROJECTS")).toBeInTheDocument();
    expect(screen.getByText("PROJECT SERVICE UNAVAILABLE")).toBeInTheDocument();
    expect(screen.getByText("OFFLINE MODE")).toBeInTheDocument();
    expect(screen.getByRole("dialog", { name: "Install local model?" })).toBeInTheDocument();
  });
});

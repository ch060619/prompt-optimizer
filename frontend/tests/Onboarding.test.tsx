import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

// RC ID: RC-109. Verify new, configured, and service-error onboarding states.

function visitOnboarding() {
  window.history.replaceState({}, "", "/onboarding");
}

function stubHealth(response: Response) {
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(response)));
}

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("onboarding", () => {
  it("shows two main choices for a new installation", async () => {
    visitOnboarding();
    stubHealth(new Response(JSON.stringify({ status: "ok" }), { status: 200 }));

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Start Rabbit Code." })).toBeInTheDocument();
    expect(screen.getByText("NEW INSTALLATION")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /USE API/i })).toHaveAttribute(
      "href",
      "/workspace/providers?entry=api",
    );
    expect(screen.getByRole("link", { name: /NO API/i })).toHaveAttribute(
      "href",
      "/workspace/models?entry=local",
    );
    expect(screen.getByText("DATA / SENT TO SELECTED PROVIDER")).toBeInTheDocument();
    expect(screen.getByText("DATA / STAYS ON THIS DEVICE")).toBeInTheDocument();
    expect(screen.getByText("NETWORK / INTERNET REQUIRED")).toBeInTheDocument();
    expect(screen.getByText("HARDWARE / CPU, GPU, AND DISK CHECK")).toBeInTheDocument();
    expect(screen.getAllByRole("link").filter((link) => link.getAttribute("href")?.includes("entry=")).length).toBe(2);
  });

  it("shows existing configuration and keeps both routes keyboard reachable", async () => {
    visitOnboarding();
    localStorage.setItem("rabbit_code_onboarding_configured", "true");
    localStorage.setItem("rabbit_code_api_configured", "true");
    localStorage.setItem("rabbit_code_local_runner_ready", "true");
    stubHealth(new Response(JSON.stringify({ status: "ok" }), { status: 200 }));

    render(<App />);

    expect(await screen.findByText("CONFIGURATION FOUND")).toBeInTheDocument();
    const apiChoice = screen.getByRole("link", { name: /USE API/i });
    const localChoice = screen.getByRole("link", { name: /NO API/i });
    apiChoice.focus();
    expect(document.activeElement).toBe(apiChoice);
    fireEvent.keyDown(apiChoice, { key: "Enter" });
    localChoice.focus();
    expect(document.activeElement).toBe(localChoice);
  });

  it("shows a service error with retry while preserving the two choices", async () => {
    visitOnboarding();
    stubHealth(Promise.reject(new Error("offline")) as unknown as Response);

    render(<App />);

    expect(await screen.findByText("LOCAL SERVICE UNAVAILABLE")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /RECHECK/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /USE API/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /NO API/i })).toBeInTheDocument();
  });
});

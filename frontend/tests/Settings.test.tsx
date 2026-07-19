import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

// RC IDs: RC-117, RC-184. Verify scoped settings and confirmed local-data cleanup.

function visitSettings(workspace = "alpha") {
  window.history.replaceState({}, "", `/workspace/settings?workspace=${workspace}`);
}

afterEach(() => {
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("settings", () => {
  it("renders sections and persists an appearance setting in the workspace scope", () => {
    visitSettings();
    render(<App />);

    expect(screen.getByRole("complementary", { name: "Settings sections" })).toHaveTextContent("Appearance");
    fireEvent.change(screen.getByRole("combobox", { name: "Theme" }), { target: { value: "dark" } });
    expect(screen.getByText("SETTING SAVED")).toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem("rabbit_code_settings_alpha") || "{}").theme).toBe("dark");
    expect(document.documentElement).toHaveAttribute("data-theme", "dark");
  });

  it("switches sections and keeps terminal, privacy, MCP and plugin controls scoped", () => {
    visitSettings("project-a");
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /Terminal/i }));
    fireEvent.change(screen.getByRole("combobox", { name: "Default shell" }), { target: { value: "WSL" } });
    fireEvent.click(screen.getByRole("button", { name: /Privacy/i }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Share anonymous usage telemetry" }));
    fireEvent.click(screen.getByRole("button", { name: /^MCP/i }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Enable MCP servers" }));
    fireEvent.click(screen.getByRole("button", { name: /^Plugins/i }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Enable workspace plugins" }));
    const saved = JSON.parse(localStorage.getItem("rabbit_code_settings_project-a") || "{}");
    expect(saved.shell).toBe("WSL");
    expect(saved.telemetry).toBe(true);
    expect(saved.mcp).toBe(true);
    expect(saved.plugins).toBe(true);
  });

  it("exposes workspace-scoped Provider and model CRUD from settings", () => {
    visitSettings("provider-workspace");
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /Providers & models/i }));
    expect(screen.getByRole("link", { name: /MANAGE PROVIDERS & MODELS/i })).toHaveAttribute(
      "href",
      "/workspace/providers?workspace=provider-workspace",
    );
  });

  it("does not leak settings between workspaces and confirms reset", () => {
    visitSettings("alpha");
    const first = render(<App />);
    fireEvent.change(screen.getByRole("combobox", { name: "Theme" }), { target: { value: "dark" } });
    first.unmount();
    visitSettings("beta");
    render(<App />);
    expect(screen.getByRole("combobox", { name: "Theme" })).toHaveValue("light");
    fireEvent.click(screen.getByRole("button", { name: /Data/i }));
    fireEvent.click(screen.getByRole("button", { name: /RESET WORKSPACE SETTINGS/i }));
    expect(screen.getByRole("alertdialog", { name: "Reset workspace settings" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /RESET SETTINGS/i }));
    expect(screen.getByText("WORKSPACE SETTINGS RESET")).toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem("rabbit_code_settings_alpha") || "{}").theme).toBe("dark");
    expect(JSON.parse(localStorage.getItem("rabbit_code_settings_beta") || "{}").theme).toBe("light");
  });

  it("previews local cleanup, preserves data on cancel, and clears it after confirmation", async () => {
    visitSettings("cleanup");
    localStorage.setItem("rabbit_code_settings_cleanup", JSON.stringify({ theme: "dark" }));
    vi.stubGlobal("fetch", vi.fn().mockImplementation(() => Promise.resolve(new Response(JSON.stringify({
      delete_paths: ["config.json", "rabbit-code.sqlite3"],
      credential_count: 1,
      retain: ["Rabbit Code application files"],
    }), { status: 200, headers: { "Content-Type": "application/json" } }))));

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /^Data/i }));
    fireEvent.click(screen.getByRole("button", { name: /PREVIEW ALL LOCAL DATA/i }));
    await waitFor(() => expect(screen.getByRole("alertdialog", { name: "Delete all local data" })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /^CANCEL$/i }));
    await waitFor(() => expect(screen.queryByRole("alertdialog", { name: "Delete all local data" })).not.toBeInTheDocument());
    expect(localStorage.getItem("rabbit_code_settings_cleanup")).toContain("dark");

    fireEvent.click(screen.getByRole("button", { name: /PREVIEW ALL LOCAL DATA/i }));
    await waitFor(() => expect(screen.getByRole("alertdialog", { name: "Delete all local data" })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /DELETE ALL LOCAL DATA/i }));
    await waitFor(() => expect(screen.getByText("ALL LOCAL DATA DELETED")).toBeInTheDocument());
    expect(localStorage.getItem("rabbit_code_settings_cleanup")).toBeNull();
    vi.unstubAllGlobals();
  });
});

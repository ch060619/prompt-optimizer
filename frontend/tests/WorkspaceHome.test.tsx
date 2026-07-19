import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

// RC ID: RC-183. Verify guest/local workspace access remains available without account login.
import { api } from "../src/api";

// RC ID: RC-110. Verify workspace home loading, empty/error states, recents, and actions.

function visitWorkspaceHome() {
  window.history.replaceState({}, "", "/workspace/home");
}

function stubFetch(handler: (url: string) => Response) {
  vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve(handler(url))));
}

afterEach(() => {
  vi.unstubAllGlobals();
  api.setToken(null);
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("workspace home", () => {
  it("renders an empty guest state with open and new task actions", async () => {
    visitWorkspaceHome();
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Pick up where you left off." })).toBeInTheDocument();
    expect(screen.getByText("NO RECENT PROJECTS")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /OPEN PROJECT/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /NEW TASK/i })).toHaveAttribute(
      "href",
      "/workspace?new=1",
    );
  });

  it("loads projects from the shared API and removes a local recent item", async () => {
    visitWorkspaceHome();
    api.setToken("token-projects");
    stubFetch((url) => {
      if (url === "/api/v1/projects") {
        return new Response(
          JSON.stringify([
            { id: 7, owner_id: 1, name: "Prompt Lab", created_at: "2026-07-18T00:00:00Z" },
          ]),
          { status: 200 },
        );
      }
      return new Response(JSON.stringify([]), { status: 200 });
    });

    render(<App />);

    expect(await screen.findByText("Prompt Lab")).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Workspace model" })).toHaveTextContent("Offline Rules / offline");
    fireEvent.click(screen.getByRole("button", { name: /REMOVE PROMPT LAB/i }));
    expect(screen.queryByText("Prompt Lab")).not.toBeInTheDocument();
  });

  it("shows a retryable service error without losing quick actions", async () => {
    visitWorkspaceHome();
    api.setToken("token-projects");
    stubFetch(() => {
      throw new Error("project service unavailable");
    });

    render(<App />);

    expect(await screen.findByText("PROJECT SERVICE UNAVAILABLE")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /RETRY/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /NEW TASK/i })).toBeInTheDocument();
  });

  it("offers cloud and local models without changing the workspace route", async () => {
    window.history.replaceState({}, "", "/workspace/home?workspace=rc177");
    localStorage.setItem("rabbit_code_provider_route_rc177", JSON.stringify({ provider: "openrouter", model: "team/model-v1", health: "healthy" }));
    localStorage.setItem("rabbit_code_workspace_routes_rc177", JSON.stringify([
      { provider: "openrouter", model: "team/model-v1", health: "healthy" },
      { provider: "local", model: "gemma-3-4b", health: "healthy" },
    ]));
    localStorage.setItem("rabbit_code_selected_model", "gemma-3-4b");
    localStorage.setItem("rabbit_code_local_runner_ready", "true");

    render(<App />);

    const selector = await screen.findByRole("combobox", { name: "Workspace model" });
    expect(selector).toHaveTextContent("Cloud / openrouter / team/model-v1");
    expect(selector).toHaveTextContent("Local / gemma-3-4b");
    fireEvent.change(selector, { target: { value: "local:gemma-3-4b" } });

    expect(screen.getByText("LOCAL")).toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem("rabbit_code_provider_route_rc177") || "{}")).toMatchObject({
      provider: "local",
      model: "gemma-3-4b",
    });
    expect(JSON.parse(localStorage.getItem("rabbit_code_workspace_routes_rc177") || "[]")).toEqual(expect.arrayContaining([
      expect.objectContaining({ provider: "openrouter", model: "team/model-v1" }),
      expect.objectContaining({ provider: "local", model: "gemma-3-4b" }),
    ]));
  });
});

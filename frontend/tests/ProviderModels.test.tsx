import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

// RC IDs: RC-114, RC-148, RC-181. Verify Provider CRUD, route persistence, capabilities, defaults, and source-only credential state.

function visitProviders() {
  window.history.replaceState({}, "", "/workspace/providers");
}

afterEach(() => {
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("Provider and model page", () => {
  it("renders provider state, capabilities, models, cost and default route", () => {
    visitProviders();
    render(<App />);

    expect(screen.getByRole("complementary", { name: "Providers" })).toHaveTextContent("OpenAI Compatible");
    expect(screen.getByRole("region", { name: "Provider capabilities" })).toHaveTextContent("TEXT");
    expect(screen.getByText("UNKNOWN COST")).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Default model" })).toHaveTextContent("OpenAI Compatible");
    expect(screen.getByText("NO MODELS DISCOVERED")).toBeInTheDocument();
  });

  it("shows a versioned privacy boundary and custom endpoint responsibility", () => {
    visitProviders();
    render(<App />);

    expect(screen.getByText("DATA HANDLING / custom-endpoint-v1")).toBeInTheDocument();
    expect(screen.getByText(/CUSTOM ENDPOINT \/ USER RESPONSIBILITY/)).toBeInTheDocument();
    expect(screen.getByText(/Unknown \/ configured endpoint/)).toBeInTheDocument();
  });

  it("shows an environment credential source without receiving its value", async () => {
    visitProviders();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      api_key: {
        value: "secret://config/api_key",
        source_label: "environment variable",
      },
    }), { status: 200, headers: { "Content-Type": "application/json" } })));

    render(<App />);

    await waitFor(() => expect(screen.getByText(/API KEY SOURCE \/ ENVIRONMENT/)).toBeInTheDocument());
    expect(screen.getByText(/API KEY SOURCE \/ ENVIRONMENT/)).not.toHaveTextContent("environment-secret");
    vi.unstubAllGlobals();
  });

  it("adds, tests, discovers, selects, disables, defaults, edits and deletes a provider without exposing the key", () => {
    visitProviders();
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Add provider" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Provider name" }), { target: { value: "Team Gateway" } });
    fireEvent.change(screen.getByRole("textbox", { name: "Provider base URL" }), { target: { value: "https://gateway.example/v1" } });
    fireEvent.change(screen.getByLabelText("Provider API key"), { target: { value: "top-secret-key" } });
    expect(screen.getByLabelText("Provider API key")).toHaveAttribute("type", "password");
    fireEvent.click(screen.getByRole("button", { name: /SAVE PROVIDER/i }));
    expect(screen.getAllByText("Team Gateway").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: /TEST CONNECTION/i }));
    expect(screen.getByText("CONNECTION PASSED")).toBeInTheDocument();
    expect(screen.getByText("MOCK / $0")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /DISCOVER/i }));
    expect(screen.getByText("auto-discovered-model")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Manual model ID" }), { target: { value: "team/model-v2" } });
    fireEvent.click(screen.getByRole("button", { name: "Add manual model" }));
    fireEvent.click(screen.getByRole("button", { name: /^team\/model-v2/ }));
    fireEvent.click(screen.getByRole("button", { name: /SET AS DEFAULT/i }));
    expect(screen.getByText("DEFAULT PROVIDER UPDATED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /DISABLE/i }));
    expect(screen.getByText("DISABLED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /EDIT/i }));
    expect(screen.getByRole("dialog", { name: "Edit provider" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /CANCEL/i }));
    fireEvent.click(screen.getByRole("button", { name: /DELETE/i }));
    expect(screen.getByRole("dialog", { name: "Delete provider" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /MIGRATE AND DELETE/i }));
    expect(screen.queryByText("Team Gateway")).not.toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem("rabbit_code_provider_route_default") || "{}")).toMatchObject({ provider: "offline" });
  });

  it("persists the supported workspace optimization route", () => {
    window.history.replaceState({}, "", "/workspace/providers?workspace=rc148");
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /Offline Rules/i }));
    fireEvent.click(screen.getByRole("button", { name: /SET AS DEFAULT/i }));

    expect(JSON.parse(localStorage.getItem("rabbit_code_provider_route_rc148") || "{}")).toMatchObject({
      provider: "offline",
      model: "offline",
    });
  });

  it("disables model discovery when the selected provider lacks model listing", () => {
    visitProviders();
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /Offline Rules/i }));

    expect(screen.getByRole("button", { name: /DISCOVER/i })).toBeDisabled();
  });

  it("rejects manual model IDs with whitespace without replacing saved choices", () => {
    visitProviders();
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Add provider" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Provider name" }), { target: { value: "Manual Test" } });
    fireEvent.click(screen.getByRole("button", { name: /SAVE PROVIDER/i }));
    fireEvent.change(screen.getByRole("textbox", { name: "Manual model ID" }), { target: { value: "bad model" } });
    fireEvent.click(screen.getByRole("button", { name: "Add manual model" }));

    expect(screen.getByText("INVALID MODEL ID")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /bad model/i })).not.toBeInTheDocument();
  });

  it("persists provider configuration without persisting the API key", () => {
    window.history.replaceState({}, "", "/workspace/providers?workspace=rc178");
    const first = render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Add provider" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Provider name" }), { target: { value: "Persisted Gateway" } });
    fireEvent.change(screen.getByRole("textbox", { name: "Provider base URL" }), { target: { value: "https://persisted.example/v1" } });
    fireEvent.change(screen.getByLabelText("Provider API key"), { target: { value: "persisted-secret" } });
    fireEvent.click(screen.getByRole("button", { name: /SAVE PROVIDER/i }));

    expect(localStorage.getItem("rabbit_code_provider_configs_rc178")).toContain("Persisted Gateway");
    expect(localStorage.getItem("rabbit_code_provider_configs_rc178")).not.toContain("persisted-secret");
    first.unmount();
    render(<App />);
    expect(screen.getByRole("heading", { name: "Persisted Gateway" })).toBeInTheDocument();
  });

  it("walks the API setup wizard, saves a non-secret draft, and gates the default", () => {
    window.history.replaceState({}, "", "/workspace/providers?entry=api&workspace=rc175");
    render(<App />);

    expect(screen.getByRole("heading", { name: "Configure a provider." })).toBeInTheDocument();
    fireEvent.change(screen.getByRole("combobox", { name: "API service" }), { target: { value: "openrouter" } });
    fireEvent.click(screen.getByRole("button", { name: /^NEXT$/i }));

    fireEvent.change(screen.getByRole("textbox", { name: "API base URL" }), { target: { value: "https://gateway.example/v1" } });
    fireEvent.change(screen.getByLabelText("Setup provider API key"), { target: { value: "wizard-secret" } });
    const draft = localStorage.getItem("rabbit_code_api_setup_draft_rc175") || "";
    expect(draft).toContain("gateway.example");
    expect(draft).not.toContain("wizard-secret");
    fireEvent.click(screen.getByRole("button", { name: /^NEXT$/i }));

    fireEvent.change(screen.getByRole("textbox", { name: "Setup model ID" }), { target: { value: "team/model-v1" } });
    fireEvent.click(screen.getByRole("button", { name: /^NEXT$/i }));
    const saveButton = screen.getByRole("button", { name: /SAVE AS DEFAULT/i });
    expect(saveButton).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /TEST CONNECTION \/ \$0/i }));
    expect(screen.getByText("MOCK CONNECTION PASSED")).toBeInTheDocument();
    expect(saveButton).toBeEnabled();
    fireEvent.click(saveButton);

    expect(screen.getByText(/DEFAULT MODEL SAVED/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /OPEN WORKSPACE HOME/i })).toHaveAttribute(
      "href",
      "/workspace/home?workspace=rc175",
    );
    expect(JSON.parse(localStorage.getItem("rabbit_code_provider_route_rc175") || "{}")).toMatchObject({
      provider: "openrouter",
      model: "team/model-v1",
      baseUrl: "https://gateway.example/v1",
    });
    expect(localStorage.getItem("rabbit_code_provider_route_rc175")).not.toContain("wizard-secret");
  });
});

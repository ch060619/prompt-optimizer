import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "../src/App";

// RC IDs: RC-115, RC-149, RC-185, RC-189. Verify hardware, shared JSON install events, Qwen identity, route persistence, recovery, and uninstall states.

function visitModels() {
  window.history.replaceState({}, "", "/workspace/models");
}

afterEach(() => {
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("local model installer", () => {
  it("renders hardware readiness, recommendations, license and integrity state", () => {
    visitModels();
    render(<App />);

    expect(screen.getByRole("region", { name: "Hardware readiness" })).toHaveTextContent("READY TO INSTALL");
    expect(screen.getByRole("complementary", { name: "Recommended local models" })).toHaveTextContent("Gemma 3 1B IT");
    expect(screen.getByRole("region", { name: "Local model installation" })).toHaveTextContent("Gemma Terms");
    expect(screen.getByText(/sha256:/)).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Install status" })).toHaveTextContent("DOWNLOAD");
  });

  it("installs, verifies, loads, stops and uninstalls Gemma", () => {
    visitModels();
    render(<App />);

    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: /INSTALL MODEL/i }));
    fireEvent.click(screen.getByRole("button", { name: /CONFIRM INSTALL/i }));
    fireEvent.click(screen.getByRole("button", { name: /COMPLETE DOWNLOAD/i }));
    fireEvent.click(screen.getByRole("button", { name: /VERIFY CHECKSUM/i }));
    expect(screen.getByText("CHECKSUM PASSED / MODEL READY")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /LOAD MODEL/i }));
    expect(screen.getByText("LOCAL RUNNER READY")).toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem("rabbit_code_provider_route_default") || "{}")).toMatchObject({
      provider: "local",
      model: "gemma-3-1b-it",
      health: "healthy",
    });
    fireEvent.click(screen.getByRole("button", { name: /STOP RUNNER/i }));
    fireEvent.click(screen.getByRole("button", { name: /LOAD MODEL/i }));
    fireEvent.click(screen.getByRole("button", { name: /UNINSTALL/i }));
    expect(screen.getByText("MODEL UNINSTALLED")).toBeInTheDocument();
  });

  it("supports pause and cancellation and repairs a checksum failure", () => {
    visitModels();
    render(<App />);

     fireEvent.click(screen.getByRole("button", { name: /Qwen2.5-Coder 1.5B/i }));
     expect(screen.getByText("Qwen/Qwen2.5-Coder-1.5B-Instruct / 3.1 GB download / Apache 2.0")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: /INSTALL MODEL/i }));
    fireEvent.click(screen.getByRole("button", { name: /CONFIRM INSTALL/i }));
    fireEvent.click(screen.getByRole("button", { name: /PAUSE/i }));
    fireEvent.click(screen.getByRole("button", { name: /RESUME DOWNLOAD/i }));
    fireEvent.click(screen.getByRole("button", { name: /CANCEL/i }));
    expect(screen.getByText("DOWNLOAD CANCELLED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /INSTALL MODEL/i }));
    fireEvent.click(screen.getByRole("button", { name: /CONFIRM INSTALL/i }));
    fireEvent.click(screen.getByRole("button", { name: /COMPLETE DOWNLOAD/i }));
    fireEvent.click(screen.getByRole("button", { name: /VERIFY CHECKSUM/i }));
    expect(screen.getByText("CHECKSUM FAILED / REPAIR AVAILABLE")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^RETRY$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /UNINSTALL/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /REPAIR MODEL/i }));
    fireEvent.click(screen.getByRole("button", { name: /VERIFY CHECKSUM/i }));
    expect(screen.getByText("CHECKSUM PASSED / MODEL READY")).toBeInTheDocument();
  });

  it("renders persisted update and failed states with recovery actions", () => {
    visitModels();
    localStorage.setItem("rabbit_code_local_models_default", JSON.stringify([
      { id: "gemma-3-1b-it", status: "update", progress: 100 },
    ]));
    const first = render(<App />);
    expect(screen.getAllByText("UPDATE AVAILABLE").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("button", { name: /UPDATE MODEL/i })).toBeInTheDocument();
    first.unmount();

    localStorage.setItem("rabbit_code_local_models_default", JSON.stringify([
      { id: "gemma-3-1b-it", status: "failed", progress: 32, error: "DOWNLOAD FAILED" },
    ]));
    render(<App />);
    expect(screen.getAllByText("FAILED").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("button", { name: /^RETRY$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /REPAIR MODEL/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /UNINSTALL/i })).toBeInTheDocument();
  });

  it("persists local model state and keeps the model history when disabled", () => {
    visitModels();
    const first = render(<App />);

    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: /INSTALL MODEL/i }));
    fireEvent.click(screen.getByRole("button", { name: /CONFIRM INSTALL/i }));
    fireEvent.click(screen.getByRole("button", { name: /COMPLETE DOWNLOAD/i }));
    fireEvent.click(screen.getByRole("button", { name: /VERIFY CHECKSUM/i }));
    fireEvent.click(screen.getByRole("button", { name: /LOAD MODEL/i }));
    fireEvent.click(screen.getByRole("button", { name: /DISABLE MODEL/i }));

    expect(screen.getByText("MODEL DISABLED / HISTORY RETAINED")).toBeInTheDocument();
    expect(localStorage.getItem("rabbit_code_local_models_default")).toContain('"status":"disabled"');
    first.unmount();
    render(<App />);
    expect(screen.getAllByText("DISABLED").length).toBeGreaterThanOrEqual(1);
    fireEvent.click(screen.getByRole("button", { name: /ENABLE MODEL/i }));
    expect(screen.getByText("MODEL ENABLED / CONFIGURATION RETAINED")).toBeInTheDocument();
  });

  it("walks the local setup wizard and resumes saved download progress", () => {
    window.history.replaceState({}, "", "/workspace/models?entry=local&workspace=rc176");
    render(<App />);

    expect(screen.getByRole("heading", { name: "Set up a local model." })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /CONTINUE/i }));
    fireEvent.change(screen.getByRole("combobox", { name: "Local runner" }), { target: { value: "llama.cpp" } });
    fireEvent.click(screen.getByRole("button", { name: /CONTINUE/i }));
    fireEvent.click(screen.getByRole("button", { name: /Gemma 3 1B IT/i }));
    fireEvent.click(screen.getByRole("button", { name: /CONTINUE/i }));
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: /CONTINUE/i }));
    fireEvent.click(screen.getByRole("button", { name: /START DOWNLOAD/i }));
    fireEvent.click(screen.getByRole("button", { name: /PAUSE/i }));
    expect(JSON.parse(localStorage.getItem("rabbit_code_local_setup_rc176") || "{}")).toMatchObject({
      phase: "install",
      status: "paused",
      progress: 32,
    });
    fireEvent.click(screen.getByRole("button", { name: /RESUME DOWNLOAD/i }));
    fireEvent.click(screen.getByRole("button", { name: /COMPLETE DOWNLOAD/i }));
    fireEvent.click(screen.getByRole("button", { name: /VERIFY CHECKSUM/i }));
    fireEvent.click(screen.getByRole("button", { name: /RUN HEALTH CHECK/i }));

    expect(screen.getByText("LOCAL MODEL HEALTH CHECK PASSED")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Gemma 3 1B IT is ready." })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /OPEN WORKSPACE HOME/i })).toHaveAttribute(
      "href",
      "/workspace/home?workspace=rc176",
    );
    expect(JSON.parse(localStorage.getItem("rabbit_code_provider_route_rc176") || "{}")).toMatchObject({
      provider: "local",
      model: "gemma-3-1b-it",
      health: "healthy",
    });
  });
});

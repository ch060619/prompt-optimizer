import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "../src/App";

// RC ID: RC-118. Verify health, actionable fixes, updates, licenses, and redacted diagnostics.

function visitDiagnostics() {
  window.history.replaceState({}, "", "/workspace/diagnostics");
}

afterEach(() => {
  window.history.replaceState({}, "", "/");
});

describe("diagnostics", () => {
  it("renders versions, health, logs, license, update and about state", () => {
    visitDiagnostics();
    render(<App />);

    expect(screen.getByRole("region", { name: "Component health" })).toHaveTextContent("Rabbit Code");
    expect(screen.getByRole("region", { name: "Component health" })).toHaveTextContent("DEGRADED");
    expect(screen.getByText(/rabbit-code/)).toBeInTheDocument();
    expect(screen.getByText("MIT / NOTICE")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "About Rabbit Code" })).toHaveTextContent("Open tools");
  });

  it("offers concrete fixes and update checks", () => {
    visitDiagnostics();
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /RESTART SIDECAR/i }));
    expect(screen.getByText("SIDECAR HEALTHY")).toBeInTheDocument();
    expect(screen.getAllByText("NO ACTION NEEDED").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: /CHECK FOR UPDATES/i }));
    expect(screen.getByText("UP TO DATE / 3.0.0")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /OPEN MODEL INSTALLER/i })).toHaveAttribute("href", "/workspace/models");
  });

  it("previews before copying only redacted diagnostics", () => {
    visitDiagnostics();
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /PREVIEW REDACTED DIAGNOSTICS/i }));
    expect(screen.getByRole("region", { name: "Diagnostic preview" })).toHaveTextContent("Metadata only");
    fireEvent.click(screen.getByRole("button", { name: /COPY PREVIEW/i }));
    expect(screen.getByText("REDACTED DIAGNOSTICS COPIED")).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("sk-");
    expect(document.body.textContent).not.toContain("def ");
    expect(document.body.textContent).not.toContain("[REDACTED]");
  });

  it("can clear the diagnostic preview without copying it", () => {
    visitDiagnostics();
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /PREVIEW REDACTED DIAGNOSTICS/i }));
    fireEvent.click(screen.getByRole("button", { name: /CLEAR PREVIEW/i }));
    expect(screen.queryByRole("region", { name: "Diagnostic preview" })).not.toBeInTheDocument();
    expect(screen.getByText("DIAGNOSTIC PREVIEW CLEARED")).toBeInTheDocument();
  });
});

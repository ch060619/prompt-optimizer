import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "../src/App";

// RC ID: RC-112. Verify file tree, hunk review, rollback, verification, and drift blocking.

function visitReview() {
  window.history.replaceState({}, "", "/workspace/review");
}

afterEach(() => {
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("change review", () => {
  it("renders a file tree, selected diff, and test status", () => {
    visitReview();
    render(<App />);

    expect(screen.getByRole("complementary", { name: "Changed files" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Diff review" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Changed files" })).toHaveTextContent("backend/rabbit_code/agent.py");
    expect(screen.getByText("TESTS NOT RUN")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ACCEPT HUNK/i })).toBeInTheDocument();
  });

  it("accepts and rejects hunks and runs verification", () => {
    visitReview();
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /ACCEPT HUNK/i }));
    expect(screen.getByText("ACCEPTED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /REJECT HUNK/i }));
    expect(screen.getByText("REJECTED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /RUN VERIFICATION/i }));
    expect(screen.getByText("TESTS PASSED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /ROLLBACK AGENT CHANGES/i }));
    expect(screen.getByText("ROLLBACK READY")).toBeInTheDocument();
  });

  it("blocks hunk application when workspace drift is detected", () => {
    visitReview();
    localStorage.setItem("rabbit_code_workspace_drift", "true");
    render(<App />);

    expect(screen.getByText("WORKSPACE DRIFT DETECTED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /ACCEPT HUNK/i }));
    expect(screen.getByText("Resolve workspace drift before applying changes.")).toBeInTheDocument();
    expect(screen.getByText("PENDING")).toBeInTheDocument();
  });
});

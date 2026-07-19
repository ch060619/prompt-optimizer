import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "../src/App";

// RC ID: RC-111. Verify the task workspace grid, composer draft, inspector, and terminal drawer.

function visitTaskWorkspace() {
  window.history.replaceState({}, "", "/workspace/task");
}

afterEach(() => {
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("task workspace", () => {
  it("renders workspace, conversation, inspector, and terminal regions", () => {
    visitTaskWorkspace();
    render(<App />);

    expect(screen.getByRole("complementary", { name: "Workspace sessions" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Task conversation" })).toBeInTheDocument();
    expect(screen.getByRole("tabpanel", { name: "PLAN" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Task inspector" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Task composer" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /OPEN TERMINAL/i })).toBeInTheDocument();
  });

  it("keeps the composer draft while switching inspector and terminal", () => {
    visitTaskWorkspace();
    render(<App />);
    const composer = screen.getByRole("textbox", { name: "Task composer" });

    fireEvent.change(composer, { target: { value: "Inspect the API boundary" } });
    fireEvent.click(screen.getByRole("tab", { name: "DIFF" }));
    fireEvent.click(screen.getByRole("button", { name: /COLLAPSE INSPECTOR/i }));
    fireEvent.click(screen.getByRole("button", { name: /OPEN TERMINAL/i }));

    expect(screen.getByRole("textbox", { name: "Task composer" })).toHaveValue(
      "Inspect the API boundary",
    );
    expect(screen.getByRole("region", { name: "Terminal drawer" })).toBeInTheDocument();
    expect(localStorage.getItem("rabbit_code_task_draft")).toBe("Inspect the API boundary");
    expect(JSON.parse(localStorage.getItem("rabbit_code_window_preferences") || "{}")).toMatchObject({
      activePanel: "diff",
      inspectorOpen: false,
    });
  });

  it("submits a message and exposes a new session action", () => {
    visitTaskWorkspace();
    render(<App />);
    const composer = screen.getByRole("textbox", { name: "Task composer" });
    fireEvent.change(composer, { target: { value: "Review the latest change" } });
    fireEvent.click(screen.getByRole("button", { name: /SEND TASK/i }));

    expect(screen.getByText("Review the latest change")).toBeInTheDocument();
    expect(screen.getByText("Task received. The shared agent is ready for the next step.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /^NEW SESSION$/i }));
    expect(screen.getByText("NEW SESSION READY")).toBeInTheDocument();
  });
});

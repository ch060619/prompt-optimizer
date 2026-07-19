import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "../src/App";

// RC ID: RC-113. Verify terminal tabs, shell I/O, process controls, resize, recovery, and close cleanup.

function visitTerminal() {
  window.history.replaceState({}, "", "/workspace/terminal");
}

afterEach(() => {
  window.history.replaceState({}, "", "/");
});

describe("terminal and process panel", () => {
  it("renders multiple terminal tabs, output, process status, and size controls", () => {
    visitTerminal();
    render(<App />);

    expect(screen.getByRole("tablist", { name: "Workspace terminals" })).toBeInTheDocument();
    expect(screen.getAllByRole("tab")).toHaveLength(2);
    expect(screen.getByRole("region", { name: "Active terminal" })).toBeInTheDocument();
    expect(screen.getByRole("log", { name: "Terminal output" })).toHaveTextContent("pty: service boundary");
    expect(screen.getByRole("complementary", { name: "Background processes" })).toHaveTextContent("RUNNING");
    expect(screen.getByRole("spinbutton", { name: "Terminal columns" })).toHaveValue(120);
  });

  it("sends commands, syncs size, stops and recovers terminal and processes", () => {
    visitTerminal();
    render(<App />);

    fireEvent.change(screen.getByRole("spinbutton", { name: "Terminal columns" }), { target: { value: "100" } });
    fireEvent.click(screen.getByRole("button", { name: /SYNC SIZE/i }));
    fireEvent.change(screen.getByRole("textbox", { name: "Terminal command" }), { target: { value: "echo ready" } });
    fireEvent.click(screen.getByRole("button", { name: /SEND TERMINAL COMMAND/i }));
    expect(screen.getByRole("log", { name: "Terminal output" })).toHaveTextContent("$ echo ready");
    fireEvent.click(screen.getByRole("button", { name: /STOP COMMAND/i }));
    fireEvent.click(screen.getByRole("button", { name: /RESTART TERMINAL/i }));
    fireEvent.click(screen.getByRole("button", { name: /STOP PROCESS/i }));
    expect(screen.getByText("BACKGROUND PROCESS STOPPED")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: /RESTART PROCESS/i })[0]);
    expect(screen.getByText("BACKGROUND PROCESS RESTARTED")).toBeInTheDocument();
  });

  it("confirms close and leaves no running process state", () => {
    visitTerminal();
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /CLOSE WORKSPACE/i }));
    expect(screen.getByRole("alertdialog", { name: "Close workspace confirmation" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /CONFIRM CLOSE/i }));
    expect(screen.getByText("CLOSED CLEANLY")).toBeInTheDocument();
    expect(screen.getByText("TERMINAL CLOSED / NO RUNNING PROCESS REMAINS")).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Background processes" })).toHaveTextContent("STOPPED");
  });
});

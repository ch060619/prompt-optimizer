import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PromptOptimizationDiff } from "../src/components/PromptOptimizationDiff";

// RC ID: RC-140. Cover structured prompt diff modes, actions, and long text windowing.

function renderDiff(overrides: Partial<React.ComponentProps<typeof PromptOptimizationDiff>> = {}) {
  const props = {
    original: "line one\nline two",
    optimized: "line one\nchanged line",
    onOptimizedChange: vi.fn(),
    onReplaceSelected: vi.fn(),
    onReplaceAll: vi.fn(),
    onRetry: vi.fn(),
    ...overrides,
  };
  return { ...render(<PromptOptimizationDiff {...props} />), props };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("PromptOptimizationDiff", () => {
  it("switches inline and side-by-side modes and selects changed rows", () => {
    const { props } = renderDiff();
    expect(screen.getByRole("region", { name: "Prompt diff lines" })).toHaveClass("prompt-diff-inline");
    fireEvent.click(screen.getByRole("button", { name: "SIDE BY SIDE" }));
    expect(screen.getByRole("region", { name: "Prompt diff lines" })).toHaveClass("prompt-diff-side-by-side");
    const changedRow = screen.getByRole("button", { name: "Diff line 2" });
    fireEvent.click(changedRow);
    expect(changedRow).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "REPLACE SELECTED" }));
    expect(screen.getByRole("button", { name: "REPLACE SELECTED" })).toBeDisabled();
    expect(props.onReplaceSelected).toHaveBeenCalledWith("line one\nchanged line");
  });

  it("supports copy, replace all, restore, undo, and retry actions", async () => {
    const writeText = vi.fn(async () => undefined);
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
    const { props } = renderDiff();
    const editor = screen.getByRole("textbox", { name: "Optimized prompt preview" });
    fireEvent.change(editor, { target: { value: "edited result" } });
    fireEvent.click(screen.getByRole("button", { name: /UNDO/i }));
    expect(props.onOptimizedChange).toHaveBeenCalledWith("line one\nchanged line");
    fireEvent.click(screen.getByRole("button", { name: /RESTORE ORIGINAL/i }));
    expect(props.onOptimizedChange).toHaveBeenCalledWith("line one\nline two");
    fireEvent.click(screen.getByRole("button", { name: /COPY OPTIMIZED/i }));
    expect(writeText).toHaveBeenCalledWith("line one\nchanged line");
    fireEvent.click(screen.getByRole("button", { name: "REPLACE ALL" }));
    fireEvent.click(screen.getByRole("button", { name: "RETRY" }));
    expect(props.onReplaceAll).toHaveBeenCalledTimes(1);
    expect(props.onRetry).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("OPTIMIZED PROMPT COPIED"));
  });

  it("renders only an overscanned window for long text", () => {
    const original = Array.from({ length: 1000 }, (_, index) => `line ${index}`).join("\n");
    const optimized = Array.from({ length: 1000 }, (_, index) => `result ${index}`).join("\n");
    renderDiff({ original, optimized });
    expect(screen.getAllByRole("button", { name: /Diff line/ }).length).toBeLessThan(1000);
  });

  it("closes the result layer through its accessible close action", () => {
    const onClose = vi.fn();
    renderDiff({ onClose });

    expect(screen.getByRole("dialog", { name: "Prompt optimization comparison" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "关闭优化结果" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

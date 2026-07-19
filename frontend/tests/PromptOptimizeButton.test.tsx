import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PromptOptimizeButton, type PromptOptimizeButtonProps } from "../src/components/PromptOptimizeButton";

// RC ID: RC-135. Cover the prompt optimization state machine and request guard.

function renderButton(
  onOptimize: PromptOptimizeButtonProps["onOptimize"],
  disabled = false,
  options: Partial<PromptOptimizeButtonProps> = {},
) {
  return render(
    <PromptOptimizeButton
      icon={<span aria-hidden="true">*</span>}
      onOptimize={onOptimize}
      disabled={disabled}
      {...options}
    />,
  );
}

describe("PromptOptimizeButton", () => {
  it("covers idle, hover, pressed, and loading without changing its control", async () => {
    const onOptimize = vi.fn(() => new Promise<void>(() => undefined));
    renderButton(onOptimize);
    const button = screen.getByRole("button", { name: "优化输入内容" });

    expect(button).toHaveAttribute("data-state", "idle");
    fireEvent.pointerEnter(button);
    expect(button).toHaveAttribute("data-state", "hover");
    fireEvent.pointerDown(button);
    expect(button).toHaveAttribute("data-state", "pressed");
    fireEvent.click(button);
    expect(button).toHaveAttribute("data-state", "loading");
    await waitFor(() => expect(onOptimize).toHaveBeenCalledTimes(1));
    expect(button).toHaveAttribute("aria-busy", "true");
  });

  it("allows one cancellation and ignores a late request result", async () => {
    let resolveRequest!: () => void;
    let requestSignal!: AbortSignal;
    const onOptimize = vi.fn((_requestId: string, signal: AbortSignal) => new Promise<void>((resolve) => {
      requestSignal = signal;
      resolveRequest = resolve;
    }));
    renderButton(onOptimize);
    const button = screen.getByRole("button", { name: "优化输入内容" });

    fireEvent.click(button);
    await waitFor(() => expect(onOptimize).toHaveBeenCalledTimes(1));
    fireEvent.click(button);
    await waitFor(() => expect(button).toHaveAttribute("data-state", "idle"));
    expect(onOptimize).toHaveBeenCalledTimes(1);
    expect(requestSignal.aborted).toBe(true);
    resolveRequest();
    await Promise.resolve();
    expect(button).toHaveAttribute("data-state", "idle");
  });

  it("exposes success and error states for the active request", async () => {
    const succeed = vi.fn(async () => undefined);
    const { unmount } = renderButton(succeed);
    const successButton = screen.getByRole("button", { name: "优化输入内容" });
    fireEvent.click(successButton);
    await waitFor(() => expect(successButton).toHaveAttribute("data-state", "success"));

    unmount();
    renderButton(vi.fn(async () => { throw new Error("offline"); }));
    const errorButton = screen.getByRole("button", { name: "优化输入内容" });
    fireEvent.click(errorButton);
    await waitFor(() => expect(errorButton).toHaveAttribute("data-state", "error"));
  });

  it("uses the disabled state without submitting a surrounding form", () => {
    const onOptimize = vi.fn(async () => undefined);
    renderButton(onOptimize, true);
    const button = screen.getByRole("button", { name: "优化输入内容" });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("data-state", "disabled");
    fireEvent.click(button);
    expect(onOptimize).not.toHaveBeenCalled();
  });

  it("disables empty input and preserves the complete request snapshot", async () => {
    const emptyRequest = vi.fn(async () => undefined);
    renderButton(emptyRequest, false, { input: "   " });
    const emptyButton = screen.getByRole("button", { name: "优化输入内容" });
    expect(emptyButton).toBeDisabled();
    expect(emptyButton).toHaveAttribute("data-state", "disabled");

    const snapshots: unknown[] = [];
    const onOptimize = vi.fn(async (_requestId: string, _signal: AbortSignal, snapshot: unknown) => {
      snapshots.push(snapshot);
    });
    renderButton(onOptimize, false, {
      input: "Keep this exact prompt",
      revision: 7,
      cursor: { start: 5, end: 9 },
      attachmentRefs: ["attachment-1"],
    });
    const button = screen.getAllByRole("button", { name: "优化输入内容" })[1];
    fireEvent.click(button);
    await waitFor(() => expect(onOptimize).toHaveBeenCalledTimes(1));
    expect(snapshots[0]).toEqual({
      text: "Keep this exact prompt",
      revision: 7,
      cursor: { start: 5, end: 9 },
      attachmentRefs: ["attachment-1"],
    });
  });

  it("rejects attachment-only and over-budget input without truncating or sending", async () => {
    const onOptimize = vi.fn(async () => undefined);
    const onValidationError = vi.fn();
    renderButton(onOptimize, false, { input: "", attachmentRefs: ["attachment-1"], onValidationError });
    const attachmentButton = screen.getByRole("button", { name: "优化输入内容" });
    fireEvent.click(attachmentButton);
    await waitFor(() => expect(attachmentButton).toHaveAttribute("data-state", "error"));
    expect(onOptimize).not.toHaveBeenCalled();
    expect(onValidationError).toHaveBeenCalledWith("只有附件暂不支持优化，请先输入提示词。");

    const longValidation = vi.fn();
    renderButton(onOptimize, false, { input: "x".repeat(12001), onValidationError: longValidation });
    const longButton = screen.getAllByRole("button", { name: "优化输入内容" })[1];
    fireEvent.click(longButton);
    await waitFor(() => expect(longButton).toHaveAttribute("data-state", "error"));
    expect(onOptimize).not.toHaveBeenCalled();
    expect(longValidation).toHaveBeenCalledWith("提示词超过 12000 个字符限制，未截断原文。");
  });

  it("shows a delayed tooltip for pointer and keyboard focus with distinct action semantics", () => {
    vi.useFakeTimers();
    try {
      renderButton(vi.fn(async () => undefined));
      const button = screen.getByRole("button", { name: "优化输入内容" });
      expect(button).toHaveAttribute("data-action", "prompt-optimize");
      expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();

      fireEvent.pointerEnter(button);
      expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
      act(() => { vi.advanceTimersByTime(499); });
      expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
      act(() => { vi.advanceTimersByTime(1); });
      expect(screen.getByRole("tooltip", { name: "优化输入内容" })).toBeInTheDocument();
      expect(button).toHaveAttribute("aria-describedby");

      fireEvent.pointerLeave(button);
      expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
      fireEvent.focus(button);
      act(() => { vi.advanceTimersByTime(500); });
      expect(screen.getByRole("tooltip", { name: "优化输入内容" })).toBeInTheDocument();
      fireEvent.blur(button);
      expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });
});

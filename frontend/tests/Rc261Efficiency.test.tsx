import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

// RC ID: RC-261. Keep keyboard, focus, session, and diff review paths efficient.

function response(payload: unknown) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(payload) });
}

const optimizeResult = {
  version_id: null,
  analysis: {
    prompt: "保留原始输入",
    optimized_prompt: "优化后的高频提示词",
    score: { total_score: 82, dimensions: [] },
    suggestions: [],
    strengths: [],
    created_at: "2026-07-19T00:00:00Z",
  },
  metadata: {
    provider_requested: "offline",
    provider_used: "offline",
    provider_display_name: "离线规则",
    model: null,
    execution_location: "local",
    fallback_used: false,
    latency_ms: 1,
    error_summary: null,
    error_code: null,
  },
};

function visit(pathname: string) {
  window.history.replaceState({}, "", pathname);
}

function stubWorkspaceApi() {
  const calls: string[] = [];
  vi.stubGlobal("fetch", vi.fn((url: string) => {
    calls.push(url);
    if (url.startsWith("/api/v1/templates") || url === "/api/v1/history") {
      return response([]);
    }
    if (url === "/api/v1/optimize") {
      return response(optimizeResult);
    }
    return response({});
  }));
  return calls;
}

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("RC-261 high-frequency workflows", () => {
  it("opens the command palette and returns focus to the composer", async () => {
    stubWorkspaceApi();
    visit("/workspace");
    render(<App />);

    const composer = screen.getByRole("textbox", { name: "提示词输入" });
    composer.focus();
    fireEvent.keyDown(document, { key: "k", ctrlKey: true });

    const palette = await screen.findByRole("dialog", { name: "Command palette" });
    expect(palette).toBeInTheDocument();
    expect(document.activeElement).toBe(screen.getByRole("textbox", { name: "Search commands" }));
    fireEvent.click(screen.getByRole("button", { name: /Focus prompt/ }));
    await waitFor(() => expect(document.activeElement).toBe(composer));
  });

  it("uses the default shortcut, keeps one request, and restores focus after diff review", async () => {
    const calls = stubWorkspaceApi();
    visit("/workspace");
    render(<App />);

    const composer = screen.getByRole("textbox", { name: "提示词输入" });
    fireEvent.change(composer, { target: { value: "保留原始输入" } });
    const optimize = screen.getByRole("button", { name: "优化输入内容" });
    await waitFor(() => expect(optimize).not.toBeDisabled());
    optimize.focus();
    fireEvent.keyDown(document, { key: "o", ctrlKey: true, shiftKey: true });

    expect(await screen.findByRole("textbox", { name: "Optimized prompt preview" })).toHaveValue(
      "优化后的高频提示词",
    );
    expect(calls.filter((url) => url === "/api/v1/optimize")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "关闭优化结果" }));
    await waitFor(() => expect(document.activeElement).toBe(optimize));
  });

  it("keeps the Vim shortcut available for users who switch presets", async () => {
    localStorage.setItem("rabbit_code_settings_default", JSON.stringify({ shortcutPreset: "vim" }));
    stubWorkspaceApi();
    visit("/workspace");
    render(<App />);

    const composer = screen.getByRole("textbox", { name: "提示词输入" });
    fireEvent.change(composer, { target: { value: "保留原始输入" } });
    const optimize = screen.getByRole("button", { name: "优化输入内容" });
    await waitFor(() => expect(optimize).not.toBeDisabled());
    fireEvent.keyDown(document, { key: "o", altKey: true });

    expect(await screen.findByRole("textbox", { name: "Optimized prompt preview" })).toHaveValue(
      "优化后的高频提示词",
    );
  });

  it("supports session reset and focused diff review actions", () => {
    visit("/workspace/task");
    const task = render(<App />);
    fireEvent.change(screen.getByRole("textbox", { name: "Task composer" }), { target: { value: "审查最新改动" } });
    fireEvent.click(screen.getByRole("button", { name: /^NEW SESSION$/i }));
    expect(screen.getByRole("status")).toHaveTextContent("NEW SESSION READY");
    expect(screen.getByRole("textbox", { name: "Task composer" })).toHaveValue("");
    task.unmount();

    visit("/workspace/review");
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /VIEW ORIGINAL/i }));
    expect(screen.getByText(/Original file content/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /ACCEPT HUNK/i }));
    fireEvent.click(screen.getByRole("button", { name: /RUN VERIFICATION/i }));
    expect(screen.getByText("ACCEPTED")).toBeInTheDocument();
    expect(screen.getByText("TESTS PASSED")).toBeInTheDocument();
  });
});

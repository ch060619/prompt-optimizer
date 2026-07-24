import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

describe("reference workspace surface", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    window.history.replaceState({}, "", "/");
  });

  it("keeps the reference layout and extracted artwork on the main workspace route", async () => {
    window.history.replaceState({}, "", "/workspace");
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      if (url.startsWith("/api/v1/templates") || url === "/api/v1/history") {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));

    render(<App />);

    expect(await screen.findByRole("heading", { name: "我们该构建什么？" })).toBeInTheDocument();
    expect(document.querySelector(".reference-workspace")).not.toBeNull();
    expect(screen.getByRole("img", { name: "Rabbit Code 桌面端兔兔" })).toHaveAttribute("src", "/rabbit-desktop.png");
    expect(screen.getByRole("link", { name: "技能" })).toHaveAttribute("href", "/workspace/assets");
    expect(screen.getByRole("link", { name: "项目" })).toHaveAttribute("href", "/workspace/home");
    expect(screen.getByRole("textbox", { name: "提示词输入" })).toHaveAttribute("placeholder", "描述你想要完成的任务...");
  });

  it("uses the composer star to optimize in the backend and show the result dialog", async () => {
    window.history.replaceState({}, "", "/workspace");
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      if (url.startsWith("/api/v1/templates") || url === "/api/v1/history") {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      if (url === "/api/v1/optimize") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            version_id: null,
            analysis: {
              prompt: "优化这个提示词",
              optimized_prompt: "后台返回的优化提示词",
              score: { total_score: 90, dimensions: [] },
              suggestions: [],
              strengths: [],
              created_at: "2026-07-19T00:00:00Z",
            },
            metadata: {
              provider_requested: "offline",
              provider_used: "offline",
              fallback_used: false,
              latency_ms: 1,
              error_summary: null,
            },
          }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));

    render(<App />);

    const input = await screen.findByRole("textbox", { name: "提示词输入" });
    fireEvent.change(input, { target: { value: "优化这个提示词", selectionStart: 7, selectionEnd: 7 } });
    const optimize = screen.getByRole("button", { name: "优化输入内容" });
    expect(optimize.querySelector("svg")).toHaveClass("lucide-sparkles");
    fireEvent.click(optimize);

    expect(await screen.findByRole("textbox", { name: "Optimized prompt preview" })).toHaveValue("后台返回的优化提示词");
  });
});

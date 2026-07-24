import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

// RC ID: RC-195. Verify default/session isolation, context gating, and request metadata.

function response(payload: unknown) {
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve(payload),
  });
}

function visitWorkspace() {
  window.history.replaceState({}, "", "/workspace?workspace=rc195&session=alpha");
}

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("local model selection", () => {
  it("stores a session override and sends the selected Qwen model", async () => {
    visitWorkspace();
    localStorage.setItem("rabbit_code_default_local_model", "gemma-3-1b-it");
    localStorage.setItem("rabbit_code_local_models_rc195", JSON.stringify([
      { id: "gemma-3-1b-it", status: "ready" },
      { id: "qwen2.5-coder-1.5b-instruct", status: "ready" },
    ]));
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      calls.push({ url, init });
      if (url === "/api/v1/optimize") {
        return response({
          version_id: null,
          analysis: {
            prompt: "test prompt",
            optimized_prompt: "optimized with qwen",
            score: { total_score: 80, dimensions: [] },
            suggestions: [],
            strengths: [],
            created_at: "2026-07-19T00:00:00Z",
          },
          metadata: {
            provider_requested: "local",
            provider_used: "local",
            provider_display_name: "Local Model",
            model: "qwen2.5-coder-1.5b-instruct",
            execution_location: "local",
            fallback_used: false,
            latency_ms: 1,
          },
        });
      }
      return response([]);
    }));

    render(<App />);
    const selector = await screen.findByRole("combobox", { name: "Session local model" });
    fireEvent.change(selector, { target: { value: "qwen2.5-coder-1.5b-instruct" } });

    expect(localStorage.getItem("rabbit_code_session_local_model_rc195_alpha")).toBe(
      "qwen2.5-coder-1.5b-instruct",
    );
    expect(localStorage.getItem("rabbit_code_default_local_model")).toBe("gemma-3-1b-it");

    fireEvent.change(await screen.findByRole("textbox", { name: "提示词输入" }), {
      target: { value: "请用一句话解释本地模型。" },
    });
    fireEvent.click(screen.getByRole("button", { name: "优化输入内容" }));
    expect(await screen.findByRole("textbox", { name: "Optimized prompt preview" })).toHaveValue(
      "optimized with qwen",
    );
    const optimizeCall = calls.find((call) => call.url === "/api/v1/optimize");
    expect(JSON.parse(String(optimizeCall?.init?.body))).toMatchObject({
      provider: "local",
      model: "qwen2.5-coder-1.5b-instruct",
    });
    expect(screen.getByRole("region", { name: "Optimization metadata" })).toHaveTextContent(
      "qwen2.5-coder-1.5b-instruct",
    );
  });

  it("keeps the session override isolated by session id", async () => {
    visitWorkspace();
    localStorage.setItem("rabbit_code_local_models_rc195", JSON.stringify([
      { id: "gemma-3-1b-it", status: "ready" },
      { id: "qwen2.5-coder-1.5b-instruct", status: "ready" },
    ]));
    localStorage.setItem("rabbit_code_session_local_model_rc195_beta", "qwen2.5-coder-1.5b-instruct");
    vi.stubGlobal("fetch", vi.fn(() => response([])));
    const first = render(<App />);

    expect(await screen.findByRole("combobox", { name: "Session local model" })).toHaveValue("");
    first.unmount();
    window.history.replaceState({}, "", "/workspace?workspace=rc195&session=beta");
    render(<App />);

    await waitFor(() => expect(screen.getByRole("combobox", { name: "Session local model" })).toHaveValue(
      "qwen2.5-coder-1.5b-instruct",
    ));
  });

  it("rejects a local model switch when the prompt exceeds its context", async () => {
    visitWorkspace();
    localStorage.setItem("rabbit_code_local_models_rc195", JSON.stringify([
      { id: "gemma-3-1b-it", status: "ready" },
      { id: "qwen2.5-coder-1.5b-instruct", status: "ready" },
    ]));
    vi.stubGlobal("fetch", vi.fn(() => response([])));
    render(<App />);

    const composer = await screen.findByRole("textbox", { name: "提示词输入" });
    fireEvent.change(composer, { target: { value: "x".repeat(8193) } });
    const selector = screen.getByRole("combobox", { name: "Session local model" });
    fireEvent.change(selector, { target: { value: "gemma-3-1b-it" } });

    expect(selector).toHaveValue("");
    expect(screen.getByText(/上下文长度限制/)).toBeInTheDocument();
  });
});

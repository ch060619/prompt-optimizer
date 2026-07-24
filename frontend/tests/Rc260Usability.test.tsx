import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

// RC ID: RC-260. Keep the no-tutorial first-run paths executable at the UI boundary.

function response(payload: unknown) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(payload) });
}

const optimizeResult = {
  version_id: null,
  analysis: {
    prompt: "帮我写一个函数",
    optimized_prompt: "请实现一个可测试的函数，并补充边界测试。",
    score: { total_score: 86, dimensions: [] },
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
  vi.stubGlobal("fetch", vi.fn((url: string) => {
    if (url.startsWith("/api/v1/templates") || url === "/api/v1/history" || url === "/api/v1/provider-privacy") {
      return response([]);
    }
    if (url === "/api/v1/optimize") {
      return response(optimizeResult);
    }
    return response({});
  }));
}

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("RC-260 no-tutorial usability paths", () => {
  it("makes both first-run routes discoverable without external instructions", async () => {
    stubWorkspaceApi();
    visit("/onboarding");
    render(<App />);

    expect(screen.getByRole("link", { name: /USE API \/ CONFIGURE PROVIDER/ })).toHaveAttribute(
      "href",
      "/workspace/providers?entry=api",
    );
    expect(screen.getByRole("link", { name: /NO API \/ LOCAL MODEL/ })).toHaveAttribute(
      "href",
      "/workspace/models?entry=local",
    );
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("NEW INSTALLATION"));
  });

  it("walks the local model install and health checkpoints", () => {
    visit("/workspace/models?entry=local");
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "CONTINUE" }));
    fireEvent.click(screen.getByRole("button", { name: "CONTINUE" }));
    fireEvent.click(screen.getByRole("button", { name: /Qwen2.5-Coder 1.5B/ }));
    fireEvent.click(screen.getByRole("button", { name: "CONTINUE" }));
    fireEvent.click(screen.getByRole("checkbox", { name: /Apache 2.0/ }));
    fireEvent.click(screen.getByRole("button", { name: "CONTINUE" }));
    fireEvent.click(screen.getByRole("button", { name: "START DOWNLOAD" }));
    fireEvent.click(screen.getByRole("button", { name: "COMPLETE DOWNLOAD" }));
    fireEvent.click(screen.getByRole("button", { name: "VERIFY CHECKSUM" }));
    fireEvent.click(screen.getByRole("button", { name: "RUN HEALTH CHECK" }));

    expect(screen.getByRole("heading", { name: "Qwen2.5-Coder 1.5B is ready." })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "OPEN WORKSPACE HOME" })).toBeInTheDocument();
  });

  it("walks API configuration from provider choice to a $0 mock test", async () => {
    stubWorkspaceApi();
    visit("/workspace/providers?entry=api");
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "NEXT" }));
    await waitFor(() => expect(screen.getByLabelText("Setup provider API key")).toBeInTheDocument());
    const apiKey = screen.getByLabelText("Setup provider API key");
    fireEvent.change(apiKey, {
      target: { value: "sk-test-rc260" },
    });
    fireEvent.click(screen.getByRole("button", { name: "NEXT" }));
    await waitFor(() => expect(screen.getByLabelText("Setup model ID")).toBeInTheDocument());
    const modelId = screen.getByLabelText("Setup model ID");
    fireEvent.change(modelId, {
      target: { value: "gpt-4o-mini" },
    });
    fireEvent.click(screen.getByRole("button", { name: "NEXT" }));
    fireEvent.click(screen.getByRole("button", { name: /TEST CONNECTION/ }));

    expect(await screen.findByText("MOCK CONNECTION PASSED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "SAVE AS DEFAULT" }));
    expect(screen.getByText(/DEFAULT MODEL SAVED/)).toBeInTheDocument();
  });

  it("lets a new user optimize a real prompt without sending it", async () => {
    stubWorkspaceApi();
    visit("/workspace");
    render(<App />);

    const composer = screen.getByRole("textbox", { name: "提示词输入" });
    fireEvent.change(composer, { target: { value: "帮我写一个函数" } });
    const optimize = screen.getByRole("button", { name: "优化输入内容" });
    await waitFor(() => expect(optimize).not.toBeDisabled());
    fireEvent.click(optimize);

    expect(await screen.findByRole("textbox", { name: "Optimized prompt preview" })).toHaveValue(
      "请实现一个可测试的函数，并补充边界测试。",
    );
    expect(composer).toHaveValue("帮我写一个函数");
    await waitFor(() => expect(screen.getByRole("button", { name: "发送" })).not.toBeDisabled());
  });
});

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

// RC IDs: RC-246, RC-247. Keep the API and local first-run journeys deterministic and offline.

type ResponseLike = {
  ok: boolean;
  body?: ReadableStream<Uint8Array>;
  json: () => Promise<unknown>;
};

const analysis = {
  prompt: "写一个发布计划",
  optimized_prompt: "请输出一个带风险和负责人字段的发布计划。",
  score: { total_score: 90, dimensions: [] },
  suggestions: [],
  strengths: [],
  created_at: "2026-07-19T00:00:00Z",
};

function response(payload: unknown): ResponseLike {
  return { ok: true, json: () => Promise.resolve(payload) };
}

function streamResponse(): ResponseLike {
  const events = [
    `event: started\ndata: {"provider":"openai"}`,
    `event: analysis\ndata: ${JSON.stringify(analysis)}`,
    `event: chunk\ndata: {"text":"已发送"}`,
    `event: completed\ndata: ${JSON.stringify({
      version_id: 42,
      analysis,
      metadata: {
        provider_requested: "openai",
        provider_used: "openai",
        provider_display_name: "Mock OpenAI",
        model: "mock-model",
        execution_location: "cloud",
        fallback_used: false,
        latency_ms: 1,
      },
    })}`,
  ].join("\n\n");
  return {
    ok: true,
    body: new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(`${events}\n\n`));
        controller.close();
      },
    }),
    json: () => Promise.resolve({}),
  };
}

function stubOfflineApi() {
  vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/provider-privacy")) return Promise.resolve(response([]));
    if (url.includes("/config")) return Promise.resolve(response({}));
    if (url.includes("/templates") || url.endsWith("/history")) return Promise.resolve(response([]));
    if (url.includes("/local-models/") && url.endsWith("/state")) {
      return Promise.resolve(response({ event: "recovered", lifecycle_status: "not_installed", state: { status: "not_installed" } }));
    }
    if (url.endsWith("/local-models/directory")) return Promise.resolve(response({ root: "" }));
    if (url.endsWith("/optimize")) return Promise.resolve(response({ version_id: 42, analysis, metadata: {
      provider_requested: "openai",
      provider_used: "openai",
      provider_display_name: "Mock OpenAI",
      model: "mock-model",
      execution_location: "cloud",
      fallback_used: false,
      latency_ms: 1,
    } }));
    if (url.includes("/optimize/stream")) return Promise.resolve(streamResponse());
    return Promise.resolve(response({}));
  }));
}

function visit(path: string) {
  window.history.replaceState({}, "", path);
}

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("cross-surface user journeys", () => {
  it("completes API setup, star optimization, adoption, and send with one provider", async () => {
    stubOfflineApi();
    visit("/workspace/providers?entry=api&workspace=journey-api");
    const setup = render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /^NEXT$/i }));
    fireEvent.change(screen.getByRole("textbox", { name: "API base URL" }), { target: { value: "https://mock.example/v1" } });
    fireEvent.change(screen.getByLabelText("Setup provider API key"), { target: { value: "mock-key" } });
    fireEvent.click(screen.getByRole("button", { name: /^NEXT$/i }));
    fireEvent.change(screen.getByRole("textbox", { name: "Setup model ID" }), { target: { value: "mock-model" } });
    fireEvent.click(screen.getByRole("button", { name: /^NEXT$/i }));
    fireEvent.click(screen.getByRole("button", { name: /TEST CONNECTION \/ \$0/i }));
    fireEvent.click(screen.getByRole("button", { name: /SAVE AS DEFAULT/i }));

    expect(JSON.parse(localStorage.getItem("rabbit_code_provider_route_journey-api") || "{}")).toMatchObject({
      provider: "openai",
      model: "mock-model",
    });

    setup.unmount();
    visit("/workspace?workspace=journey-api");
    render(<App />);
    const input = await screen.findByRole("textbox", { name: "提示词输入" });
    fireEvent.change(input, { target: { value: "写一个发布计划" } });
    fireEvent.click(screen.getByRole("button", { name: "优化输入内容" }));
    expect(await screen.findByRole("textbox", { name: "Optimized prompt preview" })).toHaveValue(analysis.optimized_prompt);
    fireEvent.click(screen.getByRole("button", { name: "REPLACE ALL" }));
    expect(input).toHaveValue(analysis.optimized_prompt);
    fireEvent.click(screen.getByRole("button", { name: "发送" }));
    await waitFor(() => expect(screen.getByText("优化完成")).toBeInTheDocument());
    expect(screen.getByRole("region", { name: "Optimization metadata" })).toHaveTextContent("Mock OpenAI");
  });

  it("completes both Gemma and Qwen local setup routes without a network call", async () => {
    stubOfflineApi();
    for (const [workspace, modelName, modelId] of [
      ["journey-gemma", "Gemma 3 1B IT", "gemma-3-1b-it"],
      ["journey-qwen", "Qwen2.5-Coder 1.5B", "qwen2.5-coder-1.5b-instruct"],
    ] as const) {
      visit(`/workspace/models?entry=local&workspace=${workspace}`);
      const view = render(<App />);
      await waitFor(() => expect(screen.getByRole("heading", { name: "Set up a local model." })).toBeInTheDocument());
      fireEvent.click(screen.getByRole("button", { name: /CONTINUE/i }));
      fireEvent.click(screen.getByRole("button", { name: /CONTINUE/i }));
      fireEvent.click(screen.getByRole("button", { name: new RegExp(modelName) }));
      fireEvent.click(screen.getByRole("button", { name: /CONTINUE/i }));
      fireEvent.click(screen.getByRole("checkbox"));
      fireEvent.click(screen.getByRole("button", { name: /CONTINUE/i }));
      fireEvent.click(screen.getByRole("button", { name: /START DOWNLOAD/i }));
      fireEvent.click(screen.getByRole("button", { name: /COMPLETE DOWNLOAD/i }));
      fireEvent.click(screen.getByRole("button", { name: /VERIFY CHECKSUM/i }));
      fireEvent.click(screen.getByRole("button", { name: /RUN HEALTH CHECK/i }));
      expect(screen.getByRole("heading", { name: `${modelName} is ready.` })).toBeInTheDocument();
      expect(localStorage.getItem(`rabbit_code_provider_route_${workspace}`)).toContain(modelId);
      view.unmount();
    }
  });
});

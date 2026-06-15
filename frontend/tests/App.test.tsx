import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

function stubFetch(handler?: (url: string) => Promise<ResponseLike>) {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (handler) {
        return handler(url);
      }
      if (url.startsWith("/api/templates")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([])
        });
      }
      if (url === "/api/history") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([])
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    })
  );
}

interface ResponseLike {
  ok: boolean;
  body?: ReadableStream<Uint8Array>;
  json: () => Promise<unknown>;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("renders the local workspace", async () => {
    stubFetch();
    render(<App />);
    expect(await screen.findByText("Prompt Optimizer")).toBeInTheDocument();
    expect(screen.getByText("优化并保存")).toBeInTheDocument();
  });

  it("shows initialization errors from the API", async () => {
    stubFetch((url: string) => {
      if (url.startsWith("/api/templates")) {
        return Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ detail: "模板加载失败" })
        });
      }
      if (url === "/api/history") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([])
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    });
    render(<App />);
    expect(await screen.findByText("模板加载失败")).toBeInTheDocument();
  });

  it("shows streamed optimization output", async () => {
    const analysis = {
      prompt: "帮我写销售话术",
      optimized_prompt: null,
      score: { total_score: 70, dimensions: [] },
      suggestions: [],
      strengths: [],
      created_at: "2026-06-15T00:00:00Z"
    };
    stubFetch((url: string) => {
      if (url.startsWith("/api/templates")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      if (url === "/api/history") {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      if (url === "/api/optimize/stream") {
        const payload = [
          `event: started\ndata: {"provider":"offline"}`,
          `event: analysis\ndata: ${JSON.stringify(analysis)}`,
          `event: chunk\ndata: {"text":"优化后的提示词"}`,
          `event: saved\ndata: {"version_id":1}`,
          `event: completed\ndata: ${JSON.stringify({
            version_id: 1,
            analysis: { ...analysis, optimized_prompt: "优化后的提示词" },
            metadata: {
              provider_requested: "offline",
              provider_used: "offline",
              fallback_used: false,
              latency_ms: 1
            }
          })}`
        ].join("\n\n");
        return Promise.resolve({
          ok: true,
          body: new ReadableStream<Uint8Array>({
            start(controller) {
              controller.enqueue(new TextEncoder().encode(`${payload}\n\n`));
              controller.close();
            }
          }),
          json: () => Promise.resolve({})
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    render(<App />);

    fireEvent.click(await screen.findByText("流式优化"));

    expect(await screen.findByText("优化完成")).toBeInTheDocument();
    expect(screen.getAllByText("优化后的提示词").length).toBeGreaterThan(0);
  });
});

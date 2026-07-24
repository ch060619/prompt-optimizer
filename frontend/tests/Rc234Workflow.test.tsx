import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

// RC ID: RC-234. Keep the GUI workflow traceable through one mocked App Server contract.

const analysis = {
  prompt: "原始提示词",
  optimized_prompt: "优化后的提示词",
  score: { total_score: 88, dimensions: [] },
  suggestions: [],
  strengths: [],
  created_at: "2026-07-19T00:00:00Z",
};

const metadata = {
  provider_requested: "offline",
  provider_used: "offline",
  provider_display_name: "离线规则",
  model: null,
  execution_location: "local",
  fallback_used: false,
  latency_ms: 1,
  error_summary: null,
  error_code: null,
};

function jsonResponse(payload: unknown) {
  return { ok: true, json: () => Promise.resolve(payload) };
}

function installWorkflowFetch() {
  const result = { version_id: null, analysis, metadata };
  const stream = [
    `event: started\ndata: {"provider":"offline"}`,
    `event: analysis\ndata: ${JSON.stringify(analysis)}`,
    `event: chunk\ndata: {"text":"优化后的提示词"}`,
    `event: completed\ndata: ${JSON.stringify(result)}`,
  ].join("\n\n");
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.startsWith("/api/v1/templates") || url === "/api/v1/history") {
        return Promise.resolve(jsonResponse([]));
      }
      if (url === "/api/v1/optimize") {
        return Promise.resolve(jsonResponse(result));
      }
      if (url === "/api/v1/optimize/stream") {
        return Promise.resolve({
          ok: true,
          body: new ReadableStream<Uint8Array>({
            start(controller) {
              controller.enqueue(new TextEncoder().encode(`${stream}\n\n`));
              controller.close();
            },
          }),
          json: () => Promise.resolve(result),
        });
      }
      return Promise.resolve(jsonResponse({}));
    }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("RC-234 GUI workflow", () => {
  it("keeps the two onboarding entries and major workflow routes reachable", async () => {
    window.history.replaceState({}, "", "/onboarding");
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(jsonResponse({ status: "ok" }))));
    const onboarding = render(<App />);

    expect(await screen.findByRole("heading", { name: "Start Rabbit Code." })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /USE API/i })).toHaveAttribute(
      "href",
      "/workspace/providers?entry=api",
    );
    expect(screen.getByRole("link", { name: /NO API/i })).toHaveAttribute(
      "href",
      "/workspace/models?entry=local",
    );
    onboarding.unmount();

    const routes = [
      ["/workspace/providers", "complementary", "Providers"],
      ["/workspace/models", "region", "Hardware readiness"],
      ["/workspace/review", "region", "Diff review"],
      ["/workspace/settings", "complementary", "Settings sections"],
    ] as const;
    for (const [route, role, label] of routes) {
      window.history.replaceState({}, "", route);
      const view = render(<App />);
      expect(await screen.findByRole(role, { name: label })).toBeInTheDocument();
      view.unmount();
    }
  });

  it("runs optimize, compare, adopt, and send through the mocked App Server", async () => {
    window.history.replaceState({}, "", "/workspace");
    installWorkflowFetch();
    render(<App />);

    const composer = await screen.findByRole("textbox", { name: "提示词输入" });
    fireEvent.change(composer, { target: { value: "原始提示词" } });
    fireEvent.click(screen.getByRole("button", { name: "优化输入内容" }));

    const preview = await screen.findByRole("textbox", { name: "Optimized prompt preview" });
    expect(preview).toHaveValue("优化后的提示词");
    fireEvent.change(preview, { target: { value: "采用后的提示词" } });
    fireEvent.click(screen.getByRole("button", { name: "REPLACE ALL" }));

    expect(screen.getByRole("textbox", { name: "提示词输入" })).toHaveValue("采用后的提示词");
    fireEvent.click(screen.getByRole("button", { name: "发送" }));
    await waitFor(() => expect(screen.getByText("优化完成")).toBeInTheDocument());
    expect(screen.getByRole("status")).toHaveAttribute("aria-live", "polite");
  });
});

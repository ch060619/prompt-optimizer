import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { api } from "../src/api";

type MockResponse = {
  ok: boolean;
  body?: ReadableStream<Uint8Array>;
  json: () => Promise<unknown>;
};

const analysis = {
  prompt: "测试提示词",
  optimized_prompt: "优化后的提示词",
  score: { total_score: 88, dimensions: [] },
  suggestions: [],
  strengths: [],
  created_at: "2026-07-18T00:00:00Z",
};

function response(payload: unknown): Promise<MockResponse> {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(payload) });
}

function optimizeResponse(versionId: number | null = null) {
  return {
    version_id: versionId,
    analysis,
    metadata: {
      provider_requested: "offline",
      provider_used: "offline",
      provider_display_name: "离线规则",
      model: null,
      execution_location: "local",
      credential_ref: null,
      fallback_used: false,
      latency_ms: 1,
      error_summary: null,
      error_code: null,
    },
  };
}

type HistoryItem = {
  id: number;
  original_preview: string;
  optimized_preview: string;
  score: number;
  created_at: string;
  accepted: boolean;
  accepted_at: string | null;
  provider_used: string;
  model: string;
};

function visitWorkspace() {
  window.history.replaceState({}, "", "/workspace?workspace=rc146");
  api.setToken("rc146-token");
}

afterEach(() => {
  vi.unstubAllGlobals();
  api.setToken(null);
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("RC-146 prompt history persistence", () => {
  it("passes the workspace save setting to regular, stream, and task optimization", async () => {
    visitWorkspace();
    localStorage.setItem("rabbit_code_settings_rc146", JSON.stringify({ savePromptHistory: false }));
    localStorage.setItem("rabbit_code_provider_route_rc146", JSON.stringify({ provider: "openai", model: "gpt-session" }));
    const requestBodies: Record<string, unknown>[] = [];
    const streamPayload = `event: completed\ndata: ${JSON.stringify(optimizeResponse())}\n\n`;
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      if (url === "/api/v1/auth/me") {
        return response({ id: 2, username: "rc146-user", created_at: "2026-07-18T00:00:00Z" });
      }
      if (url.startsWith("/api/v1/templates") || url === "/api/v1/history") {
        return response([]);
      }
      if (url === "/api/v1/optimize") {
        requestBodies.push(JSON.parse(String(init?.body)) as Record<string, unknown>);
        return response(optimizeResponse());
      }
      if (url === "/api/v1/optimize/stream") {
        requestBodies.push(JSON.parse(String(init?.body)) as Record<string, unknown>);
        return Promise.resolve({
          ok: true,
          body: new ReadableStream<Uint8Array>({
            start(controller) {
              controller.enqueue(new TextEncoder().encode(streamPayload));
              controller.close();
            },
          }),
          json: () => Promise.resolve({}),
        });
      }
      if (url === "/api/v1/tasks/optimize") {
        requestBodies.push(JSON.parse(String(init?.body)) as Record<string, unknown>);
        return response({ task_id: "rc146-task", status: "succeeded" });
      }
      if (url === "/api/v1/tasks/rc146-task") {
        return response({ id: "rc146-task", kind: "optimize", status: "succeeded" });
      }
      if (url === "/api/v1/tasks/rc146-task/result") {
        return response(optimizeResponse());
      }
      return response({});
    }));

    render(<App />);
    const optimize = await screen.findByRole("button", { name: "优化输入内容" });
    fireEvent.click(optimize);
    expect(await screen.findByRole("textbox", { name: "Optimized prompt preview" })).toHaveValue("优化后的提示词");
    fireEvent.click(screen.getByText("流式优化"));
    expect(await screen.findByText("优化完成")).toBeInTheDocument();
    fireEvent.click(screen.getByText("后台优化"));
    await screen.findByText("optimize · succeeded");

    expect(requestBodies).toHaveLength(3);
    expect(requestBodies.every((body) => body.save_prompt_history === false)).toBe(true);
    expect(requestBodies.every((body) => body.provider === "openai" && body.model === "gpt-session")).toBe(true);
  });

  it("accepts full and partial adoption, displays metadata, and deletes the history row", async () => {
    visitWorkspace();
    const history: HistoryItem = { id: 7, original_preview: "原始提示词", optimized_preview: "优化结果", score: 88, created_at: "2026-07-18T00:00:00Z", accepted: false, accepted_at: null, provider_used: "openai", model: "gpt-test" };
    let nextVersion = 7;
    let currentHistory: HistoryItem[] = [history];
    const acceptedIds: number[] = [];
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      if (url === "/api/v1/auth/me") {
        return response({ id: 2, username: "rc146-user", created_at: "2026-07-18T00:00:00Z" });
      }
      if (url.startsWith("/api/v1/templates")) {
        return response([]);
      }
      if (url === "/api/v1/history" && init?.method === "GET") {
        return response(currentHistory);
      }
      if (url === "/api/v1/optimize") {
        const versionId = nextVersion++;
        currentHistory = [{ ...history, id: versionId }];
        return response({ ...optimizeResponse(versionId), metadata: { ...optimizeResponse(versionId).metadata, provider_used: "openai", model: "gpt-test" } });
      }
      const acceptMatch = url.match(/^\/api\/v1\/history\/(\d+)\/accept$/);
      if (acceptMatch) {
        const versionId = Number(acceptMatch[1]);
        acceptedIds.push(versionId);
        currentHistory = currentHistory.map((item) => item.id === versionId ? { ...item, accepted: true, accepted_at: "2026-07-18T00:00:00Z" } : item);
        return response({ ...history, id: versionId, accepted: true, accepted_at: "2026-07-18T00:00:00Z" });
      }
      const deleteMatch = url.match(/^\/api\/v1\/history\/(\d+)$/);
      if (deleteMatch && init?.method === "DELETE") {
        currentHistory = currentHistory.filter((item) => item.id !== Number(deleteMatch[1]));
        return response({});
      }
      return response({});
    }));

    render(<App />);
    expect(await screen.findByText("openai · gpt-test")).toBeInTheDocument();
    const optimize = screen.getByRole("button", { name: "优化输入内容" });
    fireEvent.click(optimize);
    await screen.findByRole("textbox", { name: "Optimized prompt preview" });
    fireEvent.click(screen.getByRole("button", { name: "REPLACE ALL" }));
    await waitFor(() => expect(acceptedIds).toEqual([7]));
    expect(await screen.findByText(/#7 · 88 · 已采用/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "删除版本 7" }));
    await waitFor(() => expect(screen.queryByText(/#7 · 88/)).not.toBeInTheDocument());

    fireEvent.click(optimize);
    await screen.findByRole("textbox", { name: "Optimized prompt preview" });
    fireEvent.click(screen.getByRole("button", { name: "Diff line 1" }));
    fireEvent.click(screen.getByRole("button", { name: "REPLACE SELECTED" }));
    await waitFor(() => expect(acceptedIds).toEqual([7, 8]));
  });
});

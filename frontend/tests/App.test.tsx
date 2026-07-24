import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { api } from "../src/api";

// RC ID: RC-058. Verify the GUI uses the versioned App Server paths.

// RC ID: RC-050. Verify the UI identifies offline rules instead of a model.
// RC ID: RC-054. Verify the public UI uses the Rabbit Code identity.

function stubFetch(handler?: (url: string) => Promise<ResponseLike>) {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (handler) {
        return handler(url);
      }
  if (url.startsWith("/api/v1/templates")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([])
        });
      }
  if (url === "/api/v1/history") {
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
  api.setToken(null);
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

function visitWorkspace() {
  window.history.replaceState({}, "", "/workspace");
}

describe("App", () => {
  it("renders the home page without the workspace controls", async () => {
    render(<App />);
    expect(screen.getByRole("link", { name: "Rabbit Code home" })).toBeInTheDocument();
    expect(screen.queryByText("优化并保存")).not.toBeInTheDocument();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("renders the local workspace on its dedicated route", async () => {
    visitWorkspace();
    stubFetch();
    render(<App />);
    expect(await screen.findByRole("link", { name: "Rabbit Code home" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "优化输入内容" })).toBeInTheDocument();
  });

  it("keeps empty optimization disabled and does not confuse it with send", async () => {
    visitWorkspace();
    const fetchMock = vi.fn((url: string) => {
      if (url.startsWith("/api/v1/templates") || url === "/api/v1/history") {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    const optimize = await screen.findByRole("button", { name: "优化输入内容" });
    const send = screen.getByRole("button", { name: "发送" });
    expect(optimize).toBeDisabled();
    expect(send).toBeDisabled();
    fireEvent.click(optimize);
    expect(fetchMock.mock.calls.some(([url]) => url === "/api/v1/optimize")).toBe(false);
  });

  it("locks one optimization request and keeps the current prompt when it completes", async () => {
    visitWorkspace();
    const result = {
      version_id: null,
      analysis: {
        prompt: "保留原始输入",
        optimized_prompt: "优化预览",
        score: { total_score: 80, dimensions: [] },
        suggestions: [],
        strengths: [],
        created_at: "2026-06-15T00:00:00Z",
      },
      metadata: {
        provider_requested: "offline",
        provider_used: "offline",
        fallback_used: false,
        latency_ms: 1,
        error_summary: null,
      },
    };
    let resolveOptimize!: (response: ResponseLike) => void;
    let optimizeCalls = 0;
    stubFetch((url: string) => {
      if (url.startsWith("/api/v1/templates") || url === "/api/v1/history") {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      if (url === "/api/v1/optimize") {
        optimizeCalls += 1;
        return new Promise<ResponseLike>((resolve) => { resolveOptimize = resolve; });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    render(<App />);

    const composer = screen.getByRole("textbox", { name: "提示词输入" });
    fireEvent.change(composer, { target: { value: "保留原始输入", selectionStart: 6, selectionEnd: 6 } });
    const optimize = screen.getByRole("button", { name: "优化输入内容" });
    await waitFor(() => expect(optimize).not.toBeDisabled());
    fireEvent.click(optimize);
    await waitFor(() => expect(optimizeCalls).toBe(1));
    expect(optimizeCalls).toBe(1);
    expect(screen.getByRole("button", { name: "发送" })).toBeDisabled();

    resolveOptimize({ ok: true, json: () => Promise.resolve(result) });
    expect(await screen.findByRole("textbox", { name: "Optimized prompt preview" })).toHaveValue("优化预览");
    expect(screen.getByRole("textbox", { name: "提示词输入" })).toHaveValue("保留原始输入");
  });

  it("uses Sparkles only on prompt optimization actions", async () => {
    visitWorkspace();
    stubFetch();
    render(<App />);

    const optimize = await screen.findByRole("button", { name: "优化输入内容" });
    expect(optimize).toHaveAttribute("data-tooltip", "优化输入内容");
    expect(optimize.querySelector("svg")).toHaveClass("lucide-sparkles");
    expect(screen.getByRole("button", { name: "分析" })).toHaveAttribute("title", "分析提示词");
    expect(screen.getByRole("button", { name: "分析" }).querySelector("svg")).toHaveClass("lucide-search");
  });

  it("keeps the full-screen navigation keyboard reachable", () => {
    render(<App />);
    const trigger = screen.getByRole("button", { name: "Open navigation" });
    fireEvent.click(trigger);

    const menu = screen.getByRole("dialog", { name: "Full-screen navigation" });
    const menuLinks = within(menu).getAllByRole("link");
    const menuButtons = within(menu).getAllByRole("button");
    const focusable = [...menuLinks, ...menuButtons];
    focusable[focusable.length - 1].focus();
    fireEvent.keyDown(menu, { key: "Tab" });
    expect(document.activeElement).toBe(focusable[0]);

    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog", { name: "Full-screen navigation" })).not.toBeInTheDocument();
    expect(document.activeElement).toBe(trigger);
  });

  it("renders a dedicated login page", () => {
    window.history.replaceState({}, "", "/login");
    render(<App />);
    expect(screen.getByRole("heading", { name: "Welcome back." })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "LOGIN" })).toBeInTheDocument();
  });

  it("renders a dedicated registration page", () => {
    window.history.replaceState({}, "", "/register");
    render(<App />);
    expect(screen.getByRole("heading", { name: "Start a local record." })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "CREATE ACCOUNT" })).toBeInTheDocument();
  });

  it("removes the footer while keeping a rabbit on marketing pages", () => {
    window.history.replaceState({}, "", "/contact");
    render(<App />);
    expect(screen.queryByRole("contentinfo")).not.toBeInTheDocument();
    expect(screen.getByRole("img", { name: "PromptLayer 风格复古版画兔兔插画" })).toBeInTheDocument();
  });

  it("shows initialization errors from the API", async () => {
    visitWorkspace();
    stubFetch((url: string) => {
  if (url.startsWith("/api/v1/templates")) {
        return Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ detail: "模板加载失败" })
        });
      }
  if (url === "/api/v1/history") {
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
    visitWorkspace();
    const analysis = {
      prompt: "帮我写销售话术",
      optimized_prompt: null,
      score: { total_score: 70, dimensions: [] },
      suggestions: [],
      strengths: [],
      created_at: "2026-06-15T00:00:00Z"
    };
    stubFetch((url: string) => {
  if (url.startsWith("/api/v1/templates")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
  if (url === "/api/v1/history") {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
  if (url === "/api/v1/optimize/stream") {
        const payload = [
          `event: started\ndata: {"provider":"offline"}`,
          `event: analysis\ndata: ${JSON.stringify(analysis)}`,
          `event: chunk\ndata: {"text":"优化后的提示词"}`,
          `event: completed\ndata: ${JSON.stringify({
            version_id: null,
            analysis: { ...analysis, optimized_prompt: "优化后的提示词" },
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
               error_code: null
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
    expect(screen.getByRole("region", { name: "Optimization metadata" })).toHaveTextContent("离线规则");
    expect(screen.getByRole("region", { name: "Optimization metadata" })).toHaveTextContent("本地");
    expect(screen.getByRole("region", { name: "Optimization metadata" })).toHaveTextContent("未降级");
    expect(screen.getByRole("status")).toHaveAttribute("aria-live", "polite");
  });

  it("triggers optimization from the configurable default keyboard shortcut", async () => {
    visitWorkspace();
    const analysis = {
      prompt: "快捷键测试",
      optimized_prompt: "快捷键优化结果",
      score: { total_score: 80, dimensions: [] },
      suggestions: [],
      strengths: [],
      created_at: "2026-06-15T00:00:00Z"
    };
    stubFetch((url: string) => {
      if (url === "/api/v1/optimize") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            version_id: null,
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
              error_code: null
            }
          })
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
    });
    render(<App />);
    fireEvent.change(screen.getByRole("textbox", { name: "提示词输入" }), { target: { value: "快捷键测试" } });
    await screen.findByRole("button", { name: "优化输入内容" });

    fireEvent.keyDown(document, { key: "o", ctrlKey: true, shiftKey: true });

    expect(await screen.findByRole("textbox", { name: "Optimized prompt preview" })).toHaveValue("快捷键优化结果");
  });

  it("does not overwrite edited input when an optimization response arrives late", async () => {
    visitWorkspace();
    const result = {
      version_id: null,
      analysis: {
        prompt: "旧输入",
        optimized_prompt: "旧快照的优化结果",
        score: { total_score: 88, dimensions: [] },
        suggestions: [],
        strengths: [],
        created_at: "2026-06-15T00:00:00Z"
      },
      metadata: {
        provider_requested: "offline",
        provider_used: "offline",
        fallback_used: false,
        latency_ms: 1,
        error_summary: null
      }
    };
    let resolveOptimize!: (response: ResponseLike) => void;
    stubFetch((url: string) => {
      if (url.startsWith("/api/v1/templates") || url === "/api/v1/history") {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      if (url === "/api/v1/optimize") {
        return new Promise<ResponseLike>((resolve) => { resolveOptimize = resolve; });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    render(<App />);

    const optimize = await screen.findByRole("button", { name: "优化输入内容" });
    const composer = screen.getByRole("textbox", { name: "提示词输入" });
    fireEvent.change(composer, { target: { value: "旧输入", selectionStart: 3, selectionEnd: 3 } });
    fireEvent.click(optimize);
    await waitFor(() => expect(resolveOptimize).toBeTypeOf("function"));
    fireEvent.change(composer, { target: { value: "用户已经编辑的新输入", selectionStart: 10, selectionEnd: 10 } });
    resolveOptimize({ ok: true, json: () => Promise.resolve(result) });

    expect(await screen.findByRole("status", { name: "Optimization result ready" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "提示词输入" })).toHaveValue("用户已经编辑的新输入");
    expect(screen.queryByRole("textbox", { name: "Optimized prompt preview" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "查看比较" }));
    expect(await screen.findByRole("textbox", { name: "Optimized prompt preview" })).toHaveValue("旧快照的优化结果");
  });

  it("keeps optimization as an editable preview until the user adopts it", async () => {
    visitWorkspace();
    let taskCalls = 0;
    const result = {
      version_id: null,
      analysis: {
        prompt: "原始输入",
        optimized_prompt: "可编辑的优化结果",
        score: { total_score: 90, dimensions: [] },
        suggestions: [],
        strengths: [],
        created_at: "2026-06-15T00:00:00Z"
      },
      metadata: {
        provider_requested: "offline",
        provider_used: "offline",
        fallback_used: false,
        latency_ms: 1,
        error_summary: null
      }
    };
    stubFetch((url: string) => {
      if (url.startsWith("/api/v1/templates") || url === "/api/v1/history") {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      if (url === "/api/v1/optimize") {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(result) });
      }
      if (url.startsWith("/api/v1/tasks")) {
        taskCalls += 1;
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    render(<App />);

    const composer = screen.getByRole("textbox", { name: "提示词输入" });
    fireEvent.change(composer, { target: { value: "原始输入", selectionStart: 4, selectionEnd: 4 } });
    fireEvent.click(await screen.findByRole("button", { name: "优化输入内容" }));
    const preview = await screen.findByRole("textbox", { name: "Optimized prompt preview" });
    expect(preview).toHaveValue("可编辑的优化结果");
    expect(taskCalls).toBe(0);
    fireEvent.change(preview, { target: { value: "用户确认后的结果" } });
    fireEvent.click(screen.getByRole("button", { name: "REPLACE ALL" }));
    expect(screen.getByRole("textbox", { name: "提示词输入" })).toHaveValue("用户确认后的结果");
    expect(screen.queryByRole("textbox", { name: "Optimized prompt preview" })).not.toBeInTheDocument();
  });

  it("redacts secret-bearing provider errors before rendering metadata", async () => {
    visitWorkspace();
    const result = {
      version_id: null,
      analysis: {
        prompt: "原始输入",
        optimized_prompt: "安全的优化结果",
        score: { total_score: 90, dimensions: [] },
        suggestions: [],
        strengths: [],
        created_at: "2026-06-15T00:00:00Z"
      },
      metadata: {
        provider_requested: "openai",
        provider_used: "offline",
        provider_display_name: "离线规则",
        model: null,
        execution_location: "local",
        credential_ref: null,
        fallback_used: true,
        latency_ms: 4,
        error_summary: "api_key=sk-live-1234567890abcdef system_prompt=hidden source",
        error_code: "PROVIDER_ERROR",
        fallback_reason: "not_ready",
        recovery_action: "repair"
      }
    };
    stubFetch((url: string) => {
      if (url.startsWith("/api/v1/templates") || url === "/api/v1/history") {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      if (url === "/api/v1/optimize") {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(result) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    render(<App />);

    fireEvent.change(screen.getByRole("textbox", { name: "提示词输入" }), { target: { value: "原始输入" } });
    fireEvent.click(await screen.findByRole("button", { name: "优化输入内容" }));

    const metadata = await screen.findByRole("region", { name: "Optimization metadata" });
    expect(metadata).toHaveTextContent("Provider error details were redacted.");
    expect(metadata).not.toHaveTextContent("sk-live-1234567890abcdef");
    expect(metadata).not.toHaveTextContent("system_prompt");
    expect(metadata).toHaveTextContent("PROVIDER_ERROR");
    expect(metadata).toHaveTextContent("未就绪");
    expect(screen.getByRole("link", { name: "安装或修复本地模型" })).toHaveAttribute("href", "/workspace/models");
  });

  it("registers and stores an authenticated user", async () => {
    window.history.replaceState({}, "", "/register");
    let sawAuthHeader = false;
    stubFetch((url: string) => {
  if (url.startsWith("/api/v1/templates")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
  if (url === "/api/v1/auth/register") {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              access_token: "token-1",
              token_type: "bearer",
              user: { id: 2, username: "demo-user", created_at: "2026-06-15T00:00:00Z" }
            })
        });
      }
  if (url === "/api/v1/history") {
        const calls = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls;
        const headers = calls[calls.length - 1]?.[1]?.headers as Record<string, string> | undefined;
        sawAuthHeader = headers?.Authorization === "Bearer token-1";
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "CREATE ACCOUNT" }));

    expect(await screen.findByText(/Signed in as demo-user/)).toBeInTheDocument();
    expect(sawAuthHeader).toBe(true);
  });

  it("runs an optimize background task", async () => {
    visitWorkspace();
    const analysis = {
      prompt: "帮我写销售话术",
      optimized_prompt: "后台优化后的提示词",
      score: { total_score: 80, dimensions: [] },
      suggestions: [],
      strengths: [],
      created_at: "2026-06-15T00:00:00Z"
    };
    stubFetch((url: string) => {
  if (url.startsWith("/api/v1/templates")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
  if (url === "/api/v1/history") {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
  if (url === "/api/v1/auth/me") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 1, username: "task-user", created_at: "2026-06-15T00:00:00Z" })
        });
      }
  if (url === "/api/v1/tasks/optimize") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ task_id: "task-1", status: "queued" })
        });
      }
  if (url === "/api/v1/tasks/task-1") {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              id: "task-1",
              owner_id: 1,
              kind: "optimize",
              status: "succeeded",
              created_at: "2026-06-15T00:00:00Z",
              updated_at: "2026-06-15T00:00:00Z"
            })
        });
      }
  if (url === "/api/v1/tasks/task-1/result") {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              version_id: 1,
              analysis,
              metadata: {
                provider_requested: "offline",
                provider_used: "offline",
                fallback_used: false,
                latency_ms: 1
              }
            })
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    api.setToken("token-task");
    render(<App />);

    await screen.findByText("task-user");
    fireEvent.click(screen.getByText("后台优化"));

    expect(await screen.findByText("optimize · succeeded")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Optimized prompt preview" })).toHaveValue("后台优化后的提示词");
  });
});

import { render, screen } from "@testing-library/react";
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
});

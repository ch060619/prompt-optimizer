import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

// RC ID: RC-249. Preserve the composer draft, revision, and cursor through provider failures and refresh.

function visitWorkspace() {
  window.history.replaceState({}, "", "/workspace?workspace=rc249");
}

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("composer draft protection", () => {
  it("restores the draft and cursor after a failed optimization", async () => {
    visitWorkspace();
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/templates") || url.endsWith("/history")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      if (url.endsWith("/optimize")) {
        return Promise.resolve({ ok: false, json: () => Promise.resolve({ detail: "mock provider unavailable" }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));

    const first = render(<App />);
    const input = await screen.findByRole("textbox", { name: "提示词输入" });
    fireEvent.change(input, {
      target: { value: "保留这段草稿", selectionStart: 5, selectionEnd: 5 },
    });
    fireEvent.click(screen.getByRole("button", { name: "优化输入内容" }));
    await waitFor(() => expect(screen.getByText("mock provider unavailable")).toBeInTheDocument());

    const saved = JSON.parse(localStorage.getItem("rabbit_code_prompt_draft_rc249") || "{}");
    expect(saved.text).toBe("保留这段草稿");
    expect(saved.cursor).toEqual({ start: 5, end: 5 });
    expect(saved.revision).toBeGreaterThan(0);

    first.unmount();
    render(<App />);
    expect(await screen.findByRole("textbox", { name: "提示词输入" })).toHaveValue("保留这段草稿");
  });
});

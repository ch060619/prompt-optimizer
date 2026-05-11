import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

vi.stubGlobal(
  "fetch",
  vi.fn((url: string) => {
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

describe("App", () => {
  it("renders the local workspace", async () => {
    render(<App />);
    expect(await screen.findByText("Prompt Optimizer")).toBeInTheDocument();
    expect(screen.getByText("优化并保存")).toBeInTheDocument();
  });
});


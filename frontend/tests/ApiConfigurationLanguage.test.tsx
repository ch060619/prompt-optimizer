import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

// RC ID: RC-159. Keep provider API configuration distinct from Rabbit Code account login.

afterEach(() => {
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
  localStorage.clear();
});

describe("API configuration language", () => {
  it("labels the first-run route as provider configuration", async () => {
    window.history.replaceState({}, "", "/onboarding");
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response("{}", { status: 200 }))));

    render(<App />);

    expect(await screen.findByRole("link", { name: /USE API \/ CONFIGURE PROVIDER/i })).toBeInTheDocument();
    expect(screen.getByText(/PROVIDER CREDENTIAL, NOT RABBIT CODE/i)).toBeInTheDocument();
  });

  it("describes provider keys without calling them account login credentials", () => {
    window.history.replaceState({}, "", "/workspace/providers");
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Add provider" }));

    expect(screen.getByText(/not Rabbit Code account passwords/i)).toBeInTheDocument();
    expect(screen.getByText("PROVIDER API KEY")).toBeInTheDocument();
    expect(screen.getByText("PROVIDER KEY ONLY / NOT ACCOUNT LOGIN")).toBeInTheDocument();
  });

  it("keeps actual account authentication explicitly named as account login", () => {
    window.history.replaceState({}, "", "/login");
    render(<App />);

    expect(screen.getByText("ACCOUNT LOGIN")).toBeInTheDocument();
  });
});

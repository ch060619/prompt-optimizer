import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "../src/App";

// RC ID: RC-116. Verify search/filter, pagination, favorites, compare, import/export, and Composer handoff.

function visitAssets() {
  window.history.replaceState({}, "", "/workspace/assets");
}

afterEach(() => {
  window.history.replaceState({}, "", "/");
});

describe("prompt assets", () => {
  it("renders searchable, filterable, paginated assets and favorite state", () => {
    visitAssets();
    render(<App />);

    expect(screen.getByRole("complementary", { name: "Prompt templates" })).toHaveTextContent("Product release email");
    expect(screen.getByRole("button", { name: "Next asset page" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Next asset page" }));
    expect(screen.getByText("User research plan")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("searchbox", { name: "Search prompt assets" }), { target: { value: "API" } });
    expect(screen.getByText("API design brief")).toBeInTheDocument();
    expect(screen.queryByText("User research plan")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Remove favorite" }));
    expect(screen.getByRole("button", { name: "Add favorite" })).toBeInTheDocument();
  });

  it("compares history, imports safely, exports, and hands off without sending", () => {
    visitAssets();
    render(<App />);

    fireEvent.click(screen.getByRole("tab", { name: "HISTORY" }));
    fireEvent.click(screen.getAllByRole("button", { name: /COMPARE/i })[0]);
    expect(screen.getByRole("region", { name: "Version comparison" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Close version comparison" }));
    fireEvent.click(screen.getByRole("button", { name: "Open import dialog" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Import JSON" }), { target: { value: "not-json" } });
    fireEvent.click(screen.getByRole("button", { name: /IMPORT ASSET/i }));
    expect(screen.getByText("IMPORT REJECTED / LIST UNCHANGED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open import dialog" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Import JSON" }), { target: { value: JSON.stringify({ title: "Imported prompt", prompt: "Use this prompt later.", category: "general" }) } });
    fireEvent.click(screen.getByRole("button", { name: /IMPORT ASSET/i }));
    expect(screen.getByText("Imported prompt")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /USE IN COMPOSER/i })).toHaveAttribute("href", expect.stringContaining("/workspace?template="));
    fireEvent.click(screen.getByRole("button", { name: /EXPORT JSON/i }));
    expect(screen.getByText("ASSET EXPORTED")).toBeInTheDocument();
  });
});

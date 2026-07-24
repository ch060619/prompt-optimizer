import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { AppLink, canonicalPath, NavigationProvider, useNavigation } from "../src/navigation";

function Probe() {
  const { pathname, search } = useNavigation();
  return (
    <>
      <output aria-label="location">{pathname}{search}</output>
      <AppLink href="/prompt-management?workspace=demo">Legacy workspace</AppLink>
      <AppLink href="https://example.com" target="_blank">External</AppLink>
    </>
  );
}

afterEach(() => {
  window.history.replaceState({}, "", "/");
});

describe("navigation contract", () => {
  it("canonicalizes former prompt-site routes without a reload", async () => {
    window.history.replaceState({}, "", "/prompt-management");
    render(<NavigationProvider><Probe /></NavigationProvider>);

    expect(canonicalPath("/prompt-management")).toBe("/workspace/assets");
    expect(screen.getByRole("link", { name: "Legacy workspace" })).toHaveAttribute(
      "href",
      "/prompt-management?workspace=demo",
    );
    fireEvent.click(screen.getByRole("link", { name: "Legacy workspace" }));

    await waitFor(() => expect(screen.getByLabelText("location")).toHaveTextContent("/workspace/assets?workspace=demo"));
    expect(window.location.pathname).toBe("/workspace/assets");
  });

  it("leaves external links to the browser", () => {
    render(<NavigationProvider><Probe /></NavigationProvider>);
    const external = screen.getByRole("link", { name: "External" });
    expect(external).toHaveAttribute("href", "https://example.com");
    expect(external).toHaveAttribute("target", "_blank");
    expect(window.location.pathname).toBe("/");
  });
});

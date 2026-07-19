import { render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "../src/App";

// RC ID: RC-125. Keep every independent workspace route on an explicit RabbitMark slot.
// RC ID: RC-128. Route slots use the dedicated SVG for mark and mono variants.
// RC ID: RC-129. Route artwork remains decorative and outside interactive content.

const routes = [
  ["/workspace/home", "empty"],
  ["/workspace/task", "mark"],
  ["/workspace/review", "mark"],
  ["/workspace/terminal", "mono"],
  ["/workspace/providers", "mark"],
  ["/workspace/models", "mark"],
  ["/workspace/assets", "mark"],
  ["/workspace/settings", "mark"],
  ["/workspace/diagnostics", "mark"],
] as const;

afterEach(() => {
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("RabbitMark route slots", () => {
  it.each(routes)("renders the %s route with the %s variant", (route, variant) => {
    window.history.replaceState({}, "", route);
    render(<App />);

    const slot = document.querySelector(`.route-rabbit-slot-${variant}`);
    expect(slot).not.toBeNull();
    expect(slot).toHaveAttribute("aria-hidden", "true");
    expect(slot).toHaveAttribute("data-rabbit-layer", "decorative");
    expect(slot?.querySelector("button")).toBeNull();
    if (variant === "empty") {
      expect(slot?.querySelector("img")).toHaveAttribute("src", "/rabbit-artwork.png");
    } else {
      expect(slot?.querySelector("svg")).toHaveAttribute("viewBox", "0 0 64 64");
      expect(slot?.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
    }
  });
});

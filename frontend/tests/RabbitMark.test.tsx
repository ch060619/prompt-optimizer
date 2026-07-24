import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RabbitMark } from "../src/components/RabbitMark";

// RC ID: RC-125. Verify variants use the internal asset boundary and accessible labels.
// RC ID: RC-128. Verify dedicated small marks at required display sizes.

describe("RabbitMark", () => {
  it("renders every supported variant from the fixed internal asset path", () => {
    const { container } = render(
      <div>
        {(["full", "avatar", "mark", "empty", "mono", "desktop"] as const).map((variant) => (
          <RabbitMark key={variant} variant={variant} alt={`${variant} mark`} />
        ))}
      </div>,
    );

    expect(container.querySelectorAll("img")).toHaveLength(4);
    expect(Array.from(container.querySelectorAll("img")).map((image) => image.getAttribute("src"))).toEqual([
      "/rabbit-artwork.png",
      "/rabbit-artwork.png",
      "/rabbit-artwork.png",
      "/rabbit-desktop.png",
    ]);
    expect(container.querySelectorAll("svg")).toHaveLength(2);
    expect(screen.getByAltText("full mark")).toBeInTheDocument();
  });

  it("supports decorative slots without adding a second screen-reader label", () => {
    const { container } = render(<RabbitMark variant="mark" decorative />);
    const icon = container.querySelector("svg");
    expect(icon).not.toBeNull();
    expect(icon).toHaveAttribute("aria-hidden", "true");
    expect(icon).toHaveAttribute("role", "presentation");
  });

  it("uses a dedicated SVG mark at every required small size on light and dark surfaces", () => {
    for (const theme of ["light", "dark"] as const) {
      const { container, unmount } = render(
        <div data-theme={theme} style={{ background: theme === "light" ? "#faf5eb" : "#1c1b18" }}>
          {[16, 20, 24, 32].map((size) => (
            <RabbitMark key={`${theme}-${size}`} variant="mark" size={size} alt={`${theme} ${size}px mark`} />
          ))}
          <RabbitMark variant="mono" size={16} alt={`${theme} mono`} />
        </div>,
      );

      const icons = Array.from(container.querySelectorAll("svg"));
      expect(icons).toHaveLength(5);
      expect(icons.slice(0, 4).map((icon) => icon.getAttribute("width"))).toEqual(["16", "20", "24", "32"]);
      expect(icons.every((icon) => icon.getAttribute("viewBox") === "0 0 64 64")).toBe(true);
      expect(container.querySelectorAll("img")).toHaveLength(0);
      unmount();
    }
  });

  it("keeps decorative SVG marks out of the accessibility tree", () => {
    const { container } = render(<RabbitMark variant="mono" decorative size={20} />);
    expect(container.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
    expect(container.querySelector("svg")).toHaveAttribute("role", "presentation");
  });
});

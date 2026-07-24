import { fireEvent, render, screen } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { PermissionDialog } from "../src/components/UiStates";

// RC ID: RC-236. Keep critical/serious axe findings and keyboard regressions visible in CI.

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

function stubHealth() {
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ status: "ok" }) })));
}

async function expectNoSeriousAxeFindings(container: HTMLElement) {
  const result = await axe.run(container, {
    rules: {
      "color-contrast": { enabled: false },
    },
  });
  expect(result.violations.filter((violation) => ["critical", "serious"].includes(violation.impact || ""))).toEqual([]);
}

describe("RC-236 accessibility", () => {
  it("runs axe against the workspace and settings shells", async () => {
    stubHealth();
    window.history.replaceState({}, "", "/workspace");
    const workspace = render(<App />);
    await screen.findByRole("textbox", { name: "提示词输入" });
    await expectNoSeriousAxeFindings(workspace.container);
    workspace.unmount();

    window.history.replaceState({}, "", "/workspace/settings?workspace=rc236");
    const settings = render(<App />);
    await screen.findByRole("complementary", { name: "Settings sections" });
    await expectNoSeriousAxeFindings(settings.container);
  });

  it("keeps keyboard focus in the permission dialog and restores the trigger", () => {
    function Harness() {
      return <PermissionDialog open title="Permission required" description="The workspace needs access." onClose={() => undefined} onConfirm={() => undefined} />;
    }

    render(
      <>
        <button type="button">Open permission dialog</button>
        <Harness />
      </>,
    );
    const dialog = screen.getByRole("alertdialog", { name: "Permission required" });
    const close = screen.getByRole("button", { name: "Close dialog" });
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAttribute("aria-describedby");
    close.focus();
    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).not.toBe(document.body);
  });
});

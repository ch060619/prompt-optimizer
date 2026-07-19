import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { EmptyState, ErrorState, InstallDialog, OfflineState, PermissionDialog } from "../src/components/UiStates";

// RC ID: RC-119. Verify the shared state vocabulary and accessible dialog behavior.

const approvalRequest = {
  approval_id: "approval-1",
  request_id: "request-1",
  action: "terminal.exec",
  description: "Run a local command",
  risk: "high" as const,
  tool: "terminal.exec",
  command: ["python", "-c", "print(1)"],
  paths: ["C:/workspace/output.txt"],
  workdir: "C:/workspace",
  impact: "starts one local process",
  authorization_scope: "once",
  arguments: { command: ["python", "-c", "print(1)"] },
  snapshot: "snapshot",
  expires_at: null,
};

const stateVariants = {
  empty: <EmptyState title="NO PROJECTS" description="Open a directory to start." />,
  error: <ErrorState title="PROJECT SERVICE UNAVAILABLE" description="Try the request again." primaryAction={{ label: "RETRY" }} />,
  offline: <OfflineState title="OFFLINE MODE" description="This route stays on the machine." />,
  permission: <PermissionDialog open title="Allow workspace access?" description="The action needs workspace permission." approvalRequest={approvalRequest} onClose={() => undefined} onConfirm={() => undefined} />,
  install: <InstallDialog open title="Install local model?" description="The download will be verified before use." onClose={() => undefined} onConfirm={() => undefined} />,
};

describe("shared UI states", () => {
  it.each(Object.entries(stateVariants))("renders the %s variant", (_name, variant) => {
    const { container } = render(variant);
    expect(container.firstChild).toMatchSnapshot();
  });

  it("keeps dialog focus inside, closes on Escape, and restores the trigger focus", () => {
    function Harness() {
      const [open, setOpen] = useState(false);
      return (
        <>
          <button type="button" onClick={() => setOpen(true)}>Open permission dialog</button>
          <PermissionDialog
            open={open}
            title="Allow workspace access?"
            description="The action needs workspace permission."
            onClose={() => setOpen(false)}
            onConfirm={() => setOpen(false)}
          />
        </>
      );
    }

    render(<Harness />);
    const trigger = screen.getByRole("button", { name: "Open permission dialog" });
    trigger.focus();
    fireEvent.click(trigger);

    const dialog = screen.getByRole("alertdialog", { name: "Allow workspace access?" });
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Close dialog" }));

    const dialogButtons = screen.getAllByRole("button").filter((button) => dialog.contains(button));
    dialogButtons[dialogButtons.length - 1].focus();
    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).toBe(dialogButtons[0]);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(document.activeElement).toBe(trigger);
  });

  it("exposes permission and install actions with screen-reader descriptions", () => {
    const onConfirm = vi.fn();
    render(
      <>
        <PermissionDialog open title="Permission required" description="The workspace needs access." onClose={() => undefined} onConfirm={onConfirm} />
        <InstallDialog open title="Install required" description="The model is not installed." onClose={() => undefined} onConfirm={onConfirm} />
      </>,
    );

    const permission = screen.getByRole("alertdialog", { name: "Permission required" });
    const install = screen.getByRole("dialog", { name: "Install required" });
    expect(permission).toHaveAttribute("aria-describedby");
    expect(install).toHaveAttribute("aria-describedby");
    const confirmButtons = screen.getAllByRole("button", { name: "CONFIRM" });
    expect(confirmButtons).toHaveLength(2);
    fireEvent.click(confirmButtons[0]);
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("shows the complete shared approval request", () => {
    render(
      <PermissionDialog
        open
        title="Permission required"
        description="The workspace needs access."
        approvalRequest={approvalRequest}
        onClose={() => undefined}
        onConfirm={() => undefined}
      />,
    );

    expect(screen.getByText("terminal.exec")).toBeInTheDocument();
    expect(screen.getByText("C:/workspace")).toBeInTheDocument();
    expect(screen.getByText("starts one local process")).toBeInTheDocument();
    expect(screen.getByText("ONCE")).toBeInTheDocument();
  });
});

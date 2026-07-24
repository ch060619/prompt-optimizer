import { AlertTriangle, CircleHelp, Download, Inbox, WifiOff, X, type LucideIcon } from "lucide-react";
import { useEffect, useId, useRef, type ReactNode } from "react";
import type { ApprovalRequest } from "../approval";
import { AppLink } from "../navigation";

// RC ID: RC-119. Keep page states and modal semantics in one UI surface.

export type UiAction = {
  label: string;
  onClick?: () => void;
  href?: string;
  disabled?: boolean;
};

type StateMessageProps = {
  title: string;
  description: ReactNode;
  primaryAction?: UiAction;
  secondaryAction?: UiAction;
  compact?: boolean;
};

function StateMessage({
  kind,
  icon: Icon,
  title,
  description,
  primaryAction,
  secondaryAction,
  compact = false,
}: StateMessageProps & { kind: "empty" | "error" | "offline"; icon: LucideIcon }) {
  const titleId = useId();
  return (
    <section className={`ui-state ui-state-${kind}${compact ? " ui-state-compact" : ""}`} aria-labelledby={titleId}>
      <div className="ui-state-icon" aria-hidden="true"><Icon size={compact ? 18 : 24} /></div>
      <div className="ui-state-copy">
        <h2 id={titleId}>{title}</h2>
        <p>{description}</p>
        {primaryAction || secondaryAction ? (
          <div className="ui-state-actions">
            {primaryAction ? <UiActionButton action={primaryAction} primary /> : null}
            {secondaryAction ? <UiActionButton action={secondaryAction} /> : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}

export function EmptyState(props: StateMessageProps) {
  return <StateMessage {...props} kind="empty" icon={Inbox} />;
}

export function ErrorState(props: StateMessageProps) {
  return <StateMessage {...props} kind="error" icon={AlertTriangle} />;
}

export function OfflineState(props: StateMessageProps) {
  return <StateMessage {...props} kind="offline" icon={WifiOff} />;
}

function UiActionButton({ action, primary = false }: { action: UiAction; primary?: boolean }) {
  const className = primary ? "ui-state-action ui-state-action-primary" : "ui-state-action";
  if (action.href) {
    return <AppLink className={className} href={action.href}>{action.label}</AppLink>;
  }
  return <button className={className} type="button" disabled={action.disabled} onClick={action.onClick}>{action.label}</button>;
}

type DialogProps = {
  open: boolean;
  title: string;
  description: ReactNode;
  onClose: () => void;
  onConfirm?: () => void;
  confirmLabel?: string;
  cancelLabel?: string;
  accessibleName?: string;
  role?: "dialog" | "alertdialog";
  icon?: LucideIcon;
  children?: ReactNode;
  confirmClassName?: string;
  approvalRequest?: ApprovalRequest;
};

export function UiDialog({
  open,
  title,
  description,
  onClose,
  onConfirm,
  confirmLabel = "CONFIRM",
  cancelLabel = "CANCEL",
  accessibleName,
  role = "dialog",
  icon: Icon = CircleHelp,
  children,
  confirmClassName = "",
  approvalRequest,
}: DialogProps) {
  const dialogRef = useRef<HTMLElement>(null);
  const restoreFocusRef = useRef<HTMLElement | null>(null);
  const closeRef = useRef(onClose);
  const confirmRef = useRef(onConfirm);
  const titleId = useId();
  const descriptionId = useId();
  closeRef.current = onClose;
  confirmRef.current = onConfirm;

  useEffect(() => {
    if (!open) {
      return;
    }

    restoreFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const dialog = dialogRef.current;
    const focusable = getFocusable(dialog);
    (focusable[0] ?? dialog)?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeRef.current();
        return;
      }
      if (event.key !== "Tab" || !dialog) {
        return;
      }
      const currentFocusable = getFocusable(dialog);
      if (currentFocusable.length === 0) {
        event.preventDefault();
        dialog.focus();
        return;
      }
      const first = currentFocusable[0];
      const last = currentFocusable[currentFocusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      restoreFocusRef.current?.focus();
      restoreFocusRef.current = null;
    };
  }, [open]);

  if (!open) {
    return null;
  }

  return (
    <div className="ui-dialog-backdrop">
      <section
        ref={dialogRef}
        className="ui-dialog"
        role={role}
        aria-modal="true"
        aria-label={accessibleName}
        aria-labelledby={accessibleName ? undefined : titleId}
        aria-describedby={description ? descriptionId : undefined}
        tabIndex={-1}
      >
        <div className="ui-dialog-heading">
          <div><span className="eyebrow">CONFIRMATION</span><h2 id={titleId}>{title}</h2></div>
          <button className="ui-dialog-close" type="button" aria-label="Close dialog" title="Close dialog" onClick={onClose}><X size={17} aria-hidden="true" /></button>
        </div>
        <div className="ui-dialog-body">
          <div className="ui-dialog-icon" aria-hidden="true"><Icon size={19} /></div>
          <div>
            <p id={descriptionId}>{description}</p>
            {approvalRequest ? <ApprovalRequestDetails request={approvalRequest} /> : null}
            {children}
          </div>
        </div>
        <div className="ui-dialog-actions">
          <button type="button" onClick={onClose}>{cancelLabel}</button>
          {onConfirm ? <button type="button" className={`ui-dialog-confirm ${confirmClassName}`.trim()} onClick={() => confirmRef.current?.()}>{confirmLabel}</button> : null}
        </div>
      </section>
    </div>
  );
}

function ApprovalRequestDetails({ request }: { request: ApprovalRequest }) {
  return (
    <dl className="ui-dialog-approval-details" aria-label="Approval request details">
      <div><dt>TOOL</dt><dd><code>{request.tool}</code></dd></div>
      <div><dt>COMMAND</dt><dd><code>{request.command.join(" ")}</code></dd></div>
      <div><dt>PATHS</dt><dd><code>{request.paths.length ? request.paths.join(", ") : "NONE"}</code></dd></div>
      <div><dt>WORKDIR</dt><dd><code>{request.workdir}</code></dd></div>
      <div><dt>IMPACT</dt><dd>{request.impact}</dd></div>
      <div><dt>SCOPE</dt><dd>{request.authorization_scope.toUpperCase()}</dd></div>
    </dl>
  );
}

export function PermissionDialog(props: Omit<DialogProps, "role" | "icon">) {
  return <UiDialog {...props} role="alertdialog" icon={AlertTriangle} confirmClassName="ui-dialog-danger" />;
}

export function InstallDialog(props: Omit<DialogProps, "role" | "icon">) {
  return <UiDialog {...props} role="dialog" icon={Download} />;
}

function getFocusable(root: HTMLElement | null): HTMLElement[] {
  if (!root) {
    return [];
  }
  return Array.from(root.querySelectorAll<HTMLElement>(
    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )).filter((element) => element.getAttribute("aria-hidden") !== "true");
}

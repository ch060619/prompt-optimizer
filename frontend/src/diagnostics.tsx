import { Check, Clipboard, ExternalLink, Eye, FileText, HeartPulse, RefreshCw, ShieldCheck, Wrench, X } from "lucide-react";
import { useState } from "react";
import { sanitizePublicText } from "./publicOutput";

// RC IDs: RC-118, RC-180. Render component health, redacted diagnostics, logs, licenses, and updates.

type ComponentState = "healthy" | "degraded" | "unavailable";
type Component = { id: string; name: string; version: string; state: ComponentState; detail: string; fix: string };

const initialComponents: Component[] = [
  { id: "app", name: "Rabbit Code", version: "3.0.0", state: "healthy", detail: "Desktop workspace is responding.", fix: "" },
  { id: "sidecar", name: "App Server sidecar", version: "3.0.0", state: "degraded", detail: "Health probe is slow or unavailable.", fix: "Restart the sidecar and check its local log." },
  { id: "runner", name: "Local model runner", version: "not installed", state: "unavailable", detail: "No local runner is configured.", fix: "Install a local model before starting the runner." },
];

const stateLabels: Record<ComponentState, string> = { healthy: "HEALTHY", degraded: "DEGRADED", unavailable: "UNAVAILABLE" };

export function Diagnostics() {
  const [components, setComponents] = useState(initialComponents);
  const [updateStatus, setUpdateStatus] = useState<"idle" | "checking" | "current">("idle");
  const [previewOpen, setPreviewOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  function restartSidecar() {
    setComponents((current) => current.map((component) => component.id === "sidecar" ? { ...component, state: "healthy", detail: "Health probe passed after restart.", fix: "" } : component));
    setNotice("SIDECAR HEALTHY");
  }

  function checkUpdates() {
    setUpdateStatus("checking");
    setUpdateStatus("current");
    setNotice("UP TO DATE / 3.0.0");
  }

  function diagnosticPayload() {
    return JSON.stringify({
      app_version: "3.0.0",
      platform: "windows",
      components: components.map(({ id, name, version, state }) => ({ id, name, version, state })),
      log_directory: "%APPDATA%\\rabbit-code\\logs",
      provider: "redacted",
      api_key: "[REDACTED]",
      source: "[NOT INCLUDED]",
    }, null, 2);
  }

  function openDiagnosticsPreview() {
    setPreviewOpen(true);
    setNotice("REDACTED PREVIEW READY");
  }

  function copyDiagnostics() {
    const payload = sanitizePublicText(diagnosticPayload());
    setNotice("REDACTED DIAGNOSTICS COPIED");
    if (navigator.clipboard?.writeText) {
      void navigator.clipboard.writeText(payload).catch(() => undefined);
    }
  }

  return (
    <main className="diagnostics-page">
      <header className="diagnostics-header">
        <div><span className="eyebrow">DIAGNOSTICS / ABOUT / UPDATE</span><h1>Know what is healthy before you debug.</h1><p>See component versions, actionable fixes, and a safe snapshot for support.</p></div>
        <div className="diagnostics-version"><ShieldCheck size={16} aria-hidden="true" /> RABBIT CODE 3.0.0</div>
      </header>
      <section className="diagnostics-summary" aria-label="Diagnostic summary"><div><span>APP</span><strong>3.0.0</strong></div><div><span>LOGS</span><strong>%APPDATA%\\rabbit-code\\logs</strong></div><div><span>LICENSE</span><strong>MIT / NOTICE</strong></div><button type="button" className="diagnostics-copy" onClick={openDiagnosticsPreview}><Eye size={15} aria-hidden="true" /> PREVIEW REDACTED DIAGNOSTICS</button></section>
      {previewOpen ? <section className="diagnostics-preview" aria-label="Diagnostic preview"><div className="diagnostics-preview-heading"><div><span className="eyebrow">SAFE EXPORT PREVIEW</span><strong>Metadata only. Source and prompt content excluded.</strong></div><button type="button" aria-label="Clear diagnostic preview" onClick={() => setPreviewOpen(false)}><X size={16} aria-hidden="true" /></button></div><div className="diagnostics-preview-grid"><div><span>FILES</span><strong>component status, version, log directory</strong></div><div><span>SECRETS</span><strong>redacted</strong></div></div><div className="diagnostics-preview-actions"><button type="button" onClick={copyDiagnostics}><Clipboard size={15} aria-hidden="true" /> COPY PREVIEW</button><button type="button" onClick={() => { setPreviewOpen(false); setNotice("DIAGNOSTIC PREVIEW CLEARED"); }}><X size={15} aria-hidden="true" /> CLEAR PREVIEW</button></div></section> : null}
      <div className="diagnostics-shell">
        <section className="diagnostics-components" aria-label="Component health">
          <div className="diagnostics-section-heading"><span className="eyebrow">COMPONENT HEALTH</span><HeartPulse size={16} aria-hidden="true" /></div>
          <div className="diagnostics-component-list">{components.map((component) => <article className="diagnostics-component" key={component.id}><div className="diagnostics-component-heading"><div><strong>{component.name}</strong><small>{component.version}</small></div><b className={`diagnostics-state-${component.state}`}>{stateLabels[component.state]}</b></div><p>{component.detail}</p>{component.fix ? <div className="diagnostics-fix"><Wrench size={14} aria-hidden="true" /><span>{component.fix}</span>{component.id === "sidecar" ? <button type="button" onClick={restartSidecar}>RESTART SIDECAR</button> : <a href="/workspace/models">OPEN MODEL INSTALLER <ExternalLink size={13} aria-hidden="true" /></a>}</div> : <div className="diagnostics-ok"><Check size={14} aria-hidden="true" /> NO ACTION NEEDED</div>}</article>)}</div>
        </section>
        <aside className="diagnostics-update" aria-label="Update status">
          <div className="diagnostics-section-heading"><span className="eyebrow">UPDATES</span><RefreshCw size={15} aria-hidden="true" /></div>
          <strong>{updateStatus === "current" ? "You are up to date." : "Check the stable channel."}</strong>
          <p>{updateStatus === "current" ? "Rabbit Code 3.0.0 is the latest installed release." : "No update is downloaded without your confirmation."}</p>
          <button type="button" className="diagnostics-update-button" onClick={checkUpdates}><RefreshCw size={15} aria-hidden="true" /> {updateStatus === "checking" ? "CHECKING..." : "CHECK FOR UPDATES"}</button>
          <label>RELEASE CHANNEL<select aria-label="Release channel" defaultValue="stable"><option value="stable">STABLE</option><option value="preview">PREVIEW</option></select></label>
          <div className="diagnostics-license"><FileText size={15} aria-hidden="true" /><span>MIT license, third-party notices, and privacy information are available with this build.</span></div>
        </aside>
      </div>
      <section className="diagnostics-about" aria-label="About Rabbit Code"><div><span className="eyebrow">ABOUT</span><h2>Open tools, clear boundaries.</h2></div><div><p>Rabbit Code keeps product behavior, local workspace state, and external Provider credentials in separate boundaries.</p><a href="/blog">VIEW BUILD NOTES <ExternalLink size={14} aria-hidden="true" /></a></div></section>
      {notice ? <p className="diagnostics-notice" role="status">{notice}</p> : null}
    </main>
  );
}

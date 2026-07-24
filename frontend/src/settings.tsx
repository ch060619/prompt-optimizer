import { Check, ChevronRight, Keyboard, LockKeyhole, Palette, Plug, RotateCcw, Save, Server, Shield, SlidersHorizontal, Terminal, Trash2, Wrench } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "./api";
import { PermissionDialog } from "./components/UiStates";
import { localeFromSetting, t, type Locale, type MessageKey } from "./i18n";
import { AppLink } from "./navigation";

// RC IDs: RC-117, RC-184, RC-220. Render scoped settings and versioned local consent.

const TELEMETRY_CONSENT_VERSION = "rc220-v1";

type SectionId = "appearance" | "providers" | "language" | "terminal" | "permissions" | "sandbox" | "data" | "privacy" | "updates" | "shortcuts" | "mcp" | "plugins" | "advanced";
type SettingsState = {
  theme: "light" | "dark";
  language: "English" | "简体中文";
  shell: "PowerShell" | "cmd" | "WSL";
  permissionMode: "ask" | "high" | "full";
  sandbox: boolean;
  network: "off" | "workspace" | "full";
  retainLogs: boolean;
  savePromptHistory: boolean;
  telemetry: boolean;
  telemetryConsentVersion: string | null;
  autoUpdate: boolean;
  notifications: boolean;
  tray: boolean;
  shortcutPreset: "default" | "vim";
  mcp: boolean;
  plugins: boolean;
  logLevel: "error" | "info" | "debug";
};

type CleanupPreview = {
  delete_paths: string[];
  credential_count: number;
  retain: string[];
};

type RetentionPreview = {
  rotate_log_paths: string[];
  delete_log_paths: string[];
  delete_cache_paths: string[];
  delete_task_ids: string[];
  delete_history_ids: number[];
  estimated_bytes: number;
};

const defaultSettings: SettingsState = {
  theme: "light",
  language: "English",
  shell: "PowerShell",
  permissionMode: "ask",
  sandbox: true,
  network: "workspace",
  retainLogs: true,
  savePromptHistory: true,
  telemetry: false,
  telemetryConsentVersion: null,
  autoUpdate: true,
  notifications: true,
  tray: false,
  shortcutPreset: "default",
  mcp: false,
  plugins: false,
  logLevel: "info",
};

const sections: { id: SectionId; label: string; icon: typeof Palette }[] = [
  { id: "appearance", label: "Appearance", icon: Palette },
  { id: "providers", label: "Providers & models", icon: Server },
  { id: "language", label: "Language", icon: SlidersHorizontal },
  { id: "terminal", label: "Terminal", icon: Terminal },
  { id: "permissions", label: "Permissions", icon: Shield },
  { id: "sandbox", label: "Sandbox", icon: LockKeyhole },
  { id: "data", label: "Data", icon: Trash2 },
  { id: "privacy", label: "Privacy", icon: Shield },
  { id: "updates", label: "Updates", icon: RotateCcw },
  { id: "shortcuts", label: "Shortcuts", icon: Keyboard },
  { id: "mcp", label: "MCP", icon: Server },
  { id: "plugins", label: "Plugins", icon: Plug },
  { id: "advanced", label: "Advanced", icon: Wrench },
];

function scopeFromLocation() {
  const raw = new URLSearchParams(window.location.search).get("workspace") || "default";
  return raw.replace(/[^a-zA-Z0-9_-]/g, "-");
}

function readSettings(key: string): SettingsState {
  try {
    const saved = JSON.parse(localStorage.getItem(key) || "null") as Partial<SettingsState> | null;
    return { ...defaultSettings, ...(saved || {}) };
  } catch {
    return defaultSettings;
  }
}

export function Settings() {
  const scope = scopeFromLocation();
  const storageKey = `rabbit_code_settings_${scope}`;
  const [activeSection, setActiveSection] = useState<SectionId>("appearance");
  const [settings, setSettings] = useState(() => readSettings(storageKey));
  const locale = localeFromSetting(settings.language);
  const [resetOpen, setResetOpen] = useState(false);
  const [cleanupOpen, setCleanupOpen] = useState(false);
  const [cleanupPreview, setCleanupPreview] = useState<CleanupPreview | null>(null);
  const [retentionOpen, setRetentionOpen] = useState(false);
  const [retentionPreview, setRetentionPreview] = useState<RetentionPreview | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = settings.theme;
    return () => { delete document.documentElement.dataset.theme; };
  }, [settings.theme]);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  function updateSetting<K extends keyof SettingsState>(key: K, value: SettingsState[K]) {
    setSettings((current) => {
      const next = { ...current, [key]: value };
      localStorage.setItem(storageKey, JSON.stringify(next));
      return next;
    });
    setNotice("SETTING SAVED");
  }

  function resetSettings() {
    setSettings(defaultSettings);
    localStorage.setItem(storageKey, JSON.stringify(defaultSettings));
    setResetOpen(false);
    setNotice("WORKSPACE SETTINGS RESET");
  }

  function updateTelemetry(enabled: boolean) {
    setSettings((current) => {
      const next = {
        ...current,
        telemetry: enabled,
        telemetryConsentVersion: enabled ? TELEMETRY_CONSENT_VERSION : null,
      };
      localStorage.setItem(storageKey, JSON.stringify(next));
      return next;
    });
    setNotice(enabled ? "TELEMETRY CONSENT SAVED" : "TELEMETRY TURNED OFF");
  }

  function clearPendingTelemetry() {
    localStorage.removeItem(`rabbit_code_telemetry_pending_${scope}`);
    setNotice("PENDING TELEMETRY DELETED");
  }

  async function previewCleanup() {
    try {
      const payload = await api.cleanupPreview();
      const deletePaths = Array.isArray(payload.delete_paths)
        ? payload.delete_paths.filter((value): value is string => typeof value === "string")
        : [];
      const retain = Array.isArray(payload.retain)
        ? payload.retain.filter((value): value is string => typeof value === "string")
        : [];
      setCleanupPreview({
        delete_paths: deletePaths,
        credential_count: typeof payload.credential_count === "number" ? payload.credential_count : 0,
        retain,
      });
      setCleanupOpen(true);
    } catch {
      setNotice("CLEANUP PREVIEW UNAVAILABLE");
    }
  }

  async function confirmCleanup() {
    try {
      await api.cleanup(true);
      localStorage.clear();
      api.setToken(null);
      setCleanupOpen(false);
      setCleanupPreview(null);
      setNotice("ALL LOCAL DATA DELETED");
    } catch {
      setNotice("LOCAL DATA CLEANUP FAILED");
    }
  }

  async function previewRetention() {
    try {
      const payload = await api.retentionPreview() as Record<string, unknown>;
      const list = (key: string) => Array.isArray(payload[key]) ? payload[key].filter((value): value is string => typeof value === "string") : [];
      const historyIds = Array.isArray(payload.delete_history_ids)
        ? payload.delete_history_ids.filter((value): value is number => typeof value === "number")
        : [];
      setRetentionPreview({
        rotate_log_paths: list("rotate_log_paths"),
        delete_log_paths: list("delete_log_paths"),
        delete_cache_paths: list("delete_cache_paths"),
        delete_task_ids: list("delete_task_ids"),
        delete_history_ids: historyIds,
        estimated_bytes: typeof payload.estimated_bytes === "number" ? payload.estimated_bytes : 0,
      });
      setRetentionOpen(true);
    } catch {
      setNotice("RETENTION PREVIEW UNAVAILABLE");
    }
  }

  async function confirmRetention() {
    try {
      await api.retention(true);
      setRetentionOpen(false);
      setRetentionPreview(null);
      setNotice("RETENTION CLEANUP COMPLETE");
    } catch {
      setNotice("RETENTION CLEANUP FAILED");
    }
  }

  return (
    <main className="settings-page">
      <header className="settings-header">
        <div><span className="eyebrow">SETTINGS / {scope.toUpperCase()}</span><h1>Make the workspace yours.</h1><p>Changes apply immediately to this workspace and remain separate from other projects.</p></div>
        <div className="settings-scope"><Save size={15} aria-hidden="true" /> {t(locale, "settings.scope", { workspace: scope })}</div>
      </header>
      <div className="settings-shell">
        <aside className="settings-nav" aria-label="Settings sections">
          <div className="settings-nav-heading"><span className="eyebrow">{t(locale, "settings.configure")}</span><span>{sections.length}</span></div>
          <nav>{sections.map(({ id, icon: Icon }) => <button key={id} type="button" className={activeSection === id ? "active" : ""} onClick={() => setActiveSection(id)}><Icon size={15} aria-hidden="true" /><span>{sectionLabel(locale, id)}</span><ChevronRight size={14} aria-hidden="true" /></button>)}</nav>
          <p className="settings-source-note">Every value below is marked with its scope and source.</p>
        </aside>
        <section className="settings-detail" aria-label="Settings detail">
          <div className="settings-detail-heading"><div><span className="eyebrow">{sectionLabel(locale, activeSection)}</span><h2>{sectionTitle(activeSection, locale)}</h2></div><span className="settings-saved"><Check size={14} aria-hidden="true" /> {t(locale, "settings.savedLocally")}</span></div>
          <SettingsSection section={activeSection} settings={settings} updateSetting={updateSetting} onReset={() => setResetOpen(true)} onCleanupPreview={() => void previewCleanup()} onRetentionPreview={() => void previewRetention()} onTelemetryChange={updateTelemetry} onClearPendingTelemetry={clearPendingTelemetry} workspace={scope} />
        </section>
      </div>
      <PermissionDialog
        open={resetOpen}
        accessibleName="Reset workspace settings"
        title="Reset this workspace?"
        description={<>This only removes settings for <strong>{scope}</strong>. Provider keys, workspace files, sessions, and other workspaces are untouched.</>}
        onClose={() => setResetOpen(false)}
        onConfirm={resetSettings}
        confirmLabel="RESET SETTINGS"
      />
      <PermissionDialog
        open={cleanupOpen}
        accessibleName="Delete all local data"
        title="Delete all local data?"
        description={cleanupPreview ? `This removes ${cleanupPreview.delete_paths.length} local path(s) and ${cleanupPreview.credential_count} credential reference(s). Retained: ${cleanupPreview.retain.join(", ") || "none"}. Cancel leaves everything unchanged.` : "Review the cleanup preview before deleting local data."}
        onClose={() => setCleanupOpen(false)}
        onConfirm={() => void confirmCleanup()}
        confirmLabel="DELETE ALL LOCAL DATA"
      />
      <PermissionDialog
        open={retentionOpen}
        accessibleName="Run retention cleanup"
        title="Run retention cleanup?"
        description={retentionPreview ? `Rotate ${retentionPreview.rotate_log_paths.length} log file(s), delete ${retentionPreview.delete_log_paths.length + retentionPreview.delete_cache_paths.length} file(s), ${retentionPreview.delete_task_ids.length} finished task(s), and ${retentionPreview.delete_history_ids.length} prompt history item(s). Estimated file release: ${retentionPreview.estimated_bytes} bytes. Configuration, models, attachments, database, and running tasks are retained.` : "Review the retention preview before cleanup."}
        onClose={() => setRetentionOpen(false)}
        onConfirm={() => void confirmRetention()}
        confirmLabel="RUN RETENTION CLEANUP"
      />
      {notice ? <p className="settings-notice" role="status">{notice}</p> : null}
    </main>
  );
}

function sectionLabel(locale: Locale, section: SectionId) {
  return t(locale, `settings.section.${section}` as MessageKey);
}

function sectionTitle(section: SectionId, locale: Locale) {
  return t(locale, `settings.title.${section}` as MessageKey);
}

function SettingsSection({ section, settings, updateSetting, onReset, onCleanupPreview, onRetentionPreview, onTelemetryChange, onClearPendingTelemetry, workspace }: { section: SectionId; settings: SettingsState; updateSetting: <K extends keyof SettingsState>(key: K, value: SettingsState[K]) => void; onReset: () => void; onCleanupPreview: () => void; onRetentionPreview: () => void; onTelemetryChange: (enabled: boolean) => void; onClearPendingTelemetry: () => void; workspace: string }) {
  if (section === "appearance") return <SettingRows><SettingSelect label="Theme" value={settings.theme} options={["light", "dark"]} onChange={(value) => updateSetting("theme", value as SettingsState["theme"])} /><SettingToggle label="Enable desktop notifications" checked={settings.notifications} onChange={(value) => updateSetting("notifications", value)} /><SettingToggle label="Show system tray icon when available" checked={settings.tray} onChange={(value) => updateSetting("tray", value)} /></SettingRows>;
  if (section === "providers") return <SettingRows><SettingReadOnly label="Provider data" value="Workspace-scoped, secrets stay opaque" /><AppLink className="settings-provider-link" href={`/workspace/providers?workspace=${encodeURIComponent(workspace)}`}><Server size={15} aria-hidden="true" /> MANAGE PROVIDERS &amp; MODELS</AppLink></SettingRows>;
  if (section === "language") return <SettingRows><SettingSelect label="Language" value={settings.language} options={["English", "简体中文"]} onChange={(value) => updateSetting("language", value as SettingsState["language"])} /><SettingReadOnly label="Scope" value="Workspace" /></SettingRows>;
  if (section === "terminal") return <SettingRows><SettingSelect label="Default shell" value={settings.shell} options={["PowerShell", "cmd", "WSL"]} onChange={(value) => updateSetting("shell", value as SettingsState["shell"])} /><SettingToggle label="Restore terminal tabs on launch" checked={settings.retainLogs} onChange={(value) => updateSetting("retainLogs", value)} /></SettingRows>;
  if (section === "permissions") return <SettingRows><SettingSelect label="Permission mode" value={settings.permissionMode} options={["ask", "high", "full"]} onChange={(value) => updateSetting("permissionMode", value as SettingsState["permissionMode"])} /><SettingToggle label="Confirm destructive edits" checked={settings.permissionMode !== "full"} onChange={(value) => updateSetting("permissionMode", value ? "ask" : "full")} /></SettingRows>;
  if (section === "sandbox") return <SettingRows><SettingToggle label="Enable workspace sandbox" checked={settings.sandbox} onChange={(value) => updateSetting("sandbox", value)} /><SettingSelect label="Network access" value={settings.network} options={["off", "workspace", "full"]} onChange={(value) => updateSetting("network", value as SettingsState["network"])} /></SettingRows>;
  if (section === "data") return <SettingRows><SettingToggle label="Save prompt history" checked={settings.savePromptHistory} onChange={(value) => updateSetting("savePromptHistory", value)} /><SettingToggle label="Retain local logs" checked={settings.retainLogs} onChange={(value) => updateSetting("retainLogs", value)} /><SettingReadOnly label="Data location" value="Rabbit Code local data directory" /><SettingReadOnly label="Retention defaults" value="Logs 5/50 MB; cache 100 MB; sessions 30 days; history 365 days / 500 entries" /><button type="button" className="settings-danger-link" onClick={onRetentionPreview}><Trash2 size={15} aria-hidden="true" /> PREVIEW RETENTION CLEANUP</button><button type="button" className="settings-danger-link" onClick={onReset}><Trash2 size={15} aria-hidden="true" /> RESET WORKSPACE SETTINGS</button><button type="button" className="settings-danger-link" onClick={onCleanupPreview}><Trash2 size={15} aria-hidden="true" /> PREVIEW ALL LOCAL DATA</button></SettingRows>;
  if (section === "privacy") return <SettingRows><SettingToggle label="Share anonymous usage telemetry" checked={settings.telemetry} onChange={onTelemetryChange} /><SettingReadOnly label="Consent version" value={settings.telemetryConsentVersion || "OFF / NO CONSENT"} /><div className="settings-privacy-note" aria-label="Telemetry fields"><strong>LOCAL EVENTS ONLY</strong><p>Only anonymous technical metadata is eligible: app version, event name, duration, result, Provider/model ID, and resource counters. Prompt text, files, credentials, request bodies, and responses are excluded.</p><small>No telemetry server or account is required. Turning this off stops collection immediately.</small></div><button type="button" className="settings-danger-link" onClick={onClearPendingTelemetry}><Trash2 size={15} aria-hidden="true" /> DELETE PENDING TELEMETRY</button><SettingReadOnly label="Credential handling" value="OS keychain boundary" /></SettingRows>;
  if (section === "updates") return <SettingRows><SettingToggle label="Install updates automatically" checked={settings.autoUpdate} onChange={(value) => updateSetting("autoUpdate", value)} /><SettingReadOnly label="Update channel" value="Stable" /></SettingRows>;
  if (section === "shortcuts") return <SettingRows><SettingSelect label="Shortcut preset" value={settings.shortcutPreset} options={["default", "vim"]} onChange={(value) => updateSetting("shortcutPreset", value as SettingsState["shortcutPreset"])} /><SettingReadOnly label="Command palette" value="Ctrl+K" /></SettingRows>;
  if (section === "mcp") return <SettingRows><SettingToggle label="Enable MCP servers" checked={settings.mcp} onChange={(value) => updateSetting("mcp", value)} /><SettingReadOnly label="Server scope" value="Workspace only" /></SettingRows>;
  if (section === "plugins") return <SettingRows><SettingToggle label="Enable workspace plugins" checked={settings.plugins} onChange={(value) => updateSetting("plugins", value)} /><SettingReadOnly label="Install source" value="Signed local bundles" /></SettingRows>;
  return <SettingRows><SettingSelect label="Log level" value={settings.logLevel} options={["error", "info", "debug"]} onChange={(value) => updateSetting("logLevel", value as SettingsState["logLevel"])} /><button type="button" className="settings-danger-link" onClick={onReset}><Trash2 size={15} aria-hidden="true" /> RESET WORKSPACE SETTINGS</button></SettingRows>;
}

function SettingRows({ children }: { children: React.ReactNode }) {
  return <div className="setting-rows">{children}</div>;
}

function SettingSelect({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return <label className="setting-control"><span>{label}</span><select aria-label={label} value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option key={option} value={option}>{option}</option>)}</select><small>WORKSPACE / LOCAL</small></label>;
}

function SettingToggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) {
  return <label className="setting-toggle"><span><strong>{label}</strong><small>WORKSPACE / LOCAL</small></span><input type="checkbox" aria-label={label} checked={checked} onChange={(event) => onChange(event.target.checked)} /></label>;
}

function SettingReadOnly({ label, value }: { label: string; value: string }) {
  return <div className="setting-readonly"><span>{label}</span><strong>{value}</strong><small>WORKSPACE / LOCAL</small></div>;
}

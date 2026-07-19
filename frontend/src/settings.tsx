import { Check, ChevronRight, Keyboard, LockKeyhole, Palette, Plug, RotateCcw, Save, Server, Shield, SlidersHorizontal, Terminal, Trash2, Wrench } from "lucide-react";
import { useState } from "react";
import { api } from "./api";
import { PermissionDialog } from "./components/UiStates";
import { useEffect } from "react";

// RC IDs: RC-117, RC-184. Render scoped settings and confirmed local-data cleanup.

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
  const [resetOpen, setResetOpen] = useState(false);
  const [cleanupOpen, setCleanupOpen] = useState(false);
  const [cleanupPreview, setCleanupPreview] = useState<CleanupPreview | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = settings.theme;
    return () => { delete document.documentElement.dataset.theme; };
  }, [settings.theme]);

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

  return (
    <main className="settings-page">
      <header className="settings-header">
        <div><span className="eyebrow">SETTINGS / {scope.toUpperCase()}</span><h1>Make the workspace yours.</h1><p>Changes apply immediately to this workspace and remain separate from other projects.</p></div>
        <div className="settings-scope"><Save size={15} aria-hidden="true" /> WORKSPACE SCOPE / {scope}</div>
      </header>
      <div className="settings-shell">
        <aside className="settings-nav" aria-label="Settings sections">
          <div className="settings-nav-heading"><span className="eyebrow">CONFIGURE</span><span>{sections.length}</span></div>
          <nav>{sections.map(({ id, label, icon: Icon }) => <button key={id} type="button" className={activeSection === id ? "active" : ""} onClick={() => setActiveSection(id)}><Icon size={15} aria-hidden="true" /><span>{label}</span><ChevronRight size={14} aria-hidden="true" /></button>)}</nav>
          <p className="settings-source-note">Every value below is marked with its scope and source.</p>
        </aside>
        <section className="settings-detail" aria-label="Settings detail">
          <div className="settings-detail-heading"><div><span className="eyebrow">{sections.find((section) => section.id === activeSection)?.label}</span><h2>{sectionTitle(activeSection)}</h2></div><span className="settings-saved"><Check size={14} aria-hidden="true" /> SAVED LOCALLY</span></div>
          <SettingsSection section={activeSection} settings={settings} updateSetting={updateSetting} onReset={() => setResetOpen(true)} onCleanupPreview={() => void previewCleanup()} workspace={scope} />
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
      {notice ? <p className="settings-notice" role="status">{notice}</p> : null}
    </main>
  );
}

function sectionTitle(section: SectionId) {
  const titles: Record<SectionId, string> = {
    appearance: "Set the visual rhythm.",
    providers: "Route the work safely.",
    language: "Choose the language.",
    terminal: "Shape the terminal session.",
    permissions: "Decide what needs approval.",
    sandbox: "Constrain tool access.",
    data: "Keep local data under control.",
    privacy: "Choose what leaves the machine.",
    updates: "Keep the app current.",
    shortcuts: "Tune the keyboard layer.",
    mcp: "Connect Model Context Protocol.",
    plugins: "Manage local extensions.",
    advanced: "Expose the sharp edges carefully.",
  };
  return titles[section];
}

function SettingsSection({ section, settings, updateSetting, onReset, onCleanupPreview, workspace }: { section: SectionId; settings: SettingsState; updateSetting: <K extends keyof SettingsState>(key: K, value: SettingsState[K]) => void; onReset: () => void; onCleanupPreview: () => void; workspace: string }) {
  if (section === "appearance") return <SettingRows><SettingSelect label="Theme" value={settings.theme} options={["light", "dark"]} onChange={(value) => updateSetting("theme", value as SettingsState["theme"])} /><SettingToggle label="Enable desktop notifications" checked={settings.notifications} onChange={(value) => updateSetting("notifications", value)} /><SettingToggle label="Show system tray icon when available" checked={settings.tray} onChange={(value) => updateSetting("tray", value)} /></SettingRows>;
  if (section === "providers") return <SettingRows><SettingReadOnly label="Provider data" value="Workspace-scoped, secrets stay opaque" /><a className="settings-provider-link" href={`/workspace/providers?workspace=${encodeURIComponent(workspace)}`}><Server size={15} aria-hidden="true" /> MANAGE PROVIDERS &amp; MODELS</a></SettingRows>;
  if (section === "language") return <SettingRows><SettingSelect label="Language" value={settings.language} options={["English", "简体中文"]} onChange={(value) => updateSetting("language", value as SettingsState["language"])} /><SettingReadOnly label="Scope" value="Workspace" /></SettingRows>;
  if (section === "terminal") return <SettingRows><SettingSelect label="Default shell" value={settings.shell} options={["PowerShell", "cmd", "WSL"]} onChange={(value) => updateSetting("shell", value as SettingsState["shell"])} /><SettingToggle label="Restore terminal tabs on launch" checked={settings.retainLogs} onChange={(value) => updateSetting("retainLogs", value)} /></SettingRows>;
  if (section === "permissions") return <SettingRows><SettingSelect label="Permission mode" value={settings.permissionMode} options={["ask", "high", "full"]} onChange={(value) => updateSetting("permissionMode", value as SettingsState["permissionMode"])} /><SettingToggle label="Confirm destructive edits" checked={settings.permissionMode !== "full"} onChange={(value) => updateSetting("permissionMode", value ? "ask" : "full")} /></SettingRows>;
  if (section === "sandbox") return <SettingRows><SettingToggle label="Enable workspace sandbox" checked={settings.sandbox} onChange={(value) => updateSetting("sandbox", value)} /><SettingSelect label="Network access" value={settings.network} options={["off", "workspace", "full"]} onChange={(value) => updateSetting("network", value as SettingsState["network"])} /></SettingRows>;
  if (section === "data") return <SettingRows><SettingToggle label="Save prompt history" checked={settings.savePromptHistory} onChange={(value) => updateSetting("savePromptHistory", value)} /><SettingToggle label="Retain local logs" checked={settings.retainLogs} onChange={(value) => updateSetting("retainLogs", value)} /><SettingReadOnly label="Data location" value="Rabbit Code local data directory" /><button type="button" className="settings-danger-link" onClick={onReset}><Trash2 size={15} aria-hidden="true" /> RESET WORKSPACE SETTINGS</button><button type="button" className="settings-danger-link" onClick={onCleanupPreview}><Trash2 size={15} aria-hidden="true" /> PREVIEW ALL LOCAL DATA</button></SettingRows>;
  if (section === "privacy") return <SettingRows><SettingToggle label="Share anonymous usage telemetry" checked={settings.telemetry} onChange={(value) => updateSetting("telemetry", value)} /><SettingReadOnly label="Credential handling" value="OS keychain boundary" /></SettingRows>;
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

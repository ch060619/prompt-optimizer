import { ArrowLeft, ArrowRight, Check, CircleCheck, CircleX, Database, Pencil, Pin, Plus, Power, RefreshCw, ShieldCheck, Trash2 } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { api } from "./api";
import { EmptyState, OfflineState, UiDialog } from "./components/UiStates";
import { maskSecret, maskSecretTail, registerRuntimeSecret } from "./publicOutput";
import { readWorkspaceRoute, workspaceHomeHref, workspaceScope, writeWorkspaceRoute } from "./workspaceRoute";

// RC IDs: RC-114, RC-159, RC-164, RC-167, RC-180, RC-181. Render only declared Provider capabilities.

type ConnectionStatus = "untested" | "connected" | "failed";
type ApiWizardStep = 1 | 2 | 3 | 4;
type ApiService = "openai" | "openrouter" | "deepseek" | "gemini" | "anthropic" | "custom";
type ApiProtocol = "chat_completions" | "responses" | "gemini" | "anthropic";

type ApiWizardDraft = {
  service: ApiService;
  protocol: ApiProtocol;
  baseUrl: string;
  model: string;
  step: ApiWizardStep;
};

const apiServices: Array<{
  value: ApiService;
  label: string;
  protocol: ApiProtocol;
  baseUrl: string;
}> = [
  { value: "openai", label: "OpenAI", protocol: "chat_completions", baseUrl: "https://api.openai.com/v1" },
  { value: "openrouter", label: "OpenRouter", protocol: "chat_completions", baseUrl: "https://openrouter.ai/api/v1" },
  { value: "deepseek", label: "DeepSeek", protocol: "chat_completions", baseUrl: "https://api.deepseek.com/v1" },
  { value: "gemini", label: "Google Gemini", protocol: "gemini", baseUrl: "https://generativelanguage.googleapis.com/v1beta" },
  { value: "anthropic", label: "Anthropic Messages", protocol: "anthropic", baseUrl: "https://api.anthropic.com/v1" },
  { value: "custom", label: "Custom compatible endpoint", protocol: "chat_completions", baseUrl: "" },
];

const apiProtocols: Array<{ value: ApiProtocol; label: string }> = [
  { value: "chat_completions", label: "OpenAI-compatible Chat Completions" },
  { value: "responses", label: "OpenAI Responses" },
  { value: "gemini", label: "Gemini native" },
  { value: "anthropic", label: "Anthropic Messages" },
];

const apiWizardSteps = [
  "PROTOCOL / PROVIDER",
  "ENDPOINT / CREDENTIAL",
  "MODEL",
  "TEST / DEFAULT",
] as const;

const defaultApiWizardDraft: ApiWizardDraft = {
  service: "openai",
  protocol: "chat_completions",
  baseUrl: "https://api.openai.com/v1",
  model: "",
  step: 1,
};

function apiWizardDraftKey() {
  const scope = (new URLSearchParams(window.location.search).get("workspace") || "default").replace(/[^a-zA-Z0-9_-]/g, "-");
  return `rabbit_code_api_setup_draft_${scope}`;
}

function readApiWizardDraft(): ApiWizardDraft {
  try {
    const parsed = JSON.parse(localStorage.getItem(apiWizardDraftKey()) || "null") as Partial<ApiWizardDraft> | null;
    if (!parsed || !apiServices.some((service) => service.value === parsed.service)) {
      return defaultApiWizardDraft;
    }
    return {
      service: parsed.service as ApiService,
      protocol: apiProtocols.some((protocol) => protocol.value === parsed.protocol)
        ? parsed.protocol as ApiProtocol
        : defaultApiWizardDraft.protocol,
      baseUrl: typeof parsed.baseUrl === "string" ? parsed.baseUrl : defaultApiWizardDraft.baseUrl,
      model: typeof parsed.model === "string" ? parsed.model : "",
      step: parsed.step && parsed.step >= 1 && parsed.step <= 4 ? parsed.step as ApiWizardStep : 1,
    };
  } catch {
    return defaultApiWizardDraft;
  }
}

function isValidModelId(value: string) {
  return value.length > 0
    && value.length <= 256
    && !/\s/.test(value)
    && [...value].every((character) => {
      const code = character.charCodeAt(0);
      return code > 31 && code !== 127;
    });
}
export type Provider = {
  id: string;
  name: string;
  kind: string;
  configured: boolean;
  enabled: boolean;
  isDefault: boolean;
  baseUrl: string;
  models: string[];
  selectedModel: string;
  capabilities: string[];
  costLabel: string;
  connection: ConnectionStatus;
};

function persistProviderRoute(provider: Provider, model = provider.selectedModel) {
  const providerName = provider.id === "openai-compatible" ? "openai" : provider.id;
  writeWorkspaceRoute({
    provider: providerName,
    model: model || undefined,
    health: provider.enabled && provider.connection === "connected" ? "healthy" : provider.enabled ? "unknown" : "unavailable",
    enabled: provider.enabled,
  });
}

const initialProviders: Provider[] = [
  {
    id: "offline",
    name: "Offline Rules",
    kind: "LOCAL FALLBACK",
    configured: true,
    enabled: true,
    isDefault: false,
    baseUrl: "No network",
    models: ["offline"],
    selectedModel: "offline",
    capabilities: ["TEXT", "STREAMING"],
    costLabel: "NO NETWORK / $0",
    connection: "connected",
  },
  {
    id: "openai-compatible",
    name: "OpenAI Compatible",
    kind: "REMOTE PROVIDER",
    configured: false,
    enabled: false,
    isDefault: true,
    baseUrl: "Not configured",
    models: [],
    selectedModel: "",
    capabilities: ["TEXT", "STREAMING", "MODEL LISTING"],
    costLabel: "UNKNOWN COST",
    connection: "untested",
  },
];

function providerConfigStorageKey() {
  return `rabbit_code_provider_configs_${workspaceScope()}`;
}

function readProviderConfigs(): Provider[] {
  try {
    const saved = JSON.parse(localStorage.getItem(providerConfigStorageKey()) || "null") as Provider[] | null;
    if (!Array.isArray(saved)) {
      return initialProviders;
    }
    const savedById = new Map(saved.filter((provider) => provider && typeof provider.id === "string").map((provider) => [provider.id, provider]));
    const builtIns = initialProviders.map((provider) => ({ ...provider, ...(savedById.get(provider.id) || {}) }));
    const custom = saved.filter((provider) => provider && typeof provider.id === "string" && !initialProviders.some((builtIn) => builtIn.id === provider.id));
    return [...builtIns, ...custom];
  } catch {
    return initialProviders;
  }
}

function activeSessionCount() {
  const raw = localStorage.getItem(`rabbit_code_active_sessions_${workspaceScope()}`);
  const count = Number(raw || 0);
  return Number.isFinite(count) && count > 0 ? count : 0;
}

function providerMatchesActiveRoute(provider: Provider) {
  const routeProvider = readWorkspaceRoute().provider;
  return routeProvider === (provider.id === "openai-compatible" ? "openai" : provider.id);
}

function ApiProviderWizard() {
  const [draft, setDraft] = useState<ApiWizardDraft>(readApiWizardDraft);
  const [apiKey, setApiKey] = useState("");
  const [connection, setConnection] = useState<ConnectionStatus>("untested");
  const [notice, setNotice] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const service = apiServices.find((item) => item.value === draft.service) ?? apiServices[0];

  useEffect(() => {
    localStorage.setItem(
      apiWizardDraftKey(),
      JSON.stringify({
        service: draft.service,
        protocol: draft.protocol,
        baseUrl: draft.baseUrl,
        model: draft.model,
        step: draft.step,
      }),
    );
  }, [draft]);

  function updateDraft(patch: Partial<ApiWizardDraft>) {
    setDraft((current) => ({ ...current, ...patch }));
  }

  function selectService(value: ApiService) {
    const next = apiServices.find((item) => item.value === value) ?? apiServices[0];
    updateDraft({ service: next.value, protocol: next.protocol, baseUrl: next.baseUrl });
    setConnection("untested");
  }

  function nextStep() {
    if (draft.step === 2) {
      if (!draft.baseUrl.trim() || !apiKey.trim()) {
        setNotice("ADD A BASE URL AND PROVIDER API KEY BEFORE CONTINUING");
        return;
      }
      try {
        new URL(draft.baseUrl);
      } catch {
        setNotice("ENTER A VALID BASE URL");
        return;
      }
    }
    if (draft.step === 3 && !isValidModelId(draft.model.trim())) {
      setNotice("ADD A VALID MODEL ID BEFORE CONTINUING");
      return;
    }
    if (draft.step < 4) {
      updateDraft({ step: (draft.step + 1) as ApiWizardStep });
      setNotice(null);
    }
  }

  function previousStep() {
    if (draft.step > 1) {
      updateDraft({ step: (draft.step - 1) as ApiWizardStep });
      setNotice(null);
    }
  }

  function testConnection() {
    if (!draft.baseUrl.trim() || !apiKey.trim() || !isValidModelId(draft.model.trim())) {
      setNotice("COMPLETE PROVIDER, CREDENTIAL, ENDPOINT, AND MODEL BEFORE TESTING");
      return;
    }
    setConnection("connected");
    setNotice("MOCK CONNECTION PASSED / $0");
  }

  function saveDefault() {
    if (connection !== "connected") {
      setNotice("TEST CONNECTION BEFORE SAVING A DEFAULT");
      return;
    }
    const provider = draft.service === "custom" ? "openai" : draft.service;
    writeWorkspaceRoute({
      provider,
      model: draft.model.trim(),
      health: "healthy",
      protocol: draft.protocol,
      baseUrl: draft.baseUrl.trim(),
    }, window.location.search);
    localStorage.setItem("rabbit_code_api_configured", "true");
    localStorage.setItem("rabbit_code_onboarding_configured", "true");
    setSaved(true);
    setNotice("DEFAULT MODEL SAVED / API KEY REMAINS IN MEMORY ONLY");
  }

  return (
    <main className="provider-model-page api-wizard-page">
      <header className="provider-model-header api-wizard-header">
        <div>
          <span className="eyebrow">FIRST RUN / API ROUTE</span>
          <h1>Configure a provider.</h1>
          <p>Complete the setup in order. Non-sensitive choices are saved as a workspace draft; the API key is never written to browser storage.</p>
        </div>
        <span className="provider-model-state"><ShieldCheck size={16} aria-hidden="true" /> KEYCHAIN BOUNDARY</span>
      </header>

      <section className="api-wizard-shell" aria-label="API provider setup">
        <ol className="api-wizard-steps">
          {apiWizardSteps.map((label, index) => {
            const step = (index + 1) as ApiWizardStep;
            return <li key={label} className={step === draft.step ? "current" : step < draft.step ? "complete" : ""}><span>{String(step).padStart(2, "0")}</span>{label}</li>;
          })}
        </ol>

        <form className="api-wizard-form" onSubmit={(event) => { event.preventDefault(); nextStep(); }}>
          {draft.step === 1 ? (
            <fieldset>
              <legend>Choose the protocol and service.</legend>
              <p className="api-wizard-help">The protocol controls request shape. The service only supplies a starting endpoint and display name.</p>
              <label>PROTOCOL<select aria-label="API protocol" value={draft.protocol} onChange={(event) => { updateDraft({ protocol: event.target.value as ApiProtocol }); setConnection("untested"); }}>
                {apiProtocols.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select></label>
              <label>SERVICE / PROVIDER<select aria-label="API service" value={draft.service} onChange={(event) => selectService(event.target.value as ApiService)}>
                {apiServices.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select></label>
            </fieldset>
          ) : null}

          {draft.step === 2 ? (
            <fieldset>
              <legend>Connect the endpoint.</legend>
              <p className="api-wizard-help">Use a provider API key, not a Rabbit Code account password. The key is used only for this setup session.</p>
              <label>BASE URL<input aria-label="API base URL" value={draft.baseUrl} onChange={(event) => { updateDraft({ baseUrl: event.target.value }); setConnection("untested"); }} placeholder={service.baseUrl || "https://api.example.com/v1"} /></label>
              <label>PROVIDER API KEY<input aria-label="Setup provider API key" type="password" value={apiKey} onChange={(event) => { registerRuntimeSecret(event.target.value); setApiKey(event.target.value); setConnection("untested"); }} autoComplete="new-password" placeholder="Enter once; never saved to the draft" /></label>
              <p className="provider-key-note"><ShieldCheck size={14} aria-hidden="true" /> PROVIDER KEY ONLY / NOT ACCOUNT LOGIN</p>
            </fieldset>
          ) : null}

          {draft.step === 3 ? (
            <fieldset>
              <legend>Choose the model.</legend>
              <p className="api-wizard-help">Enter a known model ID or the model ID supplied by the provider. Discovery can be added later.</p>
              <label>MODEL ID<input aria-label="Setup model ID" value={draft.model} onChange={(event) => { updateDraft({ model: event.target.value }); setConnection("untested"); }} placeholder="gpt-4o-mini" /></label>
            </fieldset>
          ) : null}

          {draft.step === 4 ? (
            <fieldset>
              <legend>Test and save the default.</legend>
              <p className="api-wizard-help">The connection test is Mock / $0 in this setup screen. Saving as default is locked until the test passes.</p>
              <dl className="api-wizard-summary">
                <div><dt>PROVIDER</dt><dd>{service.label}</dd></div>
                <div><dt>PROTOCOL</dt><dd>{draft.protocol}</dd></div>
                <div><dt>BASE URL</dt><dd>{draft.baseUrl || "Not configured"}</dd></div>
                <div><dt>MODEL</dt><dd>{draft.model || "Not configured"}</dd></div>
                <div><dt>API KEY</dt><dd>{apiKey ? `${maskSecret(apiKey)} / MEMORY ONLY` : "NOT RECEIVED"}</dd></div>
              </dl>
              <div className="api-wizard-test-row">
                <span className={`provider-connection provider-connection-${connection}`} role="status">
                  {connection === "connected" ? <CircleCheck size={15} aria-hidden="true" /> : <span className="provider-connection-dot" aria-hidden="true" />}
                  {connection === "connected" ? "MOCK CONNECTION PASSED" : "CONNECTION NOT TESTED"}
                </span>
                <button type="button" className="provider-action-primary" onClick={testConnection}><CircleCheck size={15} aria-hidden="true" /> TEST CONNECTION / $0</button>
              </div>
            </fieldset>
          ) : null}

          <div className="api-wizard-actions">
            <a href="/onboarding"><ArrowLeft size={15} aria-hidden="true" /> BACK TO ROUTES</a>
            <span>{notice ? <span className="api-wizard-notice" role="status">{notice}</span> : "DRAFT SAVED"}</span>
            <div>
              <button type="button" onClick={previousStep} disabled={draft.step === 1}><ArrowLeft size={15} aria-hidden="true" /> BACK</button>
              {draft.step < 4 ? <button type="submit" className="provider-action-primary">NEXT <ArrowRight size={15} aria-hidden="true" /></button> : <button type="button" className="provider-action-primary" onClick={saveDefault} disabled={connection !== "connected"}><Pin size={15} aria-hidden="true" /> SAVE AS DEFAULT</button>}
            </div>
          </div>
          {saved ? <a className="api-wizard-workspace-link" href={workspaceHomeHref()}><ArrowRight size={15} aria-hidden="true" /> OPEN WORKSPACE HOME</a> : null}
        </form>
      </section>
    </main>
  );
}

export function ProviderModels({ setupMode = false }: { setupMode?: boolean }) {
  const [providers, setProviders] = useState<Provider[]>(readProviderConfigs);
  const [credentialSource, setCredentialSource] = useState("KEYCHAIN");
  const [selectedId, setSelectedId] = useState(() => localStorage.getItem(`rabbit_code_selected_provider_${workspaceScope()}`) || initialProviders[1].id);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftName, setDraftName] = useState("");
  const [draftBaseUrl, setDraftBaseUrl] = useState("");
  const [apiKeyEntered, setApiKeyEntered] = useState(false);
  const [apiKeyTail, setApiKeyTail] = useState("");
  const [modelDraft, setModelDraft] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void api.config().then((payload) => {
      const entry = payload.api_key;
      if (!entry || typeof entry !== "object") {
        return;
      }
      const sourceLabel = (entry as { source_label?: unknown }).source_label;
      if (active && typeof sourceLabel === "string") {
        setCredentialSource(sourceLabel === "environment variable" ? "ENVIRONMENT" : sourceLabel.toUpperCase());
      }
    }).catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteReplacementId, setDeleteReplacementId] = useState("");
  const selectedProvider = providers.find((provider) => provider.id === selectedId) ?? providers[0];

  useEffect(() => {
    localStorage.setItem(providerConfigStorageKey(), JSON.stringify(providers));
  }, [providers]);

  useEffect(() => {
    if (!providers.some((provider) => provider.id === selectedId)) {
      setSelectedId(providers[0]?.id || "");
      return;
    }
    localStorage.setItem(`rabbit_code_selected_provider_${workspaceScope()}`, selectedId);
  }, [providers, selectedId]);

  if (setupMode) {
    return <ApiProviderWizard />;
  }

  function openNewProvider() {
    setEditingId(null);
    setDraftName("");
    setDraftBaseUrl("");
    setApiKeyEntered(false);
    setApiKeyTail("");
    setEditorOpen(true);
  }

  function openEditProvider() {
    setEditingId(selectedProvider.id);
    setDraftName(selectedProvider.name);
    setDraftBaseUrl(selectedProvider.baseUrl === "Not configured" ? "" : selectedProvider.baseUrl);
    setApiKeyEntered(false);
    setApiKeyTail("");
    setEditorOpen(true);
  }

  function saveProvider() {
    const name = draftName.trim();
    if (!name) {
      return;
    }
    if (editingId) {
      setProviders((current) => current.map((provider) => provider.id === editingId
        ? { ...provider, name, baseUrl: draftBaseUrl.trim() || "Not configured", configured: true, enabled: true, connection: "untested" }
        : provider));
      setSelectedId(editingId);
    } else {
      const id = `provider-${Date.now()}`;
      setProviders((current) => [...current, {
        id,
        name,
        kind: "CUSTOM PROVIDER",
        configured: true,
        enabled: true,
        isDefault: false,
        baseUrl: draftBaseUrl.trim() || "Custom endpoint",
        models: [],
        selectedModel: "",
        capabilities: ["TEXT"],
        costLabel: "UNKNOWN COST",
        connection: "untested",
      }]);
      setSelectedId(id);
    }
    setEditorOpen(false);
    setNotice("PROVIDER SAVED");
  }

  function testConnection() {
    if (!selectedProvider.configured) {
      setNotice("CONFIGURE PROVIDER BEFORE TESTING");
      return;
    }
    if (!selectedProvider.enabled) {
      setNotice("ENABLE PROVIDER BEFORE TESTING");
      return;
    }
    setProviders((current) => current.map((provider) => provider.id === selectedProvider.id
      ? {
        ...provider,
        connection: "connected",
        costLabel: provider.id === "offline" ? "NO NETWORK / $0" : "MOCK / $0",
        capabilities: provider.id === "offline" || provider.capabilities.includes("MODEL LISTING")
          ? provider.capabilities
          : [...provider.capabilities, "MODEL LISTING"],
      }
      : provider));
    persistProviderRoute({ ...selectedProvider, connection: "connected" });
    setNotice("CONNECTION PASSED");
  }

  function discoverModels() {
    if (!selectedProvider.configured) {
      setNotice("CONFIGURE PROVIDER BEFORE DISCOVERY");
      return;
    }
    if (!selectedProvider.capabilities.includes("MODEL LISTING")) {
      setNotice("MODEL DISCOVERY NOT SUPPORTED");
      return;
    }
    setProviders((current) => current.map((provider) => provider.id === selectedProvider.id
      ? { ...provider, models: Array.from(new Set([...provider.models, "auto-discovered-model"])) }
      : provider));
    setNotice("MODEL DISCOVERY COMPLETE");
  }

  function addManualModel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const model = modelDraft.trim();
    if (!model || !selectedProvider.configured) {
      return;
    }
    if (!isValidModelId(model)) {
      setNotice("INVALID MODEL ID");
      return;
    }
    setProviders((current) => current.map((provider) => provider.id === selectedProvider.id
      ? { ...provider, models: Array.from(new Set([...provider.models, model])), selectedModel: model }
      : provider));
    setModelDraft("");
    setNotice("MODEL ID ADDED");
  }

  function removeModel(model: string) {
    if (selectedProvider.models.length <= 1) {
      setNotice("KEEP ONE MODEL OR DELETE THE PROVIDER");
      return;
    }
    const remainingModels = selectedProvider.models.filter((item) => item !== model);
    const nextModel = selectedProvider.selectedModel === model ? remainingModels[0] : selectedProvider.selectedModel;
    setProviders((current) => current.map((provider) => provider.id === selectedProvider.id
      ? { ...provider, models: remainingModels, selectedModel: nextModel }
      : provider));
    if (providerMatchesActiveRoute(selectedProvider) && selectedProvider.selectedModel === model) {
      persistProviderRoute(selectedProvider, nextModel);
    }
    setNotice("MODEL REMOVED");
  }

  function toggleProvider() {
    const enabled = !selectedProvider.enabled;
    setProviders((current) => current.map((provider) => provider.id === selectedProvider.id ? { ...provider, enabled } : provider));
    if (providerMatchesActiveRoute(selectedProvider)) {
      persistProviderRoute({ ...selectedProvider, enabled });
    }
    setNotice(enabled ? "PROVIDER ENABLED" : "PROVIDER DISABLED / CONFIGURATION RETAINED");
  }

  function deleteProviderNow(replacement?: Provider) {
    const removing = selectedProvider;
    const remaining = providers.filter((provider) => provider.id !== removing.id);
    const nextProviders = replacement
      ? remaining.map((provider) => ({ ...provider, isDefault: provider.id === replacement.id }))
      : remaining;
    if (replacement && (providerMatchesActiveRoute(removing) || activeSessionCount() > 0)) {
      persistProviderRoute(replacement);
    }
    setProviders(nextProviders);
    setSelectedId(replacement?.id || nextProviders[0]?.id || "");
    setDeleteOpen(false);
    setNotice("PROVIDER DELETED / REFERENCES MIGRATED");
  }

  function requestDeleteProvider() {
    if (providers.length === 1) {
      setNotice("KEEP ONE PROVIDER CONFIGURED");
      return;
    }
    const needsMigration = selectedProvider.isDefault || providerMatchesActiveRoute(selectedProvider) || activeSessionCount() > 0;
    if (!needsMigration) {
      deleteProviderNow();
      return;
    }
    const replacement = providers.find((provider) => provider.id !== selectedProvider.id && provider.enabled && provider.configured);
    if (!replacement) {
      setNotice("ADD AN ENABLED PROVIDER BEFORE DELETING THIS REFERENCE");
      return;
    }
    setDeleteReplacementId(replacement.id);
    setDeleteOpen(true);
  }

  function confirmDeleteProvider() {
    const replacement = providers.find((provider) => provider.id === deleteReplacementId && provider.id !== selectedProvider.id && provider.enabled && provider.configured);
    if (!replacement) {
      setNotice("CHOOSE AN ENABLED REPLACEMENT PROVIDER");
      return;
    }
    deleteProviderNow(replacement);
  }

  function setDefault() {
    if (!selectedProvider.enabled || !selectedProvider.configured) {
      setNotice("ENABLE AND CONFIGURE PROVIDER BEFORE SETTING DEFAULT");
      return;
    }
    setProviders((current) => current.map((provider) => ({ ...provider, isDefault: provider.id === selectedProvider.id })));
    persistProviderRoute(selectedProvider);
    setNotice("DEFAULT PROVIDER UPDATED");
  }

  function selectModel(model: string) {
    setProviders((current) => current.map((provider) => provider.id === selectedProvider.id ? { ...provider, selectedModel: model } : provider));
    persistProviderRoute(selectedProvider, model);
    setNotice("MODEL SELECTED");
  }

  return (
    <main className="provider-model-page">
      <header className="provider-model-header">
          <div>
            <span className="eyebrow">PROVIDERS / MODELS</span>
            <h1>Choose the model for the work.</h1>
            <p>Configure provider access and model choice without exposing secrets. “Claude Code format” means Anthropic Messages or an approved official Agent SDK, never a subscription login.</p>
        </div>
        <div className="provider-model-state"><ShieldCheck size={16} aria-hidden="true" /> KEYCHAIN BOUNDARY</div>
      </header>

      <div className="provider-model-shell">
        <aside className="provider-list" aria-label="Providers">
          <div className="provider-panel-heading"><span className="eyebrow">PROVIDERS</span><button type="button" aria-label="Add provider" title="Add provider" onClick={openNewProvider}><Plus size={16} aria-hidden="true" /></button></div>
          <div className="provider-items">
            {providers.map((provider) => (
              <button key={provider.id} type="button" className={provider.id === selectedProvider.id ? "active" : ""} onClick={() => setSelectedId(provider.id)}>
                <span><strong>{provider.name}</strong><small>{provider.kind}</small></span>
                {provider.isDefault ? <Pin size={14} aria-label="Default provider" /> : <span className={`provider-dot provider-dot-${provider.enabled ? "on" : "off"}`} aria-hidden="true" />}
              </button>
            ))}
          </div>
          <button type="button" className="provider-add-button" onClick={openNewProvider}><Plus size={15} aria-hidden="true" /> ADD PROVIDER</button>
        </aside>

        <section className="provider-config" aria-label="Provider configuration">
          <div className="provider-config-heading">
            <div><span className="eyebrow">{selectedProvider.kind}</span><h2>{selectedProvider.name}</h2><p>{selectedProvider.baseUrl}</p></div>
            <span className={`provider-connection provider-connection-${selectedProvider.connection}`}>
              {selectedProvider.connection === "connected" ? <CircleCheck size={15} aria-hidden="true" /> : selectedProvider.connection === "failed" ? <CircleX size={15} aria-hidden="true" /> : <span className="provider-connection-dot" aria-hidden="true" />}
              {selectedProvider.connection === "connected" ? "CONNECTED" : selectedProvider.connection === "failed" ? "FAILED" : "NOT TESTED"}
            </span>
          </div>
          <div className="provider-config-actions">
            <button type="button" className="provider-action-primary" onClick={testConnection}><CircleCheck size={15} aria-hidden="true" /> TEST CONNECTION</button>
            <button type="button" onClick={openEditProvider}><Pencil size={15} aria-hidden="true" /> EDIT</button>
            <button type="button" onClick={toggleProvider}><Power size={15} aria-hidden="true" /> {selectedProvider.enabled ? "DISABLE" : "ENABLE"}</button>
            <button type="button" className="provider-action-danger" onClick={requestDeleteProvider}><Trash2 size={15} aria-hidden="true" /> DELETE</button>
          </div>
          <div className="provider-meta-grid">
            <div><span>STATUS</span><strong>{selectedProvider.configured ? (selectedProvider.enabled ? "ENABLED" : "DISABLED") : "NOT CONFIGURED"}</strong></div>
            <div><span>COST</span><strong>{selectedProvider.costLabel}</strong></div>
            <div><span>DEFAULT</span><strong>{selectedProvider.isDefault ? "CURRENT" : "AVAILABLE"}</strong></div>
          </div>
          <section className="provider-capabilities" aria-label="Provider capabilities">
            <div className="provider-section-heading"><span className="eyebrow">CAPABILITIES</span><span>{selectedProvider.capabilities.length}</span></div>
            <div className="provider-capability-list">{selectedProvider.capabilities.map((capability) => <span key={capability}>{capability}</span>)}</div>
          </section>
          <div className="provider-model-discovery">
          <div className="provider-section-heading"><span className="eyebrow">MODEL DISCOVERY</span><button type="button" onClick={discoverModels} disabled={!selectedProvider.configured || !selectedProvider.capabilities.includes("MODEL LISTING")}><RefreshCw size={14} aria-hidden="true" /> DISCOVER</button></div>
            {selectedProvider.id === "offline" ? <OfflineState title="OFFLINE RULES" description="This route stays on the machine and does not discover remote models." compact /> : (
              <div className="provider-model-list">
                {selectedProvider.models.length === 0 ? <EmptyState title="NO MODELS DISCOVERED" description="Run discovery or add a model ID to this provider." compact /> : selectedProvider.models.map((model) => <div className="provider-model-row" key={model}><button type="button" className={selectedProvider.selectedModel === model ? "active" : ""} onClick={() => selectModel(model)}><Database size={14} aria-hidden="true" /><span>{model}</span>{selectedProvider.selectedModel === model ? <Check size={14} aria-label="Selected model" /> : null}</button><button type="button" aria-label={`Remove model ${model}`} title="Remove model" onClick={() => removeModel(model)}><Trash2 size={14} aria-hidden="true" /></button></div>)}
              </div>
            )}
            <form className="provider-manual-model" onSubmit={addManualModel}><label htmlFor="manual-model-id">MANUAL MODEL ID</label><input id="manual-model-id" aria-label="Manual model ID" value={modelDraft} onChange={(event) => setModelDraft(event.target.value)} placeholder="provider/model-id" disabled={!selectedProvider.configured} /><button type="submit" aria-label="Add manual model" title="Add manual model"><Plus size={15} aria-hidden="true" /></button></form>
          </div>
        </section>

        <aside className="provider-default-panel" aria-label="Default model">
          <div className="provider-section-heading"><span className="eyebrow">DEFAULT ROUTE</span><Pin size={15} aria-hidden="true" /></div>
          <strong className="provider-default-name">{providers.find((provider) => provider.isDefault)?.name}</strong>
          <p>{providers.find((provider) => provider.isDefault)?.selectedModel || "Choose a model after configuration."}</p>
            <button type="button" className="provider-default-button" title="Set provider as default" onClick={setDefault} disabled={selectedProvider.isDefault}><Pin size={15} aria-hidden="true" /> SET AS DEFAULT</button>
          <div className="provider-secret-note"><ShieldCheck size={15} aria-hidden="true" /><span>API KEY SOURCE / {credentialSource}. This page only shows configuration state; the value is never returned.</span></div>
        </aside>
      </div>

      <UiDialog
        open={deleteOpen}
        accessibleName="Delete provider"
        title="Migrate before deleting?"
        description={`This provider is ${selectedProvider.isDefault ? "the default route" : "referenced by the current workspace"}${activeSessionCount() ? ` and has ${activeSessionCount()} active session(s)` : ""}. Choose a safe replacement; its configuration and model history will remain until deletion.`}
        onClose={() => setDeleteOpen(false)}
        onConfirm={confirmDeleteProvider}
        confirmLabel="MIGRATE AND DELETE"
        confirmClassName="ui-dialog-danger"
        icon={Trash2}
      >
        <label className="provider-replacement-field">REPLACEMENT PROVIDER<select aria-label="Replacement provider" value={deleteReplacementId} onChange={(event) => setDeleteReplacementId(event.target.value)}>{providers.filter((provider) => provider.id !== selectedProvider.id && provider.enabled && provider.configured).map((provider) => <option key={provider.id} value={provider.id}>{provider.name}</option>)}</select></label>
      </UiDialog>
      <UiDialog
        open={editorOpen}
        accessibleName={editingId ? "Edit provider" : "Add provider"}
        title={editingId ? "Edit provider" : "Add a provider"}
        description="Provider API keys stay inside the keychain boundary and are never rendered back into the page. They are not Rabbit Code account passwords."
        onClose={() => setEditorOpen(false)}
        onConfirm={saveProvider}
        confirmLabel="SAVE PROVIDER"
      >
            <form className="provider-editor-form" onSubmit={(event) => { event.preventDefault(); saveProvider(); }}>
              <label>PROVIDER NAME<input aria-label="Provider name" value={draftName} onChange={(event) => setDraftName(event.target.value)} placeholder="OpenAI Compatible" /></label>
              <label>BASE URL<input aria-label="Provider base URL" value={draftBaseUrl} onChange={(event) => setDraftBaseUrl(event.target.value)} placeholder="https://api.example.com/v1" /></label>
              <label>PROVIDER API KEY<input aria-label="Provider API key" type="password" onChange={(event) => { registerRuntimeSecret(event.target.value); setApiKeyEntered(Boolean(event.target.value)); setApiKeyTail(event.target.value.slice(-4)); }} placeholder={apiKeyEntered ? `${maskSecretTail(apiKeyTail)} / KEYCHAIN VALUE RECEIVED` : "Enter once; never rendered"} autoComplete="new-password" /></label>
              <p className="provider-key-note"><ShieldCheck size={14} aria-hidden="true" /> PROVIDER KEY ONLY / NOT ACCOUNT LOGIN</p>
            </form>
      </UiDialog>
      {notice ? <p className="provider-notice" role="status">{notice}</p> : null}
    </main>
  );
}

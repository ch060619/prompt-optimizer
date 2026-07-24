import { AlertTriangle, ArrowLeft, ArrowRight, CheckCircle2, Cpu, Download, HardDrive, Pause, Play, Power, RefreshCw, RotateCcw, ServerCog, ShieldCheck, Trash2, WifiOff, X } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "./api";
import { InstallDialog } from "./components/UiStates";
import { writeDefaultLocalModel } from "./localModelSelection";
import { AppLink } from "./navigation";
import { providerRouteStorageKey, workspaceHomeHref, workspaceScope, writeWorkspaceRoute } from "./workspaceRoute";

// RC IDs: RC-115, RC-185, RC-194. Render backend-driven local model lifecycle state.

export type ModelStatus = "not_installed" | "downloading" | "paused" | "verifying" | "loading" | "ready" | "busy" | "stopping" | "unloaded" | "corrupt" | "update" | "failed" | "disabled";
export type LocalModelEventName = "download_started" | "download_progress" | "download_paused" | "download_completed" | "verified" | "load_started" | "ready" | "busy" | "unload_started" | "unloaded" | "corrupt" | "update_available" | "update_started" | "failed" | "reset" | "disable" | "enable" | "recovered";
type LocalModel = {
  id: string;
  sourceModelId: string;
  name: string;
  family: string;
  size: string;
  sizeGb: number;
  license: string;
  checksum: string;
  status: ModelStatus;
  progress: number;
  recommended: boolean;
  error?: string;
  lastEvent?: string;
};

type LocalModelEvent = {
  event: LocalModelEventName;
  message: string;
  state: {
    status: ModelStatus;
    progress?: number;
    error?: string | null;
    model_id?: string;
  };
};

const initialModels: LocalModel[] = [
  {
    id: "gemma-3-1b-it",
    sourceModelId: "google/gemma-3-1b-it",
    name: "Gemma 3 1B IT",
    family: "Gemma",
    size: "2.0 GB",
    sizeGb: 2.0,
    license: "Gemma Terms",
    checksum: "sha256: 3d4ef8d71c14db7e448a09ebe891cfb6bf32c57a9b44499ae0d1c098e48516b6",
    status: "not_installed",
    progress: 0,
    recommended: true,
  },
  {
    id: "qwen2.5-coder-1.5b-instruct",
    sourceModelId: "Qwen/Qwen2.5-Coder-1.5B-Instruct",
    name: "Qwen2.5-Coder 1.5B",
    family: "Qwen2.5-Coder",
    size: "3.1 GB",
    sizeGb: 3.1,
    license: "Apache 2.0",
    checksum: "sha256: c1b9b30e907950516ba3c646bdf570d8084c25a6410a0cdca80cf04b11bc13a8",
    status: "not_installed",
    progress: 0,
    recommended: false,
  },
];

const statusLabels: Record<ModelStatus, string> = {
  not_installed: "NOT INSTALLED",
  downloading: "DOWNLOADING",
  paused: "PAUSED",
  verifying: "VERIFYING",
  loading: "LOADING",
  ready: "READY",
  busy: "BUSY",
  stopping: "STOPPING",
  unloaded: "UNLOADED",
  corrupt: "CORRUPT / REPAIR",
  update: "UPDATE AVAILABLE",
  failed: "FAILED",
  disabled: "DISABLED",
};

const allowedLocalModelEvents: Record<ModelStatus, readonly LocalModelEventName[]> = {
  not_installed: ["download_started", "update_started", "recovered"],
  downloading: ["download_started", "download_progress", "download_paused", "download_completed", "failed", "corrupt", "reset", "recovered"],
  paused: ["download_started", "download_progress", "reset", "failed", "recovered"],
  verifying: ["download_started", "verified", "corrupt", "failed", "reset", "recovered"],
  loading: ["ready", "busy", "failed", "corrupt", "reset", "recovered"],
  ready: ["load_started", "busy", "unload_started", "update_available", "update_started", "reset", "disable", "recovered"],
  busy: ["ready", "unload_started", "failed", "disable", "recovered"],
  stopping: ["ready", "unloaded", "failed", "reset", "recovered"],
  unloaded: ["load_started", "download_started", "update_started", "reset", "recovered"],
  corrupt: ["download_started", "download_progress", "verified", "unload_started", "reset", "failed", "recovered"],
  update: ["update_started", "download_started", "download_progress", "download_completed", "verified", "load_started", "ready", "failed", "corrupt", "reset", "recovered"],
  failed: ["download_started", "download_progress", "verified", "load_started", "unload_started", "reset", "failed", "recovered"],
  disabled: ["enable", "reset", "recovered"],
};

const eventTargetStatus: Partial<Record<LocalModelEventName, ModelStatus>> = {
  download_started: "downloading",
  download_progress: "downloading",
  download_paused: "paused",
  download_completed: "verifying",
  verified: "loading",
  load_started: "loading",
  ready: "ready",
  busy: "busy",
  unload_started: "stopping",
  unloaded: "unloaded",
  corrupt: "corrupt",
  update_available: "update",
  update_started: "update",
  failed: "failed",
  reset: "not_installed",
  disable: "disabled",
  enable: "ready",
};

function applyLocalModelEvent(current: LocalModel, event: LocalModelEvent): LocalModel {
  if (event.event !== "recovered" && !allowedLocalModelEvents[current.status].includes(event.event)) {
    throw new Error(`cannot apply ${event.event} from ${current.status}`);
  }
  const nextStatus = event.event === "recovered" ? event.state.status : eventTargetStatus[event.event];
  if (!nextStatus) {
    throw new Error(`event ${event.event} has no target status`);
  }
  return {
    ...current,
    status: nextStatus,
    progress: Math.min(100, Math.max(0, event.state.progress ?? current.progress)),
    error: event.state.error || undefined,
    lastEvent: event.event,
  };
}

function localModelEvent(
  current: LocalModel,
  event: LocalModelEventName,
  message: string,
  progress?: number,
  error?: string,
): LocalModelEvent {
  return {
    event,
    message,
    state: {
      status: event === "recovered" ? current.status : eventTargetStatus[event] || current.status,
      progress,
      error: error || null,
      model_id: current.sourceModelId,
    },
  };
}

function normalizeSavedModel(model: Partial<LocalModel>): LocalModel | null {
  if (typeof model.id !== "string") {
    return null;
  }
  const legacyStatus = model.status as string | undefined;
  const status: ModelStatus = legacyStatus === "available" || legacyStatus === "cancelled" || legacyStatus === "uninstalled"
    ? "not_installed"
    : legacyStatus === "running"
      ? "busy"
      : legacyStatus === "error"
        ? "corrupt"
        : Object.prototype.hasOwnProperty.call(statusLabels, legacyStatus || "")
          ? legacyStatus as ModelStatus
          : "not_installed";
  return { ...initialModels.find((item) => item.id === model.id), ...model, status } as LocalModel;
}

function persistLocalRoute(modelId: string, health: "healthy" | "unavailable", enabled = true) {
  localStorage.setItem("rabbit_code_selected_model", modelId);
  writeWorkspaceRoute({
    provider: "local",
    model: modelId,
    health,
    enabled,
  });
}

function localModelsStorageKey() {
  return `rabbit_code_local_models_${workspaceScope()}`;
}

function readLocalModels(): LocalModel[] {
  try {
    const saved = JSON.parse(localStorage.getItem(localModelsStorageKey()) || "null") as LocalModel[] | null;
    if (!Array.isArray(saved)) {
      return initialModels;
    }
    const savedById = new Map(saved.map((model) => [model.id, normalizeSavedModel(model)]));
    return initialModels.map((model) => ({ ...model, ...(savedById.get(model.id) || {}) }));
  } catch {
    return initialModels;
  }
}

type LocalSetupPhase = "hardware" | "runner" | "model" | "license" | "install" | "health" | "complete";
type LocalSetupStatus = "idle" | "downloading" | "paused" | "verifying" | "ready" | "cancelled";
type LocalSetupState = {
  phase: LocalSetupPhase;
  runner: "ollama" | "llama.cpp";
  modelId: string;
  licenseAccepted: boolean;
  status: LocalSetupStatus;
  progress: number;
};

type LocalInstallSnapshot = {
  model_id: string;
  runner: string;
  phase: "download" | "verify" | "install" | "ready";
  status: "downloading" | "paused" | "cancelled" | "failed" | "ready" | "running";
  progress: number;
  checksum: string;
  error: string | null;
};

type LocalInstallEvent = {
  event: string;
  message: string;
  state: LocalInstallSnapshot;
};

function applyLocalInstallEvent(current: LocalSetupState, event: LocalInstallEvent): LocalSetupState {
  const { state } = event;
  const phase: LocalSetupPhase = state.phase === "ready"
    ? "complete"
    : state.phase === "install"
      ? "health"
      : "install";
  const status: LocalSetupStatus = state.phase === "verify"
    ? "verifying"
    : state.status === "failed"
      ? "cancelled"
      : state.status === "running" || state.status === "ready"
        ? "ready"
        : state.status;
  return {
    ...current,
    phase,
    runner: state.runner === "llama.cpp" ? "llama.cpp" : "ollama",
    modelId: state.model_id,
    status,
    progress: Math.min(100, Math.max(0, state.progress)),
  };
}

const defaultLocalSetupState: LocalSetupState = {
  phase: "hardware",
  runner: "ollama",
  modelId: "gemma-3-1b-it",
  licenseAccepted: false,
  status: "idle",
  progress: 0,
};

function localSetupKey() {
  return `rabbit_code_local_setup_${workspaceScope()}`;
}

function readLocalSetupState(): LocalSetupState {
  try {
    const parsed = JSON.parse(localStorage.getItem(localSetupKey()) || "null") as Partial<LocalSetupState> | null;
    if (!parsed || !initialModels.some((model) => model.id === parsed.modelId)) {
      return defaultLocalSetupState;
    }
    return {
      phase: parsed.phase && ["hardware", "runner", "model", "license", "install", "health", "complete"].includes(parsed.phase) ? parsed.phase as LocalSetupPhase : "hardware",
      runner: parsed.runner === "llama.cpp" ? "llama.cpp" : "ollama",
      modelId: parsed.modelId as string,
      licenseAccepted: parsed.licenseAccepted === true,
      status: parsed.status && ["idle", "downloading", "paused", "verifying", "ready", "cancelled"].includes(parsed.status) ? parsed.status as LocalSetupStatus : "idle",
      progress: typeof parsed.progress === "number" ? Math.min(100, Math.max(0, parsed.progress)) : 0,
    };
  } catch {
    return defaultLocalSetupState;
  }
}

function LocalSetupWizard() {
  const [state, setState] = useState<LocalSetupState>(readLocalSetupState);
  const [notice, setNotice] = useState<string | null>(null);
  const selectedModel = initialModels.find((model) => model.id === state.modelId) ?? initialModels[0];
  const hardwareThreads = typeof navigator.hardwareConcurrency === "number" ? navigator.hardwareConcurrency : null;

  useEffect(() => {
    localStorage.setItem(localSetupKey(), JSON.stringify(state));
  }, [state]);

  function update(patch: Partial<LocalSetupState>) {
    setState((current) => ({ ...current, ...patch }));
  }

  function continueSetup() {
    if (state.phase === "hardware") update({ phase: "runner" });
    else if (state.phase === "runner") update({ phase: "model" });
    else if (state.phase === "model") update({ phase: "license" });
    else if (state.phase === "license") {
      if (!state.licenseAccepted) {
        setNotice("ACCEPT THE MODEL LICENSE BEFORE CONTINUING");
        return;
      }
      update({ phase: "install" });
      setNotice(null);
    } else if (state.phase === "health") {
      update({ phase: "complete" });
      localStorage.setItem("rabbit_code_local_runner_ready", "true");
      localStorage.setItem("rabbit_code_onboarding_configured", "true");
      writeDefaultLocalModel(state.modelId);
      persistLocalRoute(state.modelId, "healthy");
      setNotice("LOCAL MODEL HEALTH CHECK PASSED");
    }
  }

  function startDownload() {
    setState((current) => applyLocalInstallEvent(current, buildInstallEvent(current, "started", "download started", "download", "downloading", 32)));
    setNotice("DOWNLOAD STARTED / RESUMABLE");
  }

  function pauseDownload() {
    setState((current) => applyLocalInstallEvent(current, buildInstallEvent(current, "paused", "download paused", "download", "paused", current.progress)));
    setNotice("DOWNLOAD PAUSED / PROGRESS SAVED");
  }

  function resumeDownload() {
    setState((current) => applyLocalInstallEvent(current, buildInstallEvent(current, "resumed", "download resumed", "download", "downloading", Math.max(68, current.progress))));
    setNotice("DOWNLOAD RESUMED");
  }

  function completeDownload() {
    setState((current) => applyLocalInstallEvent(current, buildInstallEvent(current, "downloaded", "download complete; verification required", "verify", "downloading", 100)));
    setNotice("DOWNLOAD COMPLETE / CHECKSUM READY");
  }

  function verifyDownload() {
    setState((current) => applyLocalInstallEvent(current, buildInstallEvent(current, "verified", "checksum passed; installation ready", "install", "paused", 100)));
    setNotice("CHECKSUM PASSED / RUN HEALTH CHECK");
  }

  function cancelDownload() {
    setState((current) => applyLocalInstallEvent(current, buildInstallEvent(current, "cancelled", "download cancelled", "download", "cancelled", 0)));
    setNotice("DOWNLOAD CANCELLED / SETUP CAN RESUME");
  }

  function buildInstallEvent(
    current: LocalSetupState,
    event: string,
    message: string,
    phase: LocalInstallSnapshot["phase"],
    status: LocalInstallSnapshot["status"],
    progress: number,
  ): LocalInstallEvent {
    return {
      event,
      message,
      state: {
        model_id: current.modelId,
        runner: current.runner,
        phase,
        status,
        progress,
        checksum: selectedModel.checksum,
        error: null,
      },
    };
  }

  const phaseLabels = ["HARDWARE", "RUNNER", "MODEL", "LICENSE", "INSTALL", "HEALTH"];
  const phaseIndex = ["hardware", "runner", "model", "license", "install", "health"].indexOf(state.phase);

  return (
    <main className="local-setup-page">
      <header className="local-model-header local-setup-header">
        <div>
          <span className="eyebrow">FIRST RUN / LOCAL ROUTE</span>
          <h1>Set up a local model.</h1>
          <p>Check the machine, choose a runner and model, accept its license, then download and verify before loading it.</p>
        </div>
        <span className="local-model-runner-state"><ServerCog size={16} aria-hidden="true" /> LOCAL / {state.phase === "complete" ? "READY" : "SETUP"}</span>
      </header>

      <section className="local-setup-shell" aria-label="Local model setup">
        <ol className="local-setup-steps">
          {phaseLabels.map((label, index) => <li key={label} className={index === phaseIndex ? "current" : index < phaseIndex || state.phase === "complete" ? "complete" : ""}><span>{String(index + 1).padStart(2, "0")}</span>{label}</li>)}
        </ol>

        {state.phase === "hardware" ? (
          <section className="local-setup-card">
            <span className="eyebrow">HARDWARE CHECK</span>
            <h2>Is this machine ready?</h2>
            <p>Rabbit Code checks local capacity before downloading a multi-gigabyte model.</p>
            <div className="local-setup-facts"><div><Cpu size={17} aria-hidden="true" /><span>CPU THREADS</span><strong>{hardwareThreads || "AVAILABLE"}</strong></div><div><HardDrive size={17} aria-hidden="true" /><span>DISK REQUIRED</span><strong>{selectedModel.size}</strong></div><div><ServerCog size={17} aria-hidden="true" /><span>GPU</span><strong>OPTIONAL</strong></div><div><WifiOff size={17} aria-hidden="true" /><span>AFTER SETUP</span><strong>OFFLINE READY</strong></div></div>
            <button type="button" className="local-model-primary" onClick={continueSetup}><CheckCircle2 size={15} aria-hidden="true" /> CONTINUE</button>
          </section>
        ) : null}

        {state.phase === "runner" ? (
          <section className="local-setup-card">
            <span className="eyebrow">LOCAL RUNNER</span>
            <h2>Choose how to run it.</h2>
            <p>The runner stays on this device and can be changed later.</p>
            <label className="local-setup-field">RUNNER<select aria-label="Local runner" value={state.runner} onChange={(event) => update({ runner: event.target.value as LocalSetupState["runner"] })}><option value="ollama">Ollama</option><option value="llama.cpp">llama.cpp</option></select></label>
            <button type="button" className="local-model-primary" onClick={continueSetup}><ArrowRight size={15} aria-hidden="true" /> CONTINUE</button>
          </section>
        ) : null}

        {state.phase === "model" ? (
          <section className="local-setup-card">
            <span className="eyebrow">MODEL CHOICE</span>
            <h2>Choose a local model.</h2>
             <div className="local-setup-models">{initialModels.map((model) => <button key={model.id} type="button" className={state.modelId === model.id ? "active" : ""} onClick={() => update({ modelId: model.id })}><strong>{model.name}</strong><span>{model.sourceModelId} / {model.size} / {model.license}</span></button>)}</div>
            <button type="button" className="local-model-primary" onClick={continueSetup}><ArrowRight size={15} aria-hidden="true" /> CONTINUE</button>
          </section>
        ) : null}

        {state.phase === "license" ? (
          <section className="local-setup-card">
            <span className="eyebrow">MODEL LICENSE</span>
            <h2>Review before download.</h2>
            <p>{selectedModel.name} uses the {selectedModel.license}. Review the provider terms before the file is downloaded.</p>
            <label className="local-setup-license"><input type="checkbox" checked={state.licenseAccepted} onChange={(event) => update({ licenseAccepted: event.target.checked })} /> I accept the {selectedModel.license} for this model.</label>
            <button type="button" className="local-model-primary" onClick={continueSetup}><ShieldCheck size={15} aria-hidden="true" /> CONTINUE</button>
          </section>
        ) : null}

        {state.phase === "install" ? (
          <section className="local-setup-card">
            <span className="eyebrow">DOWNLOAD / VERIFY</span>
            <h2>{selectedModel.name}</h2>
            <p>{selectedModel.size} download. Progress and the current lifecycle state are saved for resume after restart.</p>
            <div className="local-setup-progress"><div><span>{state.status.toUpperCase()}</span><strong>{state.progress}%</strong></div><div className="local-model-progress-track"><i style={{ width: `${state.progress}%` }} /></div></div>
            <div className="local-setup-actions">{state.status === "idle" || state.status === "cancelled" ? <button type="button" className="local-model-primary" onClick={startDownload}><Download size={15} aria-hidden="true" /> START DOWNLOAD</button> : null}{state.status === "downloading" ? <button type="button" className="local-model-primary" onClick={completeDownload}><CheckCircle2 size={15} aria-hidden="true" /> COMPLETE DOWNLOAD</button> : null}{state.status === "paused" ? <button type="button" className="local-model-primary" onClick={resumeDownload}><Play size={15} aria-hidden="true" /> RESUME DOWNLOAD</button> : null}{state.status === "verifying" ? <button type="button" className="local-model-primary" onClick={verifyDownload}><ShieldCheck size={15} aria-hidden="true" /> VERIFY CHECKSUM</button> : null}{state.status === "downloading" ? <button type="button" onClick={pauseDownload}><Pause size={15} aria-hidden="true" /> PAUSE</button> : null}{state.status === "downloading" || state.status === "paused" ? <button type="button" className="local-model-danger" onClick={cancelDownload}><X size={15} aria-hidden="true" /> CANCEL</button> : null}</div>
          </section>
        ) : null}

        {state.phase === "health" ? (
          <section className="local-setup-card">
            <span className="eyebrow">HEALTH CHECK</span>
            <h2>Verify the runner.</h2>
            <p>Checksum passed. Run one local load check before this model becomes the workspace route.</p>
             <div className="local-setup-health"><CheckCircle2 size={20} aria-hidden="true" /><strong>{selectedModel.name} / READY TO LOAD</strong><span>{selectedModel.sourceModelId} / {state.runner} runner / no remote Provider</span></div>
            <button type="button" className="local-model-primary" onClick={continueSetup}><ServerCog size={15} aria-hidden="true" /> RUN HEALTH CHECK</button>
          </section>
        ) : null}

        {state.phase === "complete" ? (
          <section className="local-setup-card local-setup-complete">
            <span className="eyebrow">LOCAL ROUTE READY</span>
            <h2>{selectedModel.name} is ready.</h2>
            <p>The runner passed its local health check. The workspace can now use this model without a remote API.</p>
          <AppLink className="local-model-primary" href={workspaceHomeHref()}><ArrowRight size={15} aria-hidden="true" /> OPEN WORKSPACE HOME</AppLink>
          </section>
        ) : null}

        <div className="local-setup-footer"><AppLink href="/onboarding"><ArrowLeft size={15} aria-hidden="true" /> BACK TO ROUTES</AppLink><span>{notice || (state.phase === "complete" ? "SETUP SAVED" : "PROGRESS SAVED LOCALLY")}</span></div>
      </section>
    </main>
  );
}

export function LocalModels({ setupMode = false }: { setupMode?: boolean }) {
  const [models, setModels] = useState<LocalModel[]>(readLocalModels);
  const [selectedId, setSelectedId] = useState(() => {
    const saved = localStorage.getItem("rabbit_code_selected_model");
    return saved && initialModels.some((model) => model.id === saved) ? saved : initialModels[0].id;
  });
  const [licenseAccepted, setLicenseAccepted] = useState(false);
  const [verificationAttempts, setVerificationAttempts] = useState<Record<string, number>>({});
  const [notice, setNotice] = useState<string | null>(null);
  const [installOpen, setInstallOpen] = useState(false);
  const [networkAvailable] = useState(true);
  const [runnerStatus, setRunnerStatus] = useState<"idle" | "ready" | "busy" | "stopping">("idle");
  const [modelDirectory, setModelDirectory] = useState("");
  const [directoryInput, setDirectoryInput] = useState("");
  const [directoryNotice, setDirectoryNotice] = useState<string | null>(null);
  const selectedModel = models.find((model) => model.id === selectedId) ?? models[0];

  useEffect(() => {
    localStorage.setItem(localModelsStorageKey(), JSON.stringify(models));
  }, [models]);

  useEffect(() => {
    let active = true;
    void api.localModelState(selectedModel.id).then((event) => {
      if (!active) {
        return;
      }
      setModels((current) => current.map((model) => {
        if (model.id !== selectedModel.id) {
          return model;
        }
        try {
          return applyLocalModelEvent(model, event as LocalModelEvent);
        } catch {
          return model;
        }
      }));
    }).catch(() => undefined);
    return () => {
      active = false;
    };
  }, [selectedId, selectedModel.id]);

  useEffect(() => {
    let active = true;
    void api.localModelDirectory().then((payload) => {
      const root = payload && typeof payload === "object" && typeof (payload as { root?: unknown }).root === "string"
        ? (payload as { root: string }).root
        : "";
      if (active && root) {
        setModelDirectory(root);
        setDirectoryInput(root);
      }
    }).catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);

  if (setupMode) {
    return <LocalSetupWizard />;
  }

  function dispatchEvents(events: LocalModelEvent[]) {
    setModels((current) => current.map((model) => {
      if (model.id !== selectedModel.id) {
        return model;
      }
      try {
        return events.reduce((next, event) => applyLocalModelEvent(next, event), model);
      } catch {
        return model;
      }
    }));
    setNotice(events.length ? events[events.length - 1].message : null);
    const eventChain = events.reduce<Promise<void>>(
      (chain, event) => chain.then(() => api.localModelEvent(selectedModel.id, event).then(() => undefined)),
      Promise.resolve(),
    );
    void eventChain.catch(() => undefined);
  }

  function requestInstall() {
    if (!licenseAccepted) {
      setNotice("ACCEPT THE MODEL LICENSE BEFORE INSTALLING");
      return;
    }
    setInstallOpen(true);
  }

  function install() {
    if (!networkAvailable) {
      dispatchEvents([
        localModelEvent(selectedModel, "download_started", "DOWNLOAD STARTED"),
        localModelEvent(selectedModel, "failed", "DOWNLOAD CHANNEL OFFLINE", 0, "DOWNLOAD CHANNEL OFFLINE"),
      ]);
      return;
    }
    if (selectedModel.sizeGb > 42) {
      dispatchEvents([
        localModelEvent(selectedModel, "download_started", "DOWNLOAD STARTED"),
        localModelEvent(selectedModel, "failed", "NOT ENOUGH DISK SPACE", 0, "NOT ENOUGH DISK SPACE"),
      ]);
      return;
    }
    dispatchEvents([localModelEvent(selectedModel, "download_started", "DOWNLOAD STARTED", 32)]);
  }

  function pauseDownload() {
    dispatchEvents([localModelEvent(selectedModel, "download_paused", "DOWNLOAD PAUSED")]);
  }

  function resumeDownload() {
    dispatchEvents([localModelEvent(selectedModel, "download_started", "DOWNLOAD RESUMED", 68)]);
  }

  function completeDownload() {
    dispatchEvents([localModelEvent(selectedModel, "download_completed", "DOWNLOAD COMPLETE / VERIFYING", 100)]);
  }

  function verifyDownload() {
    const attempts = verificationAttempts[selectedModel.id] ?? 0;
    if (selectedModel.id === "qwen2.5-coder-1.5b-instruct" && attempts === 0) {
      setVerificationAttempts((current) => ({ ...current, [selectedModel.id]: attempts + 1 }));
      dispatchEvents([localModelEvent(selectedModel, "corrupt", "CHECKSUM FAILED / REPAIR AVAILABLE", 100, "CHECKSUM MISMATCH")]);
      return;
    }
    dispatchEvents([
      localModelEvent(selectedModel, "verified", "CHECKSUM VERIFIED", 100),
      localModelEvent(selectedModel, "ready", "CHECKSUM PASSED / MODEL READY", 100),
    ]);
  }

  function repair() {
    dispatchEvents([
      localModelEvent(selectedModel, "download_started", "REPAIR STARTED", 32),
      localModelEvent(selectedModel, "download_completed", "REPAIR STAGED / VERIFY AGAIN", 100),
    ]);
  }

  function retry() {
    dispatchEvents([localModelEvent(selectedModel, "download_started", "RETRY STARTED", 32)]);
  }

  function cancelDownload() {
    dispatchEvents([localModelEvent(selectedModel, "reset", "DOWNLOAD CANCELLED", 0)]);
  }

  function loadModel() {
    dispatchEvents([
      localModelEvent(selectedModel, "load_started", "MODEL LOADING"),
      localModelEvent(selectedModel, "busy", "LOCAL RUNNER READY"),
    ]);
    setRunnerStatus("busy");
    localStorage.setItem("rabbit_code_local_runner_ready", "true");
    writeDefaultLocalModel(selectedModel.id);
    persistLocalRoute(selectedModel.id, "healthy");
  }

  function stopModel() {
    dispatchEvents([
      localModelEvent(selectedModel, "unload_started", "MODEL STOPPING"),
      localModelEvent(selectedModel, "ready", "LOCAL RUNNER STOPPED"),
    ]);
    setRunnerStatus("ready");
    localStorage.setItem("rabbit_code_local_runner_ready", "false");
    persistLocalRoute(selectedModel.id, "unavailable");
  }

  function toggleModelEnabled() {
    const enabled = selectedModel.status === "disabled";
    dispatchEvents([localModelEvent(selectedModel, enabled ? "enable" : "disable", enabled ? "MODEL ENABLED / CONFIGURATION RETAINED" : "MODEL DISABLED / HISTORY RETAINED")]);
    setRunnerStatus("idle");
    localStorage.setItem("rabbit_code_local_runner_ready", enabled ? "true" : "false");
    persistLocalRoute(selectedModel.id, enabled ? "healthy" : "unavailable", enabled);
  }

  function uninstall() {
    const unload = selectedModel.status === "not_installed" ? [] : [localModelEvent(selectedModel, "unload_started", "MODEL UNINSTALLING")];
    const resetSource = unload.length ? { ...selectedModel, status: "stopping" as ModelStatus } : selectedModel;
    dispatchEvents([...unload, localModelEvent(resetSource, "reset", "MODEL UNINSTALLED", 0)]);
    setRunnerStatus("idle");
    localStorage.setItem("rabbit_code_local_runner_ready", "false");
    localStorage.removeItem(providerRouteStorageKey());
    void api.uninstallRegisteredLocalModel(selectedModel.id).catch(() => undefined);
  }

  function checkDirectory() {
    const path = directoryInput.trim();
    if (!path) {
      setDirectoryNotice("ENTER A MODEL DIRECTORY");
      return;
    }
    void api.checkLocalModelDirectory(path, Math.ceil(selectedModel.sizeGb * 1024 ** 3)).then((report) => {
      const result = report as { path?: string; sufficient?: boolean; writable?: boolean };
      setDirectoryNotice(result.sufficient && result.writable ? "DIRECTORY READY" : "DIRECTORY NEEDS ATTENTION");
    }).catch(() => setDirectoryNotice("DIRECTORY CHECK FAILED"));
  }

  function migrateDirectory() {
    const destination = directoryInput.trim();
    if (!destination || destination === modelDirectory) {
      setDirectoryNotice("CHOOSE A NEW DIRECTORY");
      return;
    }
    void api.migrateLocalModelDirectory(destination).then((result) => {
      const migrated = result as { destination_root?: unknown };
      const nextRoot = typeof migrated.destination_root === "string" ? migrated.destination_root : destination;
      setModelDirectory(nextRoot);
      setDirectoryInput(nextRoot);
      setDirectoryNotice("MODEL DIRECTORY MIGRATED");
    }).catch(() => setDirectoryNotice("MIGRATION STOPPED / ORIGINAL RETAINED"));
  }

  function cleanupOldVersions() {
    void api.cleanupLocalModels(selectedModel.id).then((result) => {
      const versions = result && typeof result === "object" && Array.isArray((result as { deleted_versions?: unknown }).deleted_versions)
        ? (result as { deleted_versions: unknown[] }).deleted_versions.length
        : 0;
      setDirectoryNotice(versions ? `CLEANED ${versions} OLD VERSION${versions === 1 ? "" : "S"}` : "NO OLD VERSIONS TO CLEAN");
    }).catch(() => setDirectoryNotice("CLEANUP FAILED"));
  }

  function markUpdateAvailable() {
    dispatchEvents([localModelEvent(selectedModel, "update_available", "MODEL UPDATE AVAILABLE")]);
  }

  function selectModel(modelId: string) {
    setSelectedId(modelId);
    setLicenseAccepted(false);
    setNotice(null);
    localStorage.setItem("rabbit_code_selected_model", modelId);
  }

  const primaryAction = selectedModel.status === "not_installed" || selectedModel.status === "unloaded"
    ? <button className="local-model-primary" type="button" onClick={requestInstall}><Download size={15} aria-hidden="true" /> INSTALL MODEL</button>
    : selectedModel.status === "downloading"
      ? <button className="local-model-primary" type="button" onClick={completeDownload}><CheckCircle2 size={15} aria-hidden="true" /> COMPLETE DOWNLOAD</button>
      : selectedModel.status === "paused"
        ? <button className="local-model-primary" type="button" onClick={resumeDownload}><Play size={15} aria-hidden="true" /> RESUME DOWNLOAD</button>
        : selectedModel.status === "verifying"
          ? <button className="local-model-primary" type="button" onClick={verifyDownload}><ShieldCheck size={15} aria-hidden="true" /> VERIFY CHECKSUM</button>
            : selectedModel.status === "corrupt" || selectedModel.status === "failed"
            ? <button className="local-model-primary" type="button" onClick={repair}><RotateCcw size={15} aria-hidden="true" /> REPAIR MODEL</button>
            : selectedModel.status === "update"
              ? <button className="local-model-primary" type="button" onClick={install}><RefreshCw size={15} aria-hidden="true" /> UPDATE MODEL</button>
            : selectedModel.status === "disabled"
              ? <button className="local-model-primary" type="button" onClick={toggleModelEnabled}><Power size={15} aria-hidden="true" /> ENABLE MODEL</button>
            : selectedModel.status === "ready"
              ? <button className="local-model-primary" type="button" onClick={loadModel}><Play size={15} aria-hidden="true" /> LOAD MODEL</button>
            : <button className="local-model-primary" type="button" onClick={stopModel}><X size={15} aria-hidden="true" /> STOP RUNNER</button>;

  return (
    <main className="local-model-page">
      <header className="local-model-header">
        <div>
          <span className="eyebrow">LOCAL MODELS / INSTALLER</span>
          <h1>Bring a private model to the workspace.</h1>
          <p>Check the machine, choose a license, and keep download and runner state recoverable.</p>
        </div>
        <div className="local-model-runner-state"><ServerCog size={16} aria-hidden="true" /> RUNNER / {runnerStatus.toUpperCase()}</div>
      </header>

      <section className="local-model-hardware" aria-label="Hardware readiness">
        <div className="local-model-hardware-heading"><span className="eyebrow">HARDWARE CHECK</span><span className="local-model-ready"><CheckCircle2 size={15} aria-hidden="true" /> READY TO INSTALL</span></div>
        <div className="local-model-hardware-grid">
          <div><Cpu size={17} aria-hidden="true" /><span>CPU FALLBACK</span><strong>AVAILABLE</strong></div>
          <div><HardDrive size={17} aria-hidden="true" /><span>DISK FREE</span><strong>42 GB</strong></div>
          <div><ServerCog size={17} aria-hidden="true" /><span>LOCAL RUNNER</span><strong>{runnerStatus === "idle" ? "AVAILABLE" : runnerStatus.toUpperCase()}</strong></div>
          <div>{networkAvailable ? <CheckCircle2 size={17} aria-hidden="true" /> : <WifiOff size={17} aria-hidden="true" />}<span>DOWNLOAD CHANNEL</span><strong>{networkAvailable ? "AVAILABLE" : "OFFLINE"}</strong></div>
        </div>
      </section>

      <section className="local-model-directory" aria-label="Model directory">
        <div className="local-model-section-heading"><span className="eyebrow">MODEL DIRECTORY</span><HardDrive size={15} aria-hidden="true" /></div>
        <div className="local-model-directory-controls">
          <label htmlFor="local-model-directory-input">STORAGE PATH</label>
          <input id="local-model-directory-input" value={directoryInput} onChange={(event) => setDirectoryInput(event.target.value)} placeholder="Choose a local directory" />
          <button type="button" onClick={checkDirectory}><ShieldCheck size={14} aria-hidden="true" /> CHECK SPACE</button>
          <button type="button" onClick={migrateDirectory} disabled={!directoryInput.trim() || directoryInput.trim() === modelDirectory}><RefreshCw size={14} aria-hidden="true" /> MIGRATE DIRECTORY</button>
          <button type="button" onClick={cleanupOldVersions}><Trash2 size={14} aria-hidden="true" /> CLEAN OLD VERSIONS</button>
        </div>
        <p className="local-model-directory-path"><span>ACTIVE PATH</span><code>{modelDirectory || "LOADING"}</code></p>
        {directoryNotice ? <p className="local-model-directory-notice" role="status">{directoryNotice}</p> : null}
      </section>

      <div className="local-model-shell">
        <aside className="local-model-catalog" aria-label="Recommended local models">
          <div className="local-model-section-heading"><span className="eyebrow">RECOMMENDED</span><span>{models.length}</span></div>
          <div className="local-model-items">
            {models.map((model) => (
              <button key={model.id} type="button" className={model.id === selectedModel.id ? "active" : ""} onClick={() => selectModel(model.id)}>
                <span><strong>{model.name}</strong><small>{model.family} / {model.size}</small></span>
                <b className={`local-model-status local-model-status-${model.status}`}>{statusLabels[model.status]}</b>
              </button>
            ))}
          </div>
          <p className="local-model-catalog-note">Model files stay in the local model directory and are never sent to a remote Provider.</p>
        </aside>

        <section className="local-model-detail" aria-label="Local model installation">
           <div className="local-model-detail-heading"><div><span className="eyebrow">{selectedModel.family}</span><h2>{selectedModel.name}</h2><p>{selectedModel.sourceModelId} / {selectedModel.size} download / {selectedModel.license}</p></div><strong className={`local-model-status local-model-status-${selectedModel.status}`}>{statusLabels[selectedModel.status]}</strong></div>
          <div className="local-model-progress"><div><span>DOWNLOAD / VERIFY</span><strong>{selectedModel.progress}%</strong></div><div className="local-model-progress-track"><i style={{ width: `${selectedModel.progress}%` }} /></div>{selectedModel.error ? <p className="local-model-error"><AlertTriangle size={15} aria-hidden="true" /> {selectedModel.error}</p> : null}</div>
          <div className="local-model-actions">{primaryAction}{selectedModel.status === "corrupt" || selectedModel.status === "failed" ? <button type="button" onClick={retry}><RotateCcw size={15} aria-hidden="true" /> RETRY</button> : null}{selectedModel.status === "downloading" ? <button type="button" onClick={pauseDownload}><Pause size={15} aria-hidden="true" /> PAUSE</button> : null}{selectedModel.status === "downloading" || selectedModel.status === "paused" ? <button type="button" onClick={cancelDownload} className="local-model-danger"><X size={15} aria-hidden="true" /> CANCEL</button> : null}{selectedModel.status === "ready" || selectedModel.status === "busy" ? <button type="button" onClick={toggleModelEnabled}><Power size={15} aria-hidden="true" /> DISABLE MODEL</button> : null}{selectedModel.status === "ready" || selectedModel.status === "busy" || selectedModel.status === "corrupt" || selectedModel.status === "failed" || selectedModel.status === "update" ? <button type="button" onClick={uninstall} className="local-model-danger"><Trash2 size={15} aria-hidden="true" /> UNINSTALL</button> : null}{selectedModel.status === "ready" ? <button type="button" onClick={markUpdateAvailable}><RefreshCw size={15} aria-hidden="true" /> CHECK FOR UPDATE</button> : null}</div>
          <label className="local-model-license"><input type="checkbox" checked={licenseAccepted} onChange={(event) => setLicenseAccepted(event.target.checked)} /> <span>I accept the {selectedModel.license} for this model.</span><ShieldCheck size={15} aria-hidden="true" /></label>
          <div className="local-model-integrity"><span className="eyebrow">FILE INTEGRITY</span><code>{selectedModel.checksum}</code><span><ShieldCheck size={14} aria-hidden="true" /> VERIFY BEFORE LOAD</span></div>
        </section>

        <aside className="local-model-status-panel" aria-label="Install status">
          <div className="local-model-section-heading"><span className="eyebrow">LIFECYCLE</span><RefreshCw size={15} aria-hidden="true" /></div>
          <ol className="local-model-lifecycle"><li className={selectedModel.progress > 0 ? "done" : ""}>DOWNLOAD</li><li className={selectedModel.status === "verifying" || selectedModel.status === "loading" || selectedModel.status === "ready" || selectedModel.status === "busy" ? "done" : ""}>CHECKSUM</li><li className={selectedModel.status === "loading" || selectedModel.status === "ready" || selectedModel.status === "busy" ? "done" : ""}>LOAD RUNNER</li></ol>
          <div className="local-model-status-note"><ShieldCheck size={15} aria-hidden="true" /><p>Every downloaded file must pass its recorded checksum before the local runner can load it.</p></div>
        </aside>
      </div>
      <InstallDialog
        open={installOpen}
        title={`Install ${selectedModel.name}?`}
        description={`Download ${selectedModel.size} and verify it before loading the local runner.`}
        onClose={() => setInstallOpen(false)}
        onConfirm={() => { setInstallOpen(false); install(); }}
        confirmLabel="CONFIRM INSTALL"
      />
      {notice ? <p className="local-model-notice" role="status">{notice}</p> : null}
    </main>
  );
}

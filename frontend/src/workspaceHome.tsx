import { ArrowUpRight, Cpu, FolderOpen, Plus, Trash2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type ChangeEvent } from "react";

import { api } from "./api";
import { EmptyState, ErrorState } from "./components/UiStates";
import type { ProjectSpace } from "./types";
import { writeDefaultLocalModel } from "./localModelSelection";
import { readWorkspaceRoute, readWorkspaceRoutes, writeWorkspaceRoute } from "./workspaceRoute";

// RC IDs: RC-110, RC-183. Render local-first workspace state and recovery actions.

type RecentProject = Pick<ProjectSpace, "id" | "name" | "created_at"> & { owner_id: number };
type RecentTask = {
  id: string;
  title: string;
  status: "queued" | "running" | "succeeded" | "failed";
  updated_at: string;
};

type WorkspaceModelOption = {
  key: string;
  label: string;
  provider: string;
  model: string;
  source: "cloud" | "local" | "offline";
  health: string;
  enabled: boolean;
};

const PROJECT_STORAGE_KEY = "rabbit_code_recent_projects";
const TASK_STORAGE_KEY = "rabbit_code_recent_tasks";
const HIDDEN_PROJECT_STORAGE_KEY = "rabbit_code_hidden_projects";

function readModelOptions(): WorkspaceModelOption[] {
  const route = readWorkspaceRoute();
  const savedRoutes = readWorkspaceRoutes();
  const options: WorkspaceModelOption[] = [{
    key: "offline:offline",
    label: "Offline Rules / offline",
    provider: "offline",
    model: "offline",
    source: "offline",
    health: "healthy",
    enabled: true,
  }];
  for (const savedRoute of [...savedRoutes, route]) {
    if (!savedRoute.provider || !savedRoute.model || savedRoute.provider === "offline") {
      continue;
    }
    if (savedRoute.provider === "local") {
      if (localStorage.getItem("rabbit_code_local_runner_ready") !== "true") {
        continue;
      }
      options.push({ key: `local:${savedRoute.model}`, label: `Local / ${savedRoute.model}${savedRoute.enabled === false ? " / DISABLED" : ""}`, provider: "local", model: savedRoute.model, source: "local", health: savedRoute.enabled === false ? "unavailable" : "healthy", enabled: savedRoute.enabled !== false });
      continue;
    }
    options.push({ key: `cloud:${savedRoute.provider}:${savedRoute.model}`, label: `Cloud / ${savedRoute.provider} / ${savedRoute.model}${savedRoute.enabled === false ? " / DISABLED" : ""}`, provider: savedRoute.provider, model: savedRoute.model, source: "cloud", health: savedRoute.enabled === false ? "unavailable" : savedRoute.health || "unknown", enabled: savedRoute.enabled !== false });
  }
  const localModel = localStorage.getItem("rabbit_code_selected_model");
  if (localModel && localModel !== "offline" && localStorage.getItem("rabbit_code_local_runner_ready") === "true") {
    options.push({ key: `local:${localModel}`, label: `Local / ${localModel}`, provider: "local", model: localModel, source: "local", health: "healthy", enabled: true });
  }
  return options.filter((option, index, all) => all.findIndex((candidate) => candidate.key === option.key) === index);
}

function selectedModelOption(options: WorkspaceModelOption[]) {
  const route = readWorkspaceRoute();
  return options.find((option) => option.provider === route.provider && option.model === route.model) || options[0];
}

export function WorkspaceHome() {
  const [projects, setProjects] = useState<RecentProject[]>([]);
  const [tasks, setTasks] = useState<RecentTask[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [modelOptions] = useState(readModelOptions);
  const [selectedModelKey, setSelectedModelKey] = useState(() => selectedModelOption(modelOptions).key);
  const inputRef = useRef<HTMLInputElement>(null);

  const loadHome = useCallback(async () => {
    setLoading(true);
    setError(null);
    setTasks(readRecentTasks());
    if (!api.getToken()) {
      setProjects(readRecentProjects());
      setLoading(false);
      return;
    }
    try {
      const remoteProjects = await api.projects();
      const hiddenProjects = new Set(readJson<number[]>(HIDDEN_PROJECT_STORAGE_KEY, []));
      setProjects(remoteProjects.filter((project) => !hiddenProjects.has(project.id)));
    } catch {
      setError("PROJECT SERVICE UNAVAILABLE");
      setProjects(readRecentProjects());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadHome();
  }, [loadHome]);

  function openProjectPicker() {
    inputRef.current?.click();
  }

  function addProject(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const directoryName = file.webkitRelativePath?.split("/")[0] || file.name;
    const project: RecentProject = {
      id: Date.now(),
      owner_id: 0,
      name: directoryName,
      created_at: new Date().toISOString(),
    };
    const next = [project, ...projects.filter((item) => item.name !== project.name)];
    setProjects(next);
    saveRecentProjects(next);
    event.target.value = "";
  }

  function removeProject(project: RecentProject) {
    const next = projects.filter((item) => item.id !== project.id);
    setProjects(next);
    saveRecentProjects(next);
    const hiddenProjects = readJson<number[]>(HIDDEN_PROJECT_STORAGE_KEY, []);
    if (!hiddenProjects.includes(project.id)) {
      localStorage.setItem(
        HIDDEN_PROJECT_STORAGE_KEY,
        JSON.stringify([...hiddenProjects, project.id]),
      );
    }
  }

  const selectedModel = modelOptions.find((option) => option.key === selectedModelKey) || modelOptions[0];
  const modelStatus = !selectedModel.enabled || selectedModel.health === "unavailable"
    ? "UNAVAILABLE"
    : selectedModel.source === "local"
    ? localStorage.getItem("rabbit_code_local_runner_ready") === "true" ? "READY" : "AVAILABLE"
    : selectedModel.health === "healthy" ? "READY" : "AVAILABLE";

  function selectModel(key: string) {
    const option = modelOptions.find((item) => item.key === key);
    if (!option) {
      return;
    }
    const currentRoute = readWorkspaceRoute();
    writeWorkspaceRoute({ ...currentRoute, provider: option.provider, model: option.model, health: option.health, enabled: option.enabled });
    if (option.source === "local") {
      localStorage.setItem("rabbit_code_selected_model", option.model);
      writeDefaultLocalModel(option.model);
    }
    setSelectedModelKey(option.key);
  }

  return (
    <main className="workspace-home-page">
      <section className="workspace-home-hero" aria-labelledby="workspace-home-title">
        <div className="workspace-home-topline">
          <span className="eyebrow">WORKSPACE HOME / LOCAL SESSION</span>
          <label className="workspace-home-model"><Cpu size={15} aria-hidden="true" /> MODEL <select aria-label="Workspace model" value={selectedModel.key} onChange={(event) => selectModel(event.target.value)}>{modelOptions.map((option) => <option key={option.key} value={option.key}>{option.label}</option>)}</select></label>
        </div>
        <div className="workspace-home-heading">
          <div>
            <h1 id="workspace-home-title">Pick up where you left off.</h1>
            <p>Open a project, review recent work, or start a clean task in the shared workspace.</p>
          </div>
          <div className="workspace-home-actions">
            <button type="button" className="action-button action-button-primary" onClick={openProjectPicker}>
              <FolderOpen size={16} aria-hidden="true" /> OPEN PROJECT
            </button>
            <a className="action-button" href="/workspace?new=1">
              <Plus size={16} aria-hidden="true" /> NEW TASK
            </a>
            <input
              ref={inputRef}
              className="sr-only"
              type="file"
              aria-label="Choose project directory"
              onChange={addProject}
            />
          </div>
        </div>
      </section>

      <section className="workspace-home-status" aria-label="Current model status">
        <div><span>MODEL</span><strong>{selectedModel.model}</strong></div>
        <div><span>STATUS</span><strong className="home-status-ready">{modelStatus}</strong></div>
        <div><span>ROUTE</span><strong>{selectedModel.source === "local" ? "LOCAL" : api.getToken() ? "ACCOUNT" : "GUEST"}</strong></div>
        <a href="/onboarding">CONFIGURE <ArrowUpRight size={14} aria-hidden="true" /></a>
      </section>

      {error ? (
        <ErrorState
          title={error}
          description="Recent projects could not be loaded. Local recents remain available."
          primaryAction={{ label: "RETRY", onClick: () => void loadHome() }}
        />
      ) : null}

      <div className="workspace-home-columns">
        <section className="workspace-home-section" aria-labelledby="projects-title">
          <div className="workspace-home-section-heading">
            <div><span className="eyebrow">RECENT PROJECTS</span><h2 id="projects-title">Your workspaces.</h2></div>
            <span className="workspace-home-count">{projects.length}</span>
          </div>
          {loading ? <EmptyState title="LOADING PROJECTS" description="Checking the local project history." compact /> : projects.length === 0 ? (
            <EmptyState title="NO RECENT PROJECTS" description="Open a directory to make it available here." compact />
          ) : (
            <div className="workspace-home-list">
              {projects.map((project) => (
                <div className="workspace-home-item" key={project.id}>
                  <a href={`/workspace?project=${project.id}`}>
                    <strong>{project.name}</strong>
                    <small>Opened {formatDate(project.created_at)}</small>
                  </a>
                  <button
                    type="button"
                    aria-label={`Remove ${project.name}`}
                    title="Remove from recents"
                    onClick={() => removeProject(project)}
                  >
                    <Trash2 size={16} aria-hidden="true" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="workspace-home-section" aria-labelledby="tasks-title">
          <div className="workspace-home-section-heading">
            <div><span className="eyebrow">RECENT TASKS</span><h2 id="tasks-title">The latest runs.</h2></div>
            <span className="workspace-home-count">{tasks.length}</span>
          </div>
          {tasks.length === 0 ? (
            <EmptyState title="NO RECENT TASKS" description="New tasks will appear here after you start working." compact />
          ) : (
            <div className="workspace-home-list">
              {tasks.map((task) => (
                <a className="workspace-home-item workspace-home-task" href={`/workspace?task=${task.id}`} key={task.id}>
                  <span><strong>{task.title}</strong><small>{formatDate(task.updated_at)}</small></span>
                  <b className={`task-status-${task.status}`}>{task.status}</b>
                </a>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

function readRecentProjects(): RecentProject[] {
  return readJson<RecentProject[]>(PROJECT_STORAGE_KEY, []);
}

function readRecentTasks(): RecentTask[] {
  return readJson<RecentTask[]>(TASK_STORAGE_KEY, []);
}

function readJson<T>(key: string, fallback: T): T {
  try {
    const value = JSON.parse(localStorage.getItem(key) || "null") as T | null;
    return value ?? fallback;
  } catch {
    return fallback;
  }
}

function saveRecentProjects(projects: RecentProject[]) {
  localStorage.setItem(PROJECT_STORAGE_KEY, JSON.stringify(projects));
}

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "unknown date" : date.toLocaleDateString("en-US");
}

import { workspaceScope } from "./workspaceRoute";

// RC ID: RC-195. Keep local model identity, context limits, and scoped selection durable.

export const LOCAL_MODEL_OPTIONS = [
  {
    id: "gemma-3-1b-it",
    label: "Gemma 3 1B IT",
    sourceModelId: "google/gemma-3-1b-it",
    contextLength: 8192,
  },
  {
    id: "qwen2.5-coder-1.5b-instruct",
    label: "Qwen2.5-Coder 1.5B",
    sourceModelId: "Qwen/Qwen2.5-Coder-1.5B-Instruct",
    contextLength: 32768,
  },
] as const;

export type LocalModelId = typeof LOCAL_MODEL_OPTIONS[number]["id"];

const localModelIds = new Set<string>(LOCAL_MODEL_OPTIONS.map((model) => model.id));

export function localModelOption(modelId: string | null | undefined) {
  return LOCAL_MODEL_OPTIONS.find((model) => model.id === modelId);
}

export function localModelStatus(modelId: string, search = window.location.search): string {
  try {
    const saved = JSON.parse(localStorage.getItem(`rabbit_code_local_models_${workspaceScope(search)}`) || "null") as Array<{ id?: unknown; status?: unknown }> | null;
    const model = saved?.find((item) => item?.id === modelId);
    return typeof model?.status === "string" ? model.status : "not_installed";
  } catch {
    return "not_installed";
  }
}

export function localModelReady(modelId: string, search = window.location.search): boolean {
  return ["ready", "busy"].includes(localModelStatus(modelId, search));
}

export function readDefaultLocalModel(): LocalModelId {
  const saved = localStorage.getItem("rabbit_code_default_local_model");
  if (saved && localModelIds.has(saved)) {
    return saved as LocalModelId;
  }
  const selected = localStorage.getItem("rabbit_code_selected_model");
  if (selected && localModelIds.has(selected)) {
    return selected as LocalModelId;
  }
  return LOCAL_MODEL_OPTIONS[0].id;
}

export function writeDefaultLocalModel(modelId: string) {
  if (localModelIds.has(modelId)) {
    localStorage.setItem("rabbit_code_default_local_model", modelId);
  }
}

function sessionModelStorageKey(search = window.location.search) {
  const params = new URLSearchParams(search);
  const session = (params.get("session") || params.get("task") || "current").replace(/[^a-zA-Z0-9_-]/g, "-");
  return `rabbit_code_session_local_model_${workspaceScope(search)}_${session}`;
}

export function readSessionLocalModel(search = window.location.search): LocalModelId | null {
  const saved = localStorage.getItem(sessionModelStorageKey(search));
  return saved && localModelIds.has(saved) ? saved as LocalModelId : null;
}

export function writeSessionLocalModel(modelId: string | null, search = window.location.search) {
  const key = sessionModelStorageKey(search);
  if (modelId === null) {
    localStorage.removeItem(key);
  } else if (localModelIds.has(modelId)) {
    localStorage.setItem(key, modelId);
  }
}

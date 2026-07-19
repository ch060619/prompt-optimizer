// AUTO-GENERATED FILE. DO NOT EDIT.
// RC IDs: RC-062, RC-154, RC-181, RC-184.
// Source: docs/api/openapi-v1.json
// Generator: scripts/generate_api.py

import type * as Schema from "./schema";

export interface ApiClientOptions {
  baseUrl?: string;
  fetch?: typeof fetch;
  getToken?: () => string | null;
}

export class ApiRequestError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly category?: string;
  readonly recoveryAction?: string;
  readonly exitCode?: number;
  readonly providerRequestId?: string;

  constructor(status: number, payload: unknown, fallback: string) {
    const envelope = payload && typeof payload === "object" ? payload as Record<string, unknown> : {};
    const detail = envelope.detail && typeof envelope.detail === "object" ? envelope.detail as Record<string, unknown> : envelope;
    const message = typeof envelope.detail === "string" ? envelope.detail : detail.message;
    super(typeof message === "string" ? message : fallback);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = typeof detail.code === "string" ? detail.code : undefined;
    this.category = typeof detail.category === "string" ? detail.category : undefined;
    this.recoveryAction = typeof detail.recovery_action === "string" ? detail.recovery_action : undefined;
    this.exitCode = typeof detail.exit_code === "number" ? detail.exit_code : undefined;
    this.providerRequestId = typeof detail.provider_request_id === "string" ? detail.provider_request_id : undefined;
  }
}

export function createApiClient(options: ApiClientOptions = {}) {
  const baseUrl = options.baseUrl?.replace(/\/$/, "") ?? "";
  const fetcher = options.fetch ?? ((input: RequestInfo | URL, init?: RequestInit) => globalThis.fetch(input, init));

  async function request<T>(
    path: string,
    init: RequestInit,
    returnResponse = false,
  ): Promise<T> {
    const token = options.getToken?.();
    const headers: HeadersInit = {
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    };
    const response = await fetcher(`${baseUrl}${path}`, { ...init, headers });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({ detail: response.statusText }));
      const detail = payload && typeof payload === "object" && "detail" in payload
        ? (payload as { detail?: unknown }).detail
        : response.statusText;
      throw new ApiRequestError(response.status, payload, typeof detail === "string" ? detail : response.statusText);
    }
    if (returnResponse) {
      return response as T;
    }
    return (await response.json()) as T;
  }

  function withQuery(path: string, populate: (query: URLSearchParams) => void) {
    const query = new URLSearchParams();
    populate(query);
    const encoded = query.toString();
    return encoded ? `${path}?${encoded}` : path;
  }

  return {
    config() {
      return request<Record<string, unknown>>(`/api/v1/config`, {
        method: "GET",
      });
    },
    localModelState(modelId: string) {
      return request<Record<string, unknown>>(`/api/v1/local-models/${encodeURIComponent(String(modelId))}/state`, {
        method: "GET",
      });
    },
    localModelEvent(modelId: string, body: Schema.LocalModelEventRequest) {
      return request<Record<string, unknown>>(`/api/v1/local-models/${encodeURIComponent(String(modelId))}/events`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    localModelDirectory() {
      return request<Record<string, unknown>>(`/api/v1/local-models/directory`, {
        method: "GET",
      });
    },
    checkLocalModelDirectory(body: Schema.ModelDirectoryCheckRequest) {
      return request<Record<string, unknown>>(`/api/v1/local-models/directory/check`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    migrateLocalModelDirectory(body: Schema.ModelDirectoryMigrateRequest) {
      return request<Record<string, unknown>>(`/api/v1/local-models/directory/migrate`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    installLocalModelVersion(modelId: string, body: Schema.ModelVersionInstallRequest) {
      return request<Record<string, unknown>>(`/api/v1/local-models/${encodeURIComponent(String(modelId))}/versions`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    rollbackLocalModel(modelId: string, body: Schema.ModelRollbackRequest) {
      return request<Record<string, unknown>>(`/api/v1/local-models/${encodeURIComponent(String(modelId))}/rollback`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    repairLocalModel(modelId: string, body: Schema.ModelRepairRequest) {
      return request<Record<string, unknown>>(`/api/v1/local-models/${encodeURIComponent(String(modelId))}/repair`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    cleanupLocalModels(body: Schema.ModelCleanupRequest) {
      return request<Record<string, unknown>>(`/api/v1/local-models/cleanup`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    uninstallRegisteredLocalModel(modelId: string) {
      return request<Record<string, unknown>>(`/api/v1/local-models/${encodeURIComponent(String(modelId))}/registered`, {
        method: "DELETE",
      });
    },
    localRunnerModels(runner: string) {
      return request<Record<string, unknown>>(`/api/v1/local-runners/${encodeURIComponent(String(runner))}/models`, {
        method: "GET",
      });
    },
    localRunnerCapabilities(runner: string) {
      return request<Record<string, unknown>>(`/api/v1/local-runners/${encodeURIComponent(String(runner))}/capabilities`, {
        method: "GET",
      });
    },
    localRunnerHealth(runner: string) {
      return request<Record<string, unknown>>(`/api/v1/local-runners/${encodeURIComponent(String(runner))}/health`, {
        method: "GET",
      });
    },
    loadLocalRunnerModel(runner: string, modelId: string) {
      return request<Record<string, unknown>>(`/api/v1/local-runners/${encodeURIComponent(String(runner))}/models/${encodeURIComponent(String(modelId))}/load`, {
        method: "POST",
      });
    },
    unloadLocalRunnerModel(runner: string, modelId: string) {
      return request<Record<string, unknown>>(`/api/v1/local-runners/${encodeURIComponent(String(runner))}/models/${encodeURIComponent(String(modelId))}/unload`, {
        method: "POST",
      });
    },
    generateLocalRunner(runner: string, body: Schema.RunnerGenerateRequest) {
      return request<Record<string, unknown>>(`/api/v1/local-runners/${encodeURIComponent(String(runner))}/generate`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    streamLocalRunner(runner: string, body: Schema.RunnerGenerateRequest) {
      return request<unknown>(`/api/v1/local-runners/${encodeURIComponent(String(runner))}/stream`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    cancelLocalRunner(runner: string, requestId: string) {
      return request<Record<string, unknown>>(`/api/v1/local-runners/${encodeURIComponent(String(runner))}/requests/${encodeURIComponent(String(requestId))}/cancel`, {
        method: "POST",
      });
    },
    cleanupPreview() {
      return request<Record<string, unknown>>(`/api/v1/data/cleanup/preview`, {
        method: "GET",
      });
    },
    cleanup(body: Schema.CleanupRequest) {
      return request<Record<string, unknown>>(`/api/v1/data/cleanup`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    analyze(body: Schema.AnalyzeRequest) {
      return request<Schema.PromptAnalysis>(`/api/v1/analyze`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    register(body: Schema.AuthRequest) {
      return request<Schema.AuthResponse>(`/api/v1/auth/register`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    login(body: Schema.AuthRequest) {
      return request<Schema.AuthResponse>(`/api/v1/auth/login`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    me() {
      return request<Schema.UserPublic>(`/api/v1/auth/me`, {
        method: "GET",
      });
    },
    projects() {
      return request<Array<Schema.ProjectSpace>>(`/api/v1/projects`, {
        method: "GET",
      });
    },
    optimize(body: Schema.OptimizeRequest, signal?: AbortSignal) {
      return request<Schema.OptimizeResponse>(`/api/v1/optimize`, {
        method: "POST",
        body: JSON.stringify(body),
        ...(signal ? { signal } : {}),
      });
    },
    optimizeStream(body: Schema.OptimizeRequest, signal?: AbortSignal, requestId?: string, afterSeq?: number) {
      return request<Response>(`/api/v1/optimize/stream`, {
        method: "POST",
        body: JSON.stringify(body),
        ...(signal ? { signal } : {}),
        ...(requestId || afterSeq !== undefined ? {
          headers: {
            ...(requestId ? { "X-Request-ID": requestId } : {}),
            ...(afterSeq !== undefined ? { "Last-Event-ID": String(afterSeq) } : {}),
          },
        } : {}),
      }, true);
    },
    cancelOptimizeStream(requestId: string) {
      return request<Record<string, unknown>>(`/api/v1/optimize/stream/${encodeURIComponent(String(requestId))}/cancel`, {
        method: "POST",
      });
    },
    createOptimizeTask(body: Schema.OptimizeRequest) {
      return request<Schema.TaskCreateResponse>(`/api/v1/tasks/optimize`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    createExportTask(body: Schema.ExportRequest) {
      return request<Schema.TaskCreateResponse>(`/api/v1/tasks/export`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    createEvaluateTask(body: Schema.EvaluateTaskRequest) {
      return request<Schema.TaskCreateResponse>(`/api/v1/tasks/evaluate`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    getTask(taskId: string) {
      return request<Schema.TaskRecord>(`/api/v1/tasks/${encodeURIComponent(String(taskId))}`, {
        method: "GET",
      });
    },
    getTaskResult(taskId: string) {
      return request<Record<string, unknown>>(`/api/v1/tasks/${encodeURIComponent(String(taskId))}/result`, {
        method: "GET",
      });
    },
    templates(category?: string | null) {
      return request<Array<Schema.PromptTemplate>>(withQuery(`/api/v1/templates`, (query) => {
      if (category !== undefined && category !== null) { query.set("category", String(category)); }
    }), {
        method: "GET",
      });
    },
    template(templateId: string) {
      return request<Schema.PromptTemplate>(`/api/v1/templates/${encodeURIComponent(String(templateId))}`, {
        method: "GET",
      });
    },
    history() {
      return request<Array<Schema.VersionSummary>>(`/api/v1/history`, {
        method: "GET",
      });
    },
    version(versionId: number) {
      return request<Schema.PromptVersion>(`/api/v1/history/${encodeURIComponent(String(versionId))}`, {
        method: "GET",
      });
    },
    deleteVersion(versionId: number) {
      return request<Response>(`/api/v1/history/${encodeURIComponent(String(versionId))}`, {
        method: "DELETE",
      }, true);
    },
    acceptVersion(versionId: number) {
      return request<Schema.PromptVersion>(`/api/v1/history/${encodeURIComponent(String(versionId))}/accept`, {
        method: "POST",
      });
    },
    diff(versionId: number, otherId: number) {
      return request<Schema.DiffResult>(`/api/v1/history/${encodeURIComponent(String(versionId))}/diff/${encodeURIComponent(String(otherId))}`, {
        method: "GET",
      });
    },
    export(body: Schema.ExportRequest) {
      return request<Response>(`/api/v1/export`, {
        method: "POST",
        body: JSON.stringify(body),
      }, true);
    },
  };
}

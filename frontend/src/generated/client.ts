// AUTO-GENERATED FILE. DO NOT EDIT.
// RC ID: RC-062.
// Source: docs/api/openapi-v1.json
// Generator: scripts/generate_api.py

import type * as Schema from "./schema";

export interface ApiClientOptions {
  baseUrl?: string;
  fetch?: typeof fetch;
  getToken?: () => string | null;
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
      throw new Error(typeof detail === "string" ? detail : response.statusText);
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
    optimize(body: Schema.OptimizeRequest) {
      return request<Schema.OptimizeResponse>(`/api/v1/optimize`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    optimizeStream(body: Schema.OptimizeRequest) {
      return request<Response>(`/api/v1/optimize/stream`, {
        method: "POST",
        body: JSON.stringify(body),
      }, true);
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

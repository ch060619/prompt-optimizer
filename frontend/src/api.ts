import type {
  DiffResult,
  OptimizeResponse,
  PromptAnalysis,
  PromptTemplate,
  VersionSummary
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(payload.detail ?? response.statusText);
  }
  return (await response.json()) as T;
}

export const api = {
  analyze(prompt: string) {
    return request<PromptAnalysis>("/api/analyze", {
      method: "POST",
      body: JSON.stringify({ prompt })
    });
  },
  optimize(prompt: string, templateId?: string) {
    return request<OptimizeResponse>("/api/optimize", {
      method: "POST",
      body: JSON.stringify({ prompt, template_id: templateId })
    });
  },
  templates(category?: string) {
    const query = category ? `?category=${encodeURIComponent(category)}` : "";
    return request<PromptTemplate[]>(`/api/templates${query}`);
  },
  history() {
    return request<VersionSummary[]>("/api/history");
  },
  diff(oldId: number, newId: number) {
    return request<DiffResult>(`/api/history/${oldId}/diff/${newId}`);
  },
  async export(versionId: number, format: string) {
    const response = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ version_id: versionId, format })
    });
    if (!response.ok) {
      throw new Error("导出失败");
    }
    return response.text();
  }
};


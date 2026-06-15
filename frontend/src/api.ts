import type {
  DiffResult,
  OptimizeResponse,
  PromptAnalysis,
  PromptTemplate,
  StreamEvent,
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
  optimize(prompt: string, templateId?: string, provider = "offline") {
    return request<OptimizeResponse>("/api/optimize", {
      method: "POST",
      body: JSON.stringify({ prompt, template_id: templateId, provider })
    });
  },
  async streamOptimize(
    prompt: string,
    templateId: string | undefined,
    provider: string,
    onEvent: (event: StreamEvent) => void
  ) {
    const response = await fetch("/api/optimize/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, template_id: templateId, provider })
    });
    if (!response.ok || !response.body) {
      const payload = await response.json().catch(() => ({ detail: "流式优化失败" }));
      throw new Error(payload.detail ?? "流式优化失败");
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let reading = true;
    while (reading) {
      const { done, value } = await reader.read();
      if (done) {
        reading = false;
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";
      for (const raw of events) {
        const parsed = parseStreamEvent(raw);
        if (parsed) {
          onEvent(parsed);
        }
      }
    }
    if (buffer.trim()) {
      const parsed = parseStreamEvent(buffer);
      if (parsed) {
        onEvent(parsed);
      }
    }
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
      const payload = await response.json().catch(() => ({ detail: "导出失败" }));
      throw new Error(payload.detail ?? "导出失败");
    }
    return response.text();
  }
};

function parseStreamEvent(raw: string): StreamEvent | null {
  const eventLine = raw.split("\n").find((line) => line.startsWith("event: "));
  const dataLine = raw.split("\n").find((line) => line.startsWith("data: "));
  if (!eventLine || !dataLine) {
    return null;
  }
  return {
    event: eventLine.slice("event: ".length) as StreamEvent["event"],
    data: JSON.parse(dataLine.slice("data: ".length)) as unknown
  };
}

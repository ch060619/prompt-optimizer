import type {
  AuthResponse,
  DiffResult,
  OptimizeResponse,
  PromptAnalysis,
  PromptTemplate,
  StreamEvent,
  TaskCreateResponse,
  TaskRecord,
  VersionSummary
} from "./types";

// RC ID: RC-058. New GUI calls use the single versioned App Server prefix.
const API_PREFIX = "/api/v1";

let accessToken: string | null = localStorage.getItem("prompt_optimizer_token");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: authHeaders(init?.headers),
    ...init
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(payload.detail ?? response.statusText);
  }
  return (await response.json()) as T;
}

export const api = {
  setToken(token: string | null) {
    accessToken = token;
    if (token) {
      localStorage.setItem("prompt_optimizer_token", token);
    } else {
      localStorage.removeItem("prompt_optimizer_token");
    }
  },
  getToken() {
    return accessToken;
  },
  register(username: string, password: string) {
    return request<AuthResponse>(`${API_PREFIX}/auth/register`, {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
  },
  login(username: string, password: string) {
    return request<AuthResponse>(`${API_PREFIX}/auth/login`, {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
  },
  me() {
    return request<AuthResponse["user"]>(`${API_PREFIX}/auth/me`);
  },
  analyze(prompt: string) {
    return request<PromptAnalysis>(`${API_PREFIX}/analyze`, {
      method: "POST",
      body: JSON.stringify({ prompt })
    });
  },
  optimize(prompt: string, templateId?: string, provider = "offline") {
    return request<OptimizeResponse>(`${API_PREFIX}/optimize`, {
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
    const response = await fetch(`${API_PREFIX}/optimize/stream`, {
      method: "POST",
      headers: authHeaders(),
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
  createOptimizeTask(prompt: string, templateId?: string, provider = "offline") {
    return request<TaskCreateResponse>(`${API_PREFIX}/tasks/optimize`, {
      method: "POST",
      body: JSON.stringify({ prompt, template_id: templateId, provider })
    });
  },
  task(taskId: string) {
    return request<TaskRecord>(`${API_PREFIX}/tasks/${taskId}`);
  },
  taskResult(taskId: string) {
    return request<OptimizeResponse>(`${API_PREFIX}/tasks/${taskId}/result`);
  },
  templates(category?: string) {
    const query = category ? `?category=${encodeURIComponent(category)}` : "";
    return request<PromptTemplate[]>(`${API_PREFIX}/templates${query}`);
  },
  history() {
    return request<VersionSummary[]>(`${API_PREFIX}/history`);
  },
  diff(oldId: number, newId: number) {
    return request<DiffResult>(`${API_PREFIX}/history/${oldId}/diff/${newId}`);
  },
  async export(versionId: number, format: string) {
    const response = await fetch(`${API_PREFIX}/export`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ version_id: versionId, format })
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({ detail: "导出失败" }));
      throw new Error(payload.detail ?? "导出失败");
    }
    return response.text();
  }
};

function authHeaders(headers?: HeadersInit): HeadersInit {
  return {
    "Content-Type": "application/json",
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    ...(headers ?? {})
  };
}

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

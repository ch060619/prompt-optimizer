import { createApiClient } from "./generated/client";
import type {
  ExportRequest,
  OptimizationTargets,
  OptimizeRequest,
  OptimizeResponse
} from "./types";
import { sanitizePublicError, sanitizePublicText } from "./publicOutput";

// RC IDs: RC-058, RC-062, RC-154, RC-180, RC-181. New GUI calls use the generated versioned App Server client.
let accessToken: string | null = localStorage.getItem("prompt_optimizer_token");
const generatedClient = createApiClient({ getToken: () => accessToken });

export type Provider = NonNullable<OptimizeRequest["provider"]>;

export function providerErrorMessage(value: unknown): string {
  if (!value || typeof value !== "object") {
    return "操作失败";
  }
  const candidate = value as {
    message?: unknown;
    detail?: unknown;
    code?: unknown;
    recoveryAction?: unknown;
    recovery_action?: unknown;
    providerRequestId?: unknown;
    provider_request_id?: unknown;
  };
  const message = typeof candidate.message === "string"
    ? candidate.message
    : typeof candidate.detail === "string"
      ? candidate.detail
      : "操作失败";
  const code = typeof candidate.code === "string" ? ` [${sanitizePublicText(candidate.code)}]` : "";
  const recovery = candidate.recoveryAction ?? candidate.recovery_action;
  const action = typeof recovery === "string" ? `；修复动作：${sanitizePublicText(recovery)}` : "";
  const requestId = candidate.providerRequestId ?? candidate.provider_request_id;
  const request = typeof requestId === "string" ? `；Provider 请求 ID：${sanitizePublicText(requestId)}` : "";
  return `${sanitizePublicError(message)}${code}${action}${request}`;
}

type StreamEventName =
  | "started"
  | "analysis"
  | "delta"
  | "chunk"
  | "fallback"
  | "saved"
  | "completed"
  | "cancelled"
  | "error";
type StreamEvent = { event: StreamEventName; data: unknown; seq?: number };

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
    return generatedClient.register({ username, password });
  },
  login(username: string, password: string) {
    return generatedClient.login({ username, password });
  },
  me() {
    return generatedClient.me();
  },
  config() {
    return generatedClient.config();
  },
  cleanupPreview() {
    return generatedClient.cleanupPreview();
  },
  cleanup(confirm = false) {
    return generatedClient.cleanup({ confirm });
  },
  analyze(prompt: string) {
    return generatedClient.analyze({ prompt });
  },
  optimize(prompt: string, templateId?: string, provider: Provider = "offline", signal?: AbortSignal, savePromptHistory = true, model?: string, optimizerProvider?: Provider, optimizerModel?: string, targets?: OptimizationTargets) {
    return generatedClient.optimize({ prompt, template_id: templateId, provider, model, optimizer_provider: optimizerProvider, optimizer_model: optimizerModel, save_prompt_history: savePromptHistory, targets }, signal);
  },
  async streamOptimize(
    prompt: string,
    templateId: string | undefined,
    provider: Provider,
    onEvent: (event: StreamEvent) => void,
    savePromptHistory = true,
    model?: string,
    optimizerProvider?: Provider,
    optimizerModel?: string,
    targets?: OptimizationTargets,
    requestId?: string,
    afterSeq?: number,
  ) {
    const response = await generatedClient.optimizeStream({
      prompt,
      template_id: templateId,
      provider,
      model,
      optimizer_provider: optimizerProvider,
      optimizer_model: optimizerModel,
      save_prompt_history: savePromptHistory,
      targets,
    }, undefined, requestId, afterSeq);
    if (!response.body) {
      throw new Error("流式优化失败");
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
  cancelStream(requestId: string) {
    return generatedClient.cancelOptimizeStream(requestId);
  },
  createOptimizeTask(prompt: string, templateId?: string, provider: Provider = "offline", savePromptHistory = true, model?: string, optimizerProvider?: Provider, optimizerModel?: string, targets?: OptimizationTargets) {
    return generatedClient.createOptimizeTask({ prompt, template_id: templateId, provider, model, optimizer_provider: optimizerProvider, optimizer_model: optimizerModel, save_prompt_history: savePromptHistory, targets });
  },
  task(taskId: string) {
    return generatedClient.getTask(taskId);
  },
  async taskResult(taskId: string) {
    return (await generatedClient.getTaskResult(taskId)) as unknown as OptimizeResponse;
  },
  templates(category?: string) {
    return generatedClient.templates(category);
  },
  history() {
    return generatedClient.history();
  },
  acceptVersion(versionId: number) {
    return generatedClient.acceptVersion(versionId);
  },
  deleteVersion(versionId: number) {
    return generatedClient.deleteVersion(versionId);
  },
  // RC ID: RC-110. Load recent projects through the generated shared API client.
  projects() {
    return generatedClient.projects();
  },
  // RC ID: RC-194. Hydrate local model UI from the persisted backend lifecycle event.
  localModelState(modelId: string) {
    return fetch(`/api/v1/local-models/${encodeURIComponent(modelId)}/state`, {
      headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
    }).then(async (response) => {
      if (!response.ok) {
        throw new Error("本地模型状态不可用");
      }
      return response.json() as Promise<unknown>;
    });
  },
  localModelEvent(modelId: string, event: { event: string; message?: string; progress?: number; error?: string | null }) {
    return fetch(`/api/v1/local-models/${encodeURIComponent(modelId)}/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      body: JSON.stringify(event),
    }).then(async (response) => {
      if (!response.ok) {
        throw new Error("本地模型事件未接受");
      }
      return response.json() as Promise<unknown>;
    });
  },
  localModelDirectory() {
    return generatedClient.localModelDirectory();
  },
  checkLocalModelDirectory(path: string, requiredBytes = 0) {
    return generatedClient.checkLocalModelDirectory({ path, required_bytes: requiredBytes });
  },
  migrateLocalModelDirectory(destination: string) {
    return generatedClient.migrateLocalModelDirectory({ destination });
  },
  cleanupLocalModels(modelId?: string) {
    return generatedClient.cleanupLocalModels({ model_id: modelId });
  },
  uninstallRegisteredLocalModel(modelId: string) {
    return generatedClient.uninstallRegisteredLocalModel(modelId);
  },
  diff(oldId: number, newId: number) {
    return generatedClient.diff(oldId, newId);
  },
  async export(versionId: number, format: string) {
    const response = await generatedClient.export({
      version_id: versionId,
      format: format as ExportRequest["format"]
    });
    return sanitizePublicText(await response.text());
  }
};

function parseStreamEvent(raw: string): StreamEvent | null {
  const eventLine = raw.split("\n").find((line) => line.startsWith("event: "));
  const dataLine = raw.split("\n").find((line) => line.startsWith("data: "));
  if (!eventLine || !dataLine) {
    return null;
  }
  const payload = JSON.parse(dataLine.slice("data: ".length)) as unknown;
  if (isProtocolStreamEvent(payload)) {
    const envelope = payload as Record<string, unknown>;
    const businessPayload = "payload" in envelope
      ? envelope.payload
      : Object.fromEntries(
          Object.entries(envelope).filter(([key]) => !["protocol_version", "request_id", "seq", "type", "timestamp"].includes(key)),
        );
    return {
      event: payload.type as StreamEventName,
      data: businessPayload,
      seq: payload.seq,
    };
  }
  return {
    event: eventLine.slice("event: ".length) as StreamEventName,
    data: payload,
  };
}

function isProtocolStreamEvent(value: unknown): value is {
  type: string;
  seq: number;
  payload?: unknown;
} {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as { type?: unknown; seq?: unknown; payload?: unknown };
  return typeof candidate.type === "string" && typeof candidate.seq === "number";
}

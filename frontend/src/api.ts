import { createApiClient } from "./generated/client";
import type {
  ExportRequest,
  OptimizeRequest,
  OptimizeResponse
} from "./types";

// RC IDs: RC-058, RC-062. New GUI calls use the generated versioned App Server client.
let accessToken: string | null = localStorage.getItem("prompt_optimizer_token");
const generatedClient = createApiClient({ getToken: () => accessToken });

type Provider = NonNullable<OptimizeRequest["provider"]>;
type StreamEventName =
  | "started"
  | "analysis"
  | "chunk"
  | "fallback"
  | "saved"
  | "completed"
  | "error";
type StreamEvent = { event: StreamEventName; data: unknown };

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
  analyze(prompt: string) {
    return generatedClient.analyze({ prompt });
  },
  optimize(prompt: string, templateId?: string, provider: Provider = "offline") {
    return generatedClient.optimize({ prompt, template_id: templateId, provider });
  },
  async streamOptimize(
    prompt: string,
    templateId: string | undefined,
    provider: Provider,
    onEvent: (event: StreamEvent) => void
  ) {
    const response = await generatedClient.optimizeStream({
      prompt,
      template_id: templateId,
      provider
    });
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
  createOptimizeTask(prompt: string, templateId?: string, provider: Provider = "offline") {
    return generatedClient.createOptimizeTask({ prompt, template_id: templateId, provider });
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
  diff(oldId: number, newId: number) {
    return generatedClient.diff(oldId, newId);
  },
  async export(versionId: number, format: string) {
    const response = await generatedClient.export({
      version_id: versionId,
      format: format as ExportRequest["format"]
    });
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
    event: eventLine.slice("event: ".length) as StreamEventName,
    data: JSON.parse(dataLine.slice("data: ".length)) as unknown
  };
}

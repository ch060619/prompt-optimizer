import { workspaceScope } from "./workspaceRoute";

export type PromptDraft = {
  text: string;
  revision: number;
  cursor: { start: number; end: number };
  attachmentRefs: string[];
};

const emptyDraft: PromptDraft = {
  text: "",
  revision: 0,
  cursor: { start: 0, end: 0 },
  attachmentRefs: [],
};

export function promptDraftStorageKey(search = window.location.search) {
  return `rabbit_code_prompt_draft_${workspaceScope(search)}`;
}

export function readPromptDraft(search = window.location.search): PromptDraft {
  try {
    const parsed = JSON.parse(localStorage.getItem(promptDraftStorageKey(search)) || "null") as Partial<PromptDraft> | null;
    if (!parsed || typeof parsed.text !== "string") {
      return emptyDraft;
    }
    const cursor = parsed.cursor && typeof parsed.cursor === "object"
      ? parsed.cursor as Partial<PromptDraft["cursor"]>
      : {};
    const textLength = parsed.text.length;
    return {
      text: parsed.text,
      revision: typeof parsed.revision === "number" && Number.isInteger(parsed.revision) && parsed.revision >= 0 ? parsed.revision : 0,
      cursor: {
        start: clampCursor(cursor.start, textLength),
        end: clampCursor(cursor.end, textLength),
      },
      attachmentRefs: Array.isArray(parsed.attachmentRefs)
        ? parsed.attachmentRefs.filter((item): item is string => typeof item === "string")
        : [],
    };
  } catch {
    return emptyDraft;
  }
}

export function writePromptDraft(draft: PromptDraft, search = window.location.search) {
  localStorage.setItem(promptDraftStorageKey(search), JSON.stringify(draft));
}

function clampCursor(value: unknown, textLength: number) {
  return typeof value === "number" && Number.isInteger(value)
    ? Math.min(Math.max(value, 0), textLength)
    : 0;
}

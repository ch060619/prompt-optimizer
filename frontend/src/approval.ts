// RC ID: RC-202. Mirror the versioned protocol approval request consumed by GUI and TUI.

export type ApprovalRequest = {
  protocol_version?: "v1";
  approval_id: string;
  request_id: string;
  action: string;
  description: string;
  risk: "low" | "medium" | "high";
  tool: string;
  command: string[];
  paths: string[];
  workdir: string;
  impact: string;
  authorization_scope: string;
  arguments: Record<string, unknown>;
  snapshot: string;
  expires_at: string | null;
};

export function isApprovalRequest(value: unknown): value is ApprovalRequest {
  if (!value || typeof value !== "object") {
    return false;
  }
  const request = value as Partial<ApprovalRequest>;
  return typeof request.approval_id === "string"
    && typeof request.request_id === "string"
    && typeof request.tool === "string"
    && Array.isArray(request.command)
    && request.command.every((item) => typeof item === "string")
    && Array.isArray(request.paths)
    && request.paths.every((item) => typeof item === "string")
    && typeof request.workdir === "string"
    && typeof request.impact === "string"
    && typeof request.authorization_scope === "string";
}

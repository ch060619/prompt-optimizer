import { describe, expect, it } from "vitest";

import { maskSecret, registerRuntimeSecret, sanitizePublicError, sanitizePublicText } from "../src/publicOutput";
import { providerErrorMessage } from "../src/api";

// RC ID: RC-180. Verify public UI and API errors redact provider secrets.

describe("public secret redaction", () => {
  it("redacts common Provider formats and known runtime values", () => {
    registerRuntimeSecret("workspace-secret-value");
    const message = [
      "sk-proj-1234567890abcdef",
      "AIzaSyA1234567890abcdefghijklmnop",
      "sk-ant-api03-1234567890",
      "ghp_123456789012345678901234567890",
      "workspace-secret-value",
    ].join(" ");

    const cleaned = sanitizePublicError(message);

    expect(cleaned).not.toContain("sk-proj-");
    expect(cleaned).not.toContain("AIza");
    expect(cleaned).not.toContain("ghp_");
    expect(cleaned).not.toContain("workspace-secret-value");
  });

  it("masks with a fixed prefix and only exposes the last four characters", () => {
    expect(maskSecret("provider-secret-1234")).toBe("********1234");
    expect(sanitizePublicText("api_key=provider-secret-1234")).toBe("[REDACTED]");
  });

  it("sanitizes the shared API error formatter", () => {
    expect(providerErrorMessage({ message: "api_key=provider-secret-1234" })).toBe("[REDACTED]");
  });
});

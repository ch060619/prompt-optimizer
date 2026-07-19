// RC IDs: RC-141, RC-180. Keep provider errors and secrets safe before visible output.

const credentialAssignment = /\b(?:api[_ -]?key|access[_ -]?token|authorization|bearer|secret|password|cookie)\b\s*[:=]\s*[^\s,;]+/gi;
const bearerToken = /\bbearer\s+[A-Za-z0-9._~+/=-]+/gi;
const providerKeyFormats = [
  /\bsk-(?:proj-)?[A-Za-z0-9_-]{10,}\b/gi,
  /\bsk-ant-[A-Za-z0-9_-]{10,}\b/gi,
  /\bAIza[A-Za-z0-9_-]{20,}\b/g,
  /\bxai-[A-Za-z0-9_-]{10,}\b/gi,
  /\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9_]{20,}\b/gi,
  /\bgithub_pat_[A-Za-z0-9_]{20,}\b/gi,
  /\bhf_[A-Za-z0-9_-]{10,}\b/gi,
  /\br8_[A-Za-z0-9_-]{10,}\b/gi,
];
const secretCandidate = /(?<![A-Za-z0-9])[A-Za-z0-9][A-Za-z0-9._~+/=-]{7,}(?![A-Za-z0-9])/g;
const internalPrompt = /\b(?:system[_ -]?prompt|developer[_ -]?message|internal prompt)\b/i;
const runtimeSecretFingerprints = new Map<string, { length: number }>();

function fingerprint(value: string) {
  let hash = 2166136261;
  for (const character of value) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return `${hash >>> 0}:${value.length}`;
}

export function registerRuntimeSecret(value: unknown) {
  if (typeof value === "string" && value.length >= 8) {
    runtimeSecretFingerprints.set(fingerprint(value), { length: value.length });
  }
}

export function maskSecret(value: string) {
  const tail = value.slice(-4);
  return `********${tail}`;
}

export function maskSecretTail(tail: string) {
  return `********${tail.slice(-4)}`;
}

function redactKnownSecrets(value: string) {
  return value.replace(secretCandidate, (candidate) => runtimeSecretFingerprints.has(fingerprint(candidate)) ? "[REDACTED]" : candidate);
}

export function sanitizePublicText(value: unknown): string {
  let message = String(value ?? "").trim();
  message = message.replace(credentialAssignment, "[REDACTED]").replace(bearerToken, "[REDACTED]");
  for (const format of providerKeyFormats) {
    message = message.replace(format, "[REDACTED]");
  }
  return redactKnownSecrets(message);
}

export function sanitizePublicError(value: unknown): string {
  const message = String(value ?? "").trim();
  if (!message) {
    return "Provider request failed.";
  }
  if (internalPrompt.test(message)) {
    return "Provider error details were redacted.";
  }
  return sanitizePublicText(message).slice(0, 240);
}

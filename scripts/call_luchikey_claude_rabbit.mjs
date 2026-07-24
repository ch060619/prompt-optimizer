import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const workspace = process.cwd();
const serverPath = "C:/Users/10735/.codex/plugins/cache/personal/luchikey-image/0.1.7/scripts/luchikey-image-mcp.mjs";
const outputPath = "output/imagegen/claude-code-rabbit-icon-luchikey.png";
const prompt = `Create a small application welcome-screen icon: the same cute front-facing sitting lop-eared bunny shown in a vintage sepia pencil-and-ink storybook style, wearing a newsboy cap, with a round face, blush cheeks, dark shiny eyes, tiny paws, and visible feet. Use a black background around the bunny so it reads clearly as a terminal welcome icon. No text, no logo, no watermark, no interface, no frame.`;

const child = spawn(process.execPath, [serverPath], {
  cwd: workspace,
  env: { ...process.env, LUCHIKEY_IMAGE_MODEL: "gpt-image-2", LUCHIKEY_IMAGE_OUTPUT_ROOT: workspace },
  stdio: ["pipe", "pipe", "pipe"],
  windowsHide: true,
});

let buffer = "";
const pending = new Map();
child.stdout.setEncoding("utf8");
child.stderr.setEncoding("utf8");
child.stdout.on("data", (chunk) => {
  buffer += chunk;
  for (;;) {
    const newline = buffer.indexOf("\n");
    if (newline < 0) return;
    const raw = buffer.slice(0, newline).trim();
    buffer = buffer.slice(newline + 1);
    if (!raw) continue;
    const message = JSON.parse(raw);
    const resolve = pending.get(message.id);
    if (resolve) {
      pending.delete(message.id);
      resolve(message);
    }
  }
});
child.stderr.on("data", (chunk) => process.stderr.write(chunk));

let nextId = 1;
function request(method, params = {}) {
  const id = nextId++;
  child.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", id, method, params })}\n`);
  return new Promise((resolve, reject) => {
    pending.set(id, resolve);
    setTimeout(() => reject(new Error(`${method} timed out`)), 600000);
  });
}

try {
  const init = await request("initialize", { protocolVersion: "2024-11-05", capabilities: {} });
  if (init.error) throw new Error(init.error.message);
  child.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized", params: {} })}\n`);
  const result = await request("tools/call", {
    name: "generate_image",
    arguments: {
      prompt,
      model: "gpt-image-2",
      size: "1024x1024",
      quality: "high",
      output_format: "png",
      output_path: outputPath,
      overwrite: true,
    },
  });
  if (result.error) throw new Error(result.error.message);
  const structured = result.result?.structuredContent || {};
  const summary = {
    ok: structured.ok,
    model: structured.model,
    size: structured.size,
    quality: structured.quality,
    saved_path: structured.saved_path,
    attempts: structured.attempts,
  };
  await mkdir(path.dirname(path.join(workspace, outputPath)), { recursive: true });
  await writeFile(path.join(workspace, "output/imagegen/claude-code-rabbit-luchikey-result.json"), JSON.stringify(summary, null, 2), "utf8");
  console.log(JSON.stringify(summary));
} finally {
  child.kill();
}

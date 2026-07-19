import { ArrowUpRight, Cpu, Download, GitCompare, History, Library, Search, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { api, providerErrorMessage, type Provider } from "./api";
import { PRODUCT_NAME } from "./brand";
import type {
  DiffResult,
  OptimizationTargets,
  OptimizeResponse,
  PromptAnalysis,
  PromptTemplate,
  TaskRecord,
  UserPublic,
  VersionSummary
} from "./types";
import { SiteShell } from "./components/SiteShell";
import { AuthPage, SiteRoute } from "./marketing";
import { OnboardingPage } from "./onboarding";
import { WorkspaceHome } from "./workspaceHome";
import { TaskWorkspace } from "./taskWorkspace";
import { ChangeReview } from "./changeReview";
import { TerminalProcessPanel } from "./terminalProcess";
import { ProviderModels } from "./providerModels";
import { LocalModels } from "./localModels";
import { PromptAssets } from "./promptAssets";
import { Settings } from "./settings";
import { Diagnostics } from "./diagnostics";
import { ErrorState } from "./components/UiStates";
import { RabbitMark } from "./components/RabbitMark";
import { PromptOptimizeButton, type PromptOptimizationSnapshot } from "./components/PromptOptimizeButton";
import { PromptOptimizationDiff } from "./components/PromptOptimizationDiff";
import { PromptOptimizationControls, type OptimizationStrength } from "./components/PromptOptimizationControls";
import { sanitizePublicError } from "./publicOutput";
import { LOCAL_MODEL_OPTIONS, localModelOption, localModelReady, readDefaultLocalModel, readSessionLocalModel, writeSessionLocalModel } from "./localModelSelection";

// RC ID: RC-050. Surface offline-rule identity and fallback reasons in the workspace.
// RC ID: RC-054. Use Rabbit Code as the canonical workspace identity.
// RC ID: RC-154. Map composer presets to the generated optimization-target contract.

const categories = ["all", "tech", "creative", "business", "education", "general"];
const categoryLabels: Record<string, string> = {
  all: "全部",
  tech: "技术",
  creative: "创意",
  business: "商务",
  education: "教育",
  general: "通用"
};

const fallbackReasonLabels: Record<string, string> = {
  not_installed: "未安装",
  not_ready: "未就绪",
  out_of_memory: "资源不足",
  timeout: "响应超时",
};

const recoveryActionLabels: Record<string, string> = {
  install: "安装本地模型",
  repair: "修复本地模型",
  free_memory: "检查本地资源",
  retry: "重试本地模型",
  configure_credentials: "配置 Provider 凭据",
  check_balance: "检查 Provider 余额",
  wait_and_retry: "等待后重试",
  change_region: "更换区域",
  choose_model: "选择可用模型",
  fix_parameters: "修正请求参数",
  review_content: "检查内容过滤",
  check_network: "检查网络连接",
  cancel: "取消请求",
};

const recoveryActionPaths: Record<string, string> = {
  install: "/workspace/models",
  repair: "/workspace/models",
  free_memory: "/workspace/models",
  configure_credentials: "/workspace/providers",
  check_balance: "/workspace/providers",
  wait_and_retry: "/workspace",
  change_region: "/workspace/providers",
  choose_model: "/workspace/models",
  fix_parameters: "/workspace",
  review_content: "/workspace",
  check_network: "/workspace/diagnostics",
  retry: "/workspace/models",
  cancel: "/workspace",
};

const recoveryActionAriaLabels: Record<string, string> = {
  install: "安装或修复本地模型",
  repair: "安装或修复本地模型",
  free_memory: "安装或修复本地模型",
};

function readShortcutPreset(): "default" | "vim" {
  const scope = (new URLSearchParams(window.location.search).get("workspace") || "default").replace(/[^a-zA-Z0-9_-]/g, "-");
  try {
    const settings = JSON.parse(localStorage.getItem(`rabbit_code_settings_${scope}`) || "null") as { shortcutPreset?: unknown } | null;
    return settings?.shortcutPreset === "vim" ? "vim" : "default";
  } catch {
    return "default";
  }
}

function readSavePromptHistory(): boolean {
  const scope = (new URLSearchParams(window.location.search).get("workspace") || "default").replace(/[^a-zA-Z0-9_-]/g, "-");
  try {
    const settings = JSON.parse(localStorage.getItem(`rabbit_code_settings_${scope}`) || "null") as { savePromptHistory?: unknown } | null;
    return settings?.savePromptHistory !== false;
  } catch {
    return true;
  }
}

function readOptimizationRoute(): { provider: Provider; model?: string } {
  const scope = (new URLSearchParams(window.location.search).get("workspace") || "default").replace(/[^a-zA-Z0-9_-]/g, "-");
  try {
    const route = JSON.parse(localStorage.getItem(`rabbit_code_provider_route_${scope}`) || "null") as { provider?: unknown; model?: unknown; enabled?: unknown } | null;
    if (route?.enabled === false) {
      return { provider: "offline" };
    }
    const provider = route?.provider;
    if (
      provider === "offline"
      || provider === "local"
      || provider === "openai"
      || provider === "tongyi"
      || provider === "zhipu"
      || provider === "anthropic"
      || provider === "gemini"
      || provider === "azure"
      || provider === "vertex"
      || provider === "bedrock"
      || provider === "openrouter"
      || provider === "deepseek"
      || provider === "moonshot"
      || provider === "qwen"
      || provider === "doubao"
      || provider === "siliconflow"
      || provider === "groq"
      || provider === "together"
      || provider === "ollama"
      || provider === "lmstudio"
    ) {
      return { provider, model: typeof route?.model === "string" && route.model ? route.model : undefined };
    }
  } catch {
    return { provider: "offline" };
  }
  const defaultLocalModel = localStorage.getItem("rabbit_code_default_local_model");
  if (defaultLocalModel && localModelReady(defaultLocalModel)) {
    return { provider: "local", model: defaultLocalModel };
  }
  return { provider: "offline" };
}

export function App() {
  const pathname = window.location.pathname;
  const isWorkspaceRoute = pathname === "/workspace";
  const isWorkspaceHomeRoute = pathname === "/workspace/home";
  const isTaskWorkspaceRoute = pathname === "/workspace/task";
  const isChangeReviewRoute = pathname === "/workspace/review";
  const isTerminalProcessRoute = pathname === "/workspace/terminal";
  const isProviderModelsRoute = pathname === "/workspace/providers";
  const isLocalModelsRoute = pathname === "/workspace/models";
  const isPromptAssetsRoute = pathname === "/workspace/assets";
  const isSettingsRoute = pathname === "/workspace/settings";
  const isDiagnosticsRoute = pathname === "/workspace/diagnostics";
  const isOnboardingRoute = pathname === "/onboarding";
  const authMode = pathname === "/register" ? "register" : pathname === "/login" ? "login" : null;
  const showSharedRabbit = !isWorkspaceRoute && !isWorkspaceHomeRoute && !isTaskWorkspaceRoute && !isChangeReviewRoute && !isTerminalProcessRoute && !isProviderModelsRoute && !isLocalModelsRoute && !isPromptAssetsRoute && !isSettingsRoute && !isDiagnosticsRoute && !isOnboardingRoute && pathname !== "/" && !authMode;
  const [prompt, setPrompt] = useState("你是一名产品顾问，请帮我优化一个 SaaS 产品发布邮件。");
  const [promptRevision, setPromptRevision] = useState(0);
  const [promptCursor, setPromptCursor] = useState({ start: 0, end: 0 });
  const promptRevisionRef = useRef(0);
  const optimizeButtonRef = useRef<HTMLButtonElement>(null);
  const [category, setCategory] = useState("all");
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string | undefined>();
  const [analysis, setAnalysis] = useState<PromptAnalysis | null>(null);
  const [history, setHistory] = useState<VersionSummary[]>([]);
  const [diff, setDiff] = useState<DiffResult | null>(null);
  const [activeVersion, setActiveVersion] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [streamStatus, setStreamStatus] = useState<string | null>(null);
  const [streamText, setStreamText] = useState("");
  const [providerMetadata, setProviderMetadata] = useState<OptimizeResponse["metadata"] | null>(null);
  const [user, setUser] = useState<UserPublic | null>(null);
  const [username, setUsername] = useState("demo-user");
  const [password, setPassword] = useState("demo-password");
  const [task, setTask] = useState<TaskRecord | null>(null);
  const [pendingOptimization, setPendingOptimization] = useState<{ result: OptimizeResponse; snapshot: PromptOptimizationSnapshot } | null>(null);
  const [optimizationPreview, setOptimizationPreview] = useState<{ text: string; original: string } | null>(null);
  const [scenario, setScenario] = useState("通用");
  const [optimizationRole, setOptimizationRole] = useState("不指定");
  const [optimizationStrength, setOptimizationStrength] = useState<OptimizationStrength>("balanced");
  const [scoreEnabled, setScoreEnabled] = useState(true);
  const [shortcutPreset] = useState<"default" | "vim">(readShortcutPreset);
  const [savePromptHistory] = useState(readSavePromptHistory);
  const [defaultOptimizationRoute] = useState(readOptimizationRoute);
  const [sessionLocalModel, setSessionLocalModel] = useState(() => readSessionLocalModel());
  const optimizationRoute = sessionLocalModel
    ? { provider: "local" as Provider, model: sessionLocalModel }
    : defaultOptimizationRoute;
  const optimizationReturnFocusRef = useRef<HTMLElement | null>(null);

  const visibleTemplates = useMemo(() => templates, [templates]);

  useEffect(() => {
    if (!isWorkspaceRoute) {
      return;
    }
    function handleShortcut(event: KeyboardEvent) {
      const key = event.key.toLowerCase();
      const matches = shortcutPreset === "vim"
        ? event.altKey && !event.ctrlKey && !event.metaKey && key === "o"
        : event.ctrlKey && event.shiftKey && !event.altKey && !event.metaKey && key === "o";
      if (!event.isComposing && matches) {
        event.preventDefault();
        optimizeButtonRef.current?.focus();
        optimizeButtonRef.current?.click();
      }
    }
    document.addEventListener("keydown", handleShortcut);
    return () => document.removeEventListener("keydown", handleShortcut);
  }, [isWorkspaceRoute, shortcutPreset]);

  useEffect(() => {
    if (!isWorkspaceRoute) {
      return;
    }
    void withLoading(async () => {
      if (api.getToken()) {
        setUser(await api.me());
      }
      await loadTemplates(category);
      if (api.getToken()) {
        await loadHistory();
      } else {
        setHistory([]);
      }
    });
  }, [category, isWorkspaceRoute]);

  async function runAuth(mode: "login" | "register") {
    await withLoading(async () => {
      const result =
        mode === "login"
          ? await api.login(username, password)
          : await api.register(username, password);
      api.setToken(result.access_token);
      setUser(result.user);
      await loadHistory();
      if (authMode) {
        window.location.assign("/workspace");
      }
    });
  }

  async function logout() {
    api.setToken(null);
    setUser(null);
    setHistory([]);
    window.location.assign("/");
  }

  async function loadTemplates(nextCategory: string) {
    const items = await api.templates(nextCategory === "all" ? undefined : nextCategory);
    setTemplates(items);
  }

  async function loadHistory() {
    const items = await api.history();
    setHistory(items);
  }

  function selectTemplate(templateId: string) {
    const template = templates.find((item) => item.id === templateId);
    setSelectedTemplate(templateId || undefined);
    if (!template) {
      return;
    }
    setPrompt(template.template);
    bumpPromptRevision();
    setPromptCursor({ start: template.template.length, end: template.template.length });
  }

  function buildOptimizationInput(source: string) {
    const controls = [
      scenario !== "通用" ? `scenario: ${scenario === "代码生成" ? "code generation" : scenario === "内容改写" ? "content rewrite" : "analysis"}` : null,
      optimizationRole !== "不指定" ? `role: ${optimizationRole === "领域专家" ? "domain expert" : optimizationRole === "产品经理" ? "product manager" : "teacher"}` : null,
      optimizationStrength !== "balanced"
        ? `optimization strength: ${optimizationStrength === "light" ? "light" : "deep"}`
        : null,
      scoreEnabled ? null : "score generation: off",
    ].filter((item): item is string => item !== null);
    return controls.length ? `${source}\n\n优化控制：\n${controls.join("\n")}` : source;
  }

  function optimizationTargets(): OptimizationTargets {
    return {
      clarity: true,
      completeness: optimizationStrength !== "light",
      constraints: optimizationStrength === "strong",
      format: optimizationStrength !== "light",
      role: optimizationRole !== "不指定",
      examples: optimizationStrength === "strong",
      code_task: scenario === "代码生成",
      conciseness: true,
      language_preservation: true,
    };
  }

  function selectSessionLocalModel(modelId: string) {
    if (loading) {
      setError("请先取消当前生成，再切换会话模型。");
      return;
    }
    if (!modelId) {
      writeSessionLocalModel(null);
      setSessionLocalModel(null);
      setError(null);
      return;
    }
    const option = localModelOption(modelId);
    if (!option || !localModelReady(modelId)) {
      setError("本地模型尚未就绪，请先完成安装和健康检查。");
      return;
    }
    if (prompt.length > option.contextLength) {
      setError(`当前提示词超过 ${option.label} 的上下文长度限制。`);
      return;
    }
    writeSessionLocalModel(modelId);
    setSessionLocalModel(modelId as NonNullable<typeof sessionLocalModel>);
    setError(null);
  }

  async function runAnalyze() {
    await withLoading(async () => {
      setAnalysis(await api.analyze(prompt));
      setProviderMetadata(null);
      setDiff(null);
    });
  }

  async function runOptimize(_requestId: string, signal: AbortSignal, snapshot: PromptOptimizationSnapshot): Promise<void> {
    setLoading(true);
    setError(null);
    try {
      const result = await api.optimize(buildOptimizationInput(snapshot.text), selectedTemplate, optimizationRoute.provider, signal, savePromptHistory, optimizationRoute.model, undefined, undefined, optimizationTargets());
      if (signal.aborted) {
        return;
      }
      if (snapshot.revision !== promptRevisionRef.current) {
        setPendingOptimization({ result, snapshot });
        return;
      }
      applyOptimizeResult(result, snapshot.text);
      setDiff(null);
      if (user) {
        await loadHistory();
      }
    } catch (err) {
      if (signal.aborted) {
        return;
      }
      setError(sanitizePublicError(providerErrorMessage(err)));
      throw err;
    } finally {
      setLoading(false);
    }
  }

  async function runStreamOptimize() {
    await withLoading(async () => {
      setStreamText("");
      setProviderMetadata(null);
      setStreamStatus("准备优化");
      await api.streamOptimize(buildOptimizationInput(prompt), selectedTemplate, optimizationRoute.provider, (event) => {
        if (event.event === "started") {
          setStreamStatus("开始优化");
        }
        if (event.event === "analysis") {
          setStreamStatus("完成初始分析");
          setAnalysis(event.data as PromptAnalysis);
        }
        if (event.event === "delta" || event.event === "chunk") {
          const payload = event.data as { text: string };
          setStreamStatus("生成优化文本");
          setStreamText((current) => current + payload.text);
        }
        if (event.event === "fallback") {
          const metadata = event.data as OptimizeResponse["metadata"];
          setProviderMetadata(metadata);
          setStreamStatus(
            metadata.error_summary
              ? `已使用离线规则：${metadata.error_summary}`
              : "已使用离线规则"
          );
        }
        if (event.event === "saved") {
          const payload = event.data as { version_id: number };
          setActiveVersion(payload.version_id);
        }
        if (event.event === "completed") {
          applyOptimizeResult(event.data as OptimizeResponse, prompt);
          setStreamStatus("优化完成");
        }
        if (event.event === "cancelled") {
          setStreamStatus("优化已取消");
        }
        if (event.event === "error") {
          const payload = event.data as { detail: string };
          throw new Error(providerErrorMessage(payload));
        }
      }, savePromptHistory, optimizationRoute.model, undefined, undefined, optimizationTargets());
      setDiff(null);
      if (user) {
        await loadHistory();
      }
    });
  }

  async function runOptimizeTask() {
    await withLoading(async () => {
      const created = await api.createOptimizeTask(buildOptimizationInput(prompt), selectedTemplate, optimizationRoute.provider, savePromptHistory, optimizationRoute.model, undefined, undefined, optimizationTargets());
      let current = await api.task(created.task_id);
      setTask(current);
      for (let attempt = 0; attempt < 5 && ["queued", "running"].includes(current.status); attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 250));
        current = await api.task(created.task_id);
        setTask(current);
      }
      if (current.status === "succeeded") {
        applyOptimizeResult(await api.taskResult(created.task_id), prompt);
        await loadHistory();
      }
      if (current.status === "failed") {
        throw new Error(current.error ?? "后台任务失败");
      }
    });
  }

  function applyOptimizeResult(result: OptimizeResponse, originalPrompt = prompt) {
    setAnalysis(result.analysis);
    if (result.analysis.optimized_prompt) {
      if (document.activeElement instanceof HTMLElement) {
        optimizationReturnFocusRef.current = document.activeElement;
      }
      setOptimizationPreview({ text: result.analysis.optimized_prompt, original: originalPrompt });
    }
    // RC ID: RC-062. Respect the optional version_id generated from OpenAPI.
    setActiveVersion(result.version_id ?? null);
    setProviderMetadata(result.metadata);
  }

  function closeOptimizationPreview() {
    setOptimizationPreview(null);
    queueMicrotask(() => optimizationReturnFocusRef.current?.focus());
  }

  async function runDiff(targetId: number) {
    if (!activeVersion || activeVersion === targetId) {
      return;
    }
    await withLoading(async () => {
      setDiff(await api.diff(targetId, activeVersion));
    });
  }

  async function runExport(format: string) {
    if (!activeVersion) {
      setError("请先执行一次优化生成版本。");
      return;
    }
    await withLoading(async () => {
      const content = await api.export(activeVersion, format);
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `prompt-version-${activeVersion}.${format}`;
      link.click();
      URL.revokeObjectURL(url);
    });
  }

  async function withLoading(task: () => Promise<void>) {
    setLoading(true);
    setError(null);
    try {
      await task();
    } catch (err) {
      setError(sanitizePublicError(providerErrorMessage(err)));
    } finally {
      setLoading(false);
    }
  }

  if (isOnboardingRoute) {
    return (
      <SiteShell>
        <OnboardingPage />
      </SiteShell>
    );
  }

  async function acceptActiveVersion() {
    if (!user || activeVersion === null) {
      return;
    }
    await withLoading(async () => {
      await api.acceptVersion(activeVersion);
      await loadHistory();
    });
  }

  async function deleteVersion(versionId: number) {
    await withLoading(async () => {
      await api.deleteVersion(versionId);
      setHistory((current) => current.filter((item) => item.id !== versionId));
      setDiff(null);
      if (activeVersion === versionId) {
        setActiveVersion(null);
        setOptimizationPreview(null);
      }
      await loadHistory();
    });
  }

  function bumpPromptRevision() {
    setPromptRevision((current) => {
      const next = current + 1;
      promptRevisionRef.current = next;
      return next;
    });
  }

  if (isWorkspaceHomeRoute) {
    return (
      <SiteShell authenticated={Boolean(api.getToken())} isWorkspace rabbitVariant="empty">
        <WorkspaceHome />
      </SiteShell>
    );
  }

  if (isTaskWorkspaceRoute) {
    return (
      <SiteShell authenticated={Boolean(api.getToken())} isWorkspace rabbitVariant="mark">
        <TaskWorkspace />
      </SiteShell>
    );
  }

  if (isChangeReviewRoute) {
    return (
      <SiteShell authenticated={Boolean(api.getToken())} isWorkspace rabbitVariant="mark">
        <ChangeReview />
      </SiteShell>
    );
  }

  if (isTerminalProcessRoute) {
    return (
      <SiteShell authenticated={Boolean(api.getToken())} isWorkspace rabbitVariant="mono">
        <TerminalProcessPanel />
      </SiteShell>
    );
  }

  if (isProviderModelsRoute) {
    return (
      <SiteShell authenticated={Boolean(api.getToken())} isWorkspace rabbitVariant="mark">
        <ProviderModels setupMode={new URLSearchParams(window.location.search).get("entry") === "api"} />
      </SiteShell>
    );
  }

  if (isLocalModelsRoute) {
    return (
      <SiteShell authenticated={Boolean(api.getToken())} isWorkspace rabbitVariant="mark">
        <LocalModels setupMode={new URLSearchParams(window.location.search).get("entry") === "local"} />
      </SiteShell>
    );
  }

  if (isPromptAssetsRoute) {
    return (
      <SiteShell authenticated={Boolean(api.getToken())} isWorkspace rabbitVariant="mark">
        <PromptAssets />
      </SiteShell>
    );
  }

  if (isSettingsRoute) {
    return (
      <SiteShell authenticated={Boolean(api.getToken())} isWorkspace rabbitVariant="mark">
        <Settings />
      </SiteShell>
    );
  }

  if (isDiagnosticsRoute) {
    return (
      <SiteShell authenticated={Boolean(api.getToken())} isWorkspace rabbitVariant="mark">
        <Diagnostics />
      </SiteShell>
    );
  }

  if (!isWorkspaceRoute) {
    if (authMode) {
      return (
        <SiteShell>
          <AuthPage
            mode={authMode}
            username={username}
            password={password}
            loading={loading}
            error={error}
            user={user}
            onUsernameChange={setUsername}
            onPasswordChange={setPassword}
            onSubmit={(event) => { event.preventDefault(); void runAuth(authMode); }}
          />
        </SiteShell>
      );
    }
    return (
      <SiteShell showSharedRabbit={showSharedRabbit}>
        <SiteRoute path={pathname} />
      </SiteShell>
    );
  }

  return (
    <SiteShell authenticated={Boolean(user)} isWorkspace onSignOut={() => void logout()}>
      <main className="app-shell">
      <h1 className="sr-only">提示词工作区</h1>
      <aside className="sidebar" aria-label="Template library">
        <div className="brand">
          <RabbitMark variant="mark" decorative size={22} />
          <span>{PRODUCT_NAME}</span>
        </div>
        <div className="workspace-rabbit">
          <RabbitMark variant="full" alt="Rabbit Code 兔兔品牌插画" loading="eager" />
        </div>
        {user ? (
          <div className="workspace-account">
            <strong>{user.username}</strong>
            <span>ACCOUNT ACTIVE</span>
          </div>
        ) : (
          <div className="workspace-account workspace-guest">
            <strong>GUEST MODE</strong>
            <span>HISTORY IS NOT SAVED</span>
            <div className="guest-links">
              <a href="/login">LOGIN</a>
              <a href="/register">REGISTER</a>
            </div>
          </div>
        )}
        <div className="section-title">
          <Library size={16} aria-hidden="true" />
          <span>模板库</span>
        </div>
        <div className="category-tabs">
          {categories.map((item) => (
            <button
              key={item}
              className={item === category ? "active" : ""}
              onClick={() => setCategory(item)}
            >
              {categoryLabels[item]}
            </button>
          ))}
        </div>
        <div className="template-list">
          {visibleTemplates.map((template) => (
            <button
              className={selectedTemplate === template.id ? "template active" : "template"}
              key={template.id}
              onClick={() => selectTemplate(template.id)}
            >
              <strong>{template.name}</strong>
              <span>{template.description}</span>
            </button>
          ))}
        </div>
      </aside>

      <section className="workspace">
        <div className="toolbar">
          <label className="workspace-session-model">
            <Cpu size={15} aria-hidden="true" />
            <span>SESSION MODEL</span>
            <select
              aria-label="Session local model"
              value={sessionLocalModel || ""}
              onChange={(event) => selectSessionLocalModel(event.target.value)}
              disabled={loading}
            >
              <option value="">DEFAULT / {localModelOption(readDefaultLocalModel())?.label || "OFFLINE ROUTE"}</option>
              {LOCAL_MODEL_OPTIONS.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label} / {localModelReady(option.id) ? "READY" : "NOT READY"} / {option.contextLength} TOKENS
                </option>
              ))}
            </select>
          </label>
          <button onClick={runAnalyze} title="分析提示词" disabled={loading}>
            <Search size={15} aria-hidden="true" />
            分析
          </button>
          <PromptOptimizeButton
            icon={<Sparkles size={15} aria-hidden="true" />}
            label={user && savePromptHistory ? "优化并保存" : "优化"}
            ariaLabel="优化输入内容"
            tooltip="优化输入内容"
            disabled={loading}
            input={prompt}
            revision={promptRevision}
            cursor={promptCursor}
            buttonRef={optimizeButtonRef}
            onValidationError={setError}
            onOptimize={runOptimize}
          />
          <PromptOptimizationControls
            templates={visibleTemplates}
            selectedTemplate={selectedTemplate}
            onTemplateChange={selectTemplate}
            scenario={scenario}
            onScenarioChange={setScenario}
            role={optimizationRole}
            onRoleChange={setOptimizationRole}
            strength={optimizationStrength}
            onStrengthChange={setOptimizationStrength}
            scoreEnabled={scoreEnabled}
            onScoreEnabledChange={setScoreEnabled}
            history={history}
            activeVersion={activeVersion}
            onCompareVersion={(versionId) => void runDiff(versionId)}
          />
          <button onClick={() => void runStreamOptimize()} title="流式优化提示词" disabled={loading}>
            <Sparkles size={15} aria-hidden="true" />
            流式优化
          </button>
          <button onClick={() => void runOptimizeTask()} title="后台优化提示词" disabled={loading || !user}>
            <Sparkles size={15} aria-hidden="true" />
            后台优化
          </button>
          {["md", "json", "txt", "csv"].map((format) => (
            <button key={format} onClick={() => void runExport(format)} title={`导出 ${format}`} disabled={loading || !user || !activeVersion}>
              <Download size={15} aria-hidden="true" />
              {format.toUpperCase()}
            </button>
          ))}
        </div>
        {error ? <ErrorState title={error} description="The operation did not complete. Check the local service and try again." /> : null}
        {pendingOptimization ? (
          <section className="prompt-optimization-compare" aria-label="Optimization result ready" role="status">
            <strong>输入已改变，优化结果待比较</strong>
            <span>结果基于 revision {pendingOptimization.snapshot.revision}；当前输入是 revision {promptRevision}。</span>
            <div>
              <button type="button" onClick={() => { applyOptimizeResult(pendingOptimization.result, pendingOptimization.snapshot.text); setPendingOptimization(null); }}>查看比较</button>
              <button type="button" onClick={() => { setPendingOptimization(null); optimizeButtonRef.current?.focus(); optimizeButtonRef.current?.click(); }}>重新优化</button>
            </div>
          </section>
        ) : null}
        <textarea
          aria-label="提示词输入"
          value={prompt}
          onChange={(event) => {
            setPrompt(event.target.value);
            bumpPromptRevision();
            setPromptCursor({ start: event.target.selectionStart, end: event.target.selectionEnd });
          }}
          onSelect={(event) => setPromptCursor({ start: event.currentTarget.selectionStart, end: event.currentTarget.selectionEnd })}
        />
        {streamStatus ? (
          <section className="stream-panel" role="status" aria-live="polite" aria-atomic="true">
            <strong>{streamStatus}</strong>
            {streamText ? <pre aria-hidden="true">{streamText}</pre> : null}
          </section>
        ) : null}
        {task ? (
          <section className="task-panel">
            <strong>后台任务</strong>
            <span>{task.kind} · {task.status}</span>
          </section>
        ) : null}
        {analysis ? (
          <section className="result-panel">
            {providerMetadata ? (
              <div
                aria-label="Optimization metadata"
                className={providerMetadata.fallback_used ? "provider-status fallback" : "provider-status"}
                role="region"
              >
                <strong>{providerMetadata.provider_display_name || (providerMetadata.provider_used === "offline" ? "离线规则" : providerMetadata.provider_used)}</strong>
                <span>模型：{providerMetadata.model || (providerMetadata.provider_used === "offline" ? "规则引擎" : "未声明")}</span>
                <span>{(providerMetadata.execution_location || (providerMetadata.provider_used === "offline" ? "local" : "cloud")) === "local" ? "本地" : "云端"}</span>
                <span>{providerMetadata.fallback_used ? "已降级到离线规则" : "未降级"}</span>
                <span>选择来源：{providerMetadata.selection_scope || "default"}</span>
                <span>健康：{providerMetadata.provider_health || "unknown"}</span>
                <span>{providerMetadata.latency_ms} ms</span>
                {providerMetadata.credential_ref ? <span>密钥引用：{providerMetadata.credential_ref}</span> : null}
                {providerMetadata.error_code ? <span>错误码：{providerMetadata.error_code}</span> : null}
                {providerMetadata.error_category ? <span>错误分类：{providerMetadata.error_category}</span> : null}
                {providerMetadata.provider_request_id ? <span>Provider 请求 ID：{providerMetadata.provider_request_id}</span> : null}
                {providerMetadata.fallback_reason ? <span>降级原因：{fallbackReasonLabels[providerMetadata.fallback_reason] || providerMetadata.fallback_reason}</span> : null}
                {providerMetadata.error_summary ? <span>错误：{sanitizePublicError(providerMetadata.error_summary)}</span> : null}
                {providerMetadata.recovery_action ? <a href={recoveryActionPaths[providerMetadata.recovery_action] || "/workspace"} aria-label={recoveryActionAriaLabels[providerMetadata.recovery_action] || recoveryActionLabels[providerMetadata.recovery_action] || "处理 Provider 错误"}>{recoveryActionLabels[providerMetadata.recovery_action] || "处理 Provider 错误"}<ArrowUpRight size={14} aria-hidden="true" /></a> : null}
              </div>
            ) : null}
            <div className="score-head">
              <span>总分</span>
              <strong>{analysis.score.total_score}</strong>
            </div>
            {analysis.optimized_prompt ? (
              <>
                <h2>优化后提示词</h2>
                {optimizationPreview ? (
                  <PromptOptimizationDiff
                    original={optimizationPreview.original}
                    optimized={optimizationPreview.text}
                    onOptimizedChange={(text) => setOptimizationPreview((current) => current ? { ...current, text } : current)}
                    onReplaceSelected={(text) => {
                      setPrompt(text);
                      bumpPromptRevision();
                      setPromptCursor({ start: text.length, end: text.length });
                      setOptimizationPreview(null);
                      void acceptActiveVersion();
                    }}
                    onReplaceAll={() => {
                      if (!optimizationPreview) return;
                      setPrompt(optimizationPreview.text);
                      bumpPromptRevision();
                      setPromptCursor({ start: optimizationPreview.text.length, end: optimizationPreview.text.length });
                      setOptimizationPreview(null);
                      void acceptActiveVersion();
                    }}
                    onClose={closeOptimizationPreview}
                    onRetry={() => { setOptimizationPreview(null); optimizeButtonRef.current?.focus(); optimizeButtonRef.current?.click(); }}
                  />
                ) : <pre>{analysis.optimized_prompt}</pre>}
              </>
            ) : null}
            <h2>优化建议</h2>
            <div className="suggestions">
              {analysis.suggestions.map((item) => (
                <article key={`${item.dimension}-${item.title}`}>
                  <span className={`priority ${item.priority}`}>{item.priority}</span>
                  <h3>{item.title}</h3>
                  <p>{item.detail}</p>
                  <code>{item.example}</code>
                </article>
              ))}
            </div>
          </section>
        ) : null}
      </section>

      <aside className="inspector" aria-label="Version history">
        <div className="section-title">
          <History size={16} aria-hidden="true" />
          <span>历史版本</span>
        </div>
        <div className="score-bars">
          {analysis?.score.dimensions.map((dimension) => (
            <div className="bar-row" key={dimension.name}>
              <span>{dimension.label}</span>
              <div><i style={{ width: `${dimension.score}%` }} /></div>
              <b>{Math.round(dimension.score)}</b>
            </div>
          ))}
        </div>
        <div className="history-list">
          {history.map((item) => (
            <div className="history-entry" key={item.id}>
              <button type="button" onClick={() => void runDiff(item.id)}>
                <span>#{item.id} · {item.score}{item.accepted ? " · 已采用" : ""}</span>
                <small>{item.original_preview}</small>
                <small>{item.provider_used || "Provider 未声明"}{item.model ? ` · ${item.model}` : ""}</small>
                <small>{item.selection_scope || "default"} · {item.provider_health || "unknown"}</small>
              </button>
              <button
                type="button"
                className="icon-button"
                aria-label={`删除版本 ${item.id}`}
                title={`删除版本 ${item.id}`}
                disabled={loading}
                onClick={() => void deleteVersion(item.id)}
              >
                <Trash2 size={14} aria-hidden="true" />
              </button>
            </div>
          ))}
        </div>
        {!user ? <div className="guest-note">GUEST MODE / HISTORY IS NOT SAVED <a href="/login">LOGIN TO SAVE</a></div> : null}
        {diff ? (
          <section className="diff-panel">
            <div className="section-title">
              <GitCompare size={16} aria-hidden="true" />
              <span>版本对比</span>
            </div>
            <p>分数变化：{diff.old_score} → {diff.new_score} ({diff.score_delta >= 0 ? "+" : ""}{diff.score_delta})</p>
            <pre>{diff.diff_lines.join("\n")}</pre>
          </section>
        ) : null}
      </aside>
      </main>
    </SiteShell>
  );
}

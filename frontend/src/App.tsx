import { Download, GitCompare, History, Library, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { api } from "./api";
import type {
  DiffResult,
  OptimizeResponse,
  PromptAnalysis,
  PromptTemplate,
  TaskRecord,
  UserPublic,
  VersionSummary
} from "./types";
import { SiteShell } from "./components/SiteShell";
import { AuthPage, SiteRoute } from "./marketing";

const categories = ["all", "tech", "creative", "business", "education", "general"];
const categoryLabels: Record<string, string> = {
  all: "全部",
  tech: "技术",
  creative: "创意",
  business: "商务",
  education: "教育",
  general: "通用"
};

export function App() {
  const pathname = window.location.pathname;
  const isWorkspaceRoute = pathname === "/workspace";
  const authMode = pathname === "/register" ? "register" : pathname === "/login" ? "login" : null;
  const showSharedRabbit = !isWorkspaceRoute && pathname !== "/" && !authMode;
  const [prompt, setPrompt] = useState("你是一名产品顾问，请帮我优化一个 SaaS 产品发布邮件。");
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
  const [user, setUser] = useState<UserPublic | null>(null);
  const [username, setUsername] = useState("demo-user");
  const [password, setPassword] = useState("demo-password");
  const [task, setTask] = useState<TaskRecord | null>(null);

  const visibleTemplates = useMemo(() => templates, [templates]);

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

  async function runAnalyze() {
    await withLoading(async () => {
      setAnalysis(await api.analyze(prompt));
      setDiff(null);
    });
  }

  async function runOptimize() {
    await withLoading(async () => {
      const result = await api.optimize(prompt, selectedTemplate);
      applyOptimizeResult(result);
      setDiff(null);
      if (user) {
        await loadHistory();
      }
    });
  }

  async function runStreamOptimize() {
    await withLoading(async () => {
      setStreamText("");
      setStreamStatus("准备优化");
      await api.streamOptimize(prompt, selectedTemplate, "offline", (event) => {
        if (event.event === "started") {
          setStreamStatus("开始优化");
        }
        if (event.event === "analysis") {
          setStreamStatus("完成初始分析");
          setAnalysis(event.data as PromptAnalysis);
        }
        if (event.event === "chunk") {
          const payload = event.data as { text: string };
          setStreamStatus("生成优化文本");
          setStreamText((current) => current + payload.text);
        }
        if (event.event === "fallback") {
          setStreamStatus("模型失败，已降级到离线规则");
        }
        if (event.event === "saved") {
          const payload = event.data as { version_id: number };
          setActiveVersion(payload.version_id);
        }
        if (event.event === "completed") {
          applyOptimizeResult(event.data as OptimizeResponse);
          setStreamStatus("优化完成");
        }
        if (event.event === "error") {
          const payload = event.data as { detail: string };
          throw new Error(payload.detail);
        }
      });
      setDiff(null);
      if (user) {
        await loadHistory();
      }
    });
  }

  async function runOptimizeTask() {
    await withLoading(async () => {
      const created = await api.createOptimizeTask(prompt, selectedTemplate);
      let current = await api.task(created.task_id);
      setTask(current);
      for (let attempt = 0; attempt < 5 && ["queued", "running"].includes(current.status); attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 250));
        current = await api.task(created.task_id);
        setTask(current);
      }
      if (current.status === "succeeded") {
        applyOptimizeResult(await api.taskResult(created.task_id));
        await loadHistory();
      }
      if (current.status === "failed") {
        throw new Error(current.error ?? "后台任务失败");
      }
    });
  }

  function applyOptimizeResult(result: OptimizeResponse) {
    setAnalysis(result.analysis);
    setActiveVersion(result.version_id);
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
      setError(err instanceof Error ? err.message : "操作失败");
    } finally {
      setLoading(false);
    }
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
      <aside className="sidebar">
        <div className="brand">
          <Sparkles size={22} />
          <span>Prompt Optimizer</span>
        </div>
        <div className="workspace-rabbit">
          <img src="/rabbit-artwork.png" alt="PromptLayer 风格复古版画兔兔插画" width="643" height="684" loading="eager" decoding="async" />
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
          <Library size={16} />
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
              onClick={() => {
                setSelectedTemplate(template.id);
                setPrompt(template.template);
              }}
            >
              <strong>{template.name}</strong>
              <span>{template.description}</span>
            </button>
          ))}
        </div>
      </aside>

      <section className="workspace">
        <div className="toolbar">
          <button onClick={runAnalyze} disabled={loading}>分析</button>
          <button className="primary" onClick={runOptimize} disabled={loading}>{user ? "优化并保存" : "优化"}</button>
          <button onClick={() => void runStreamOptimize()} disabled={loading}>流式优化</button>
          <button onClick={() => void runOptimizeTask()} disabled={loading || !user}>后台优化</button>
          {["md", "json", "txt", "csv"].map((format) => (
            <button key={format} onClick={() => void runExport(format)} title={`导出 ${format}`} disabled={loading || !user || !activeVersion}>
              <Download size={15} />
              {format.toUpperCase()}
            </button>
          ))}
        </div>
        {error ? <div className="error">{error}</div> : null}
        <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} />
        {streamStatus ? (
          <section className="stream-panel">
            <strong>{streamStatus}</strong>
            {streamText ? <pre>{streamText}</pre> : null}
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
            <div className="score-head">
              <span>总分</span>
              <strong>{analysis.score.total_score}</strong>
            </div>
            {analysis.optimized_prompt ? (
              <>
                <h2>优化后提示词</h2>
                <pre>{analysis.optimized_prompt}</pre>
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

      <aside className="inspector">
        <div className="section-title">
          <History size={16} />
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
            <button key={item.id} onClick={() => void runDiff(item.id)}>
              <span>#{item.id} · {item.score}</span>
              <small>{item.original_preview}</small>
            </button>
          ))}
        </div>
        {!user ? <div className="guest-note">GUEST MODE / HISTORY IS NOT SAVED <a href="/login">LOGIN TO SAVE</a></div> : null}
        {diff ? (
          <section className="diff-panel">
            <div className="section-title">
              <GitCompare size={16} />
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

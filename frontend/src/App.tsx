import { Download, GitCompare, History, Library, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { api } from "./api";
import type { DiffResult, PromptAnalysis, PromptTemplate, VersionSummary } from "./types";

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

  const visibleTemplates = useMemo(() => templates, [templates]);

  useEffect(() => {
    void withLoading(async () => {
      await Promise.all([loadTemplates(category), loadHistory()]);
    });
  }, [category]);

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
      setAnalysis(result.analysis);
      setActiveVersion(result.version_id);
      setDiff(null);
      await loadHistory();
    });
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

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Sparkles size={22} />
          <span>Prompt Optimizer</span>
        </div>
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
          <button className="primary" onClick={runOptimize} disabled={loading}>优化并保存</button>
          {["md", "json", "txt", "csv"].map((format) => (
            <button key={format} onClick={() => void runExport(format)} title={`导出 ${format}`}>
              <Download size={15} />
              {format.toUpperCase()}
            </button>
          ))}
        </div>
        {error ? <div className="error">{error}</div> : null}
        <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} />
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
  );
}

import { ArrowLeftRight, Check, ChevronLeft, ChevronRight, Download, FileJson, Filter, Heart, Search, Upload, X } from "lucide-react";
import { useMemo, useState } from "react";
import { UiDialog } from "./components/UiStates";
import { AppLink } from "./navigation";

// RC ID: RC-116. Render prompt assets, history, search/filter, comparison, and safe import/export.

type Asset = { id: string; title: string; category: string; score: number; version: number; updatedAt: string; favorite: boolean; prompt: string };
type HistoryEntry = { id: string; assetId: string; version: number; label: string; score: number; prompt: string };

const initialAssets: Asset[] = [
  { id: "release-email", title: "Product release email", category: "business", score: 88, version: 3, updatedAt: "2026-07-18", favorite: true, prompt: "Write a concise product release email for a SaaS audience." },
  { id: "api-brief", title: "API design brief", category: "tech", score: 91, version: 2, updatedAt: "2026-07-17", favorite: false, prompt: "Turn these API requirements into a review-ready design brief." },
  { id: "research-plan", title: "User research plan", category: "education", score: 84, version: 1, updatedAt: "2026-07-14", favorite: false, prompt: "Create a practical user research plan with measurable outcomes." },
  { id: "launch-notes", title: "Launch notes", category: "creative", score: 79, version: 4, updatedAt: "2026-07-11", favorite: false, prompt: "Draft launch notes that are clear, specific, and useful to builders." },
];

const initialHistory: HistoryEntry[] = [
  { id: "release-v3", assetId: "release-email", version: 3, label: "Current release copy", score: 88, prompt: "Write a concise product release email for a SaaS audience." },
  { id: "release-v2", assetId: "release-email", version: 2, label: "Added audience context", score: 81, prompt: "Write a product release email for a SaaS audience." },
  { id: "api-v2", assetId: "api-brief", version: 2, label: "Added acceptance criteria", score: 91, prompt: "Turn these API requirements into a review-ready design brief." },
];

const PAGE_SIZE = 2;

export function PromptAssets() {
  const [assets, setAssets] = useState(initialAssets);
  const [history] = useState(initialHistory);
  const [view, setView] = useState<"templates" | "history">("templates");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [page, setPage] = useState(0);
  const [selectedId, setSelectedId] = useState(initialAssets[0].id);
  const [compareId, setCompareId] = useState<string | null>(null);
  const [importOpen, setImportOpen] = useState(false);
  const [importText, setImportText] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const selectedAsset = assets.find((asset) => asset.id === selectedId) ?? assets[0];
  const selectedHistory = history.find((entry) => entry.id === compareId);
  const filteredAssets = useMemo(() => assets.filter((asset) => {
    const matchesQuery = !query.trim() || `${asset.title} ${asset.prompt}`.toLowerCase().includes(query.trim().toLowerCase());
    return matchesQuery && (category === "all" || asset.category === category);
  }), [assets, category, query]);
  const visibleAssets = filteredAssets.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE);
  const pageCount = Math.max(1, Math.ceil(filteredAssets.length / PAGE_SIZE));
  const historyForAsset = history.filter((entry) => entry.assetId === selectedAsset.id);

  function changeView(next: "templates" | "history") {
    setView(next);
    setPage(0);
    setCompareId(null);
  }

  function toggleFavorite(assetId: string) {
    setAssets((current) => current.map((asset) => asset.id === assetId ? { ...asset, favorite: !asset.favorite } : asset));
    setNotice("FAVORITE UPDATED");
  }

  function exportAsset() {
    const payload = JSON.stringify(selectedAsset, null, 2);
    const blob = new Blob([payload], { type: "application/json" });
    if (typeof URL.createObjectURL === "function") {
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${selectedAsset.id}.json`;
      link.click();
      if (typeof URL.revokeObjectURL === "function") {
        URL.revokeObjectURL(url);
      }
    }
    setNotice("ASSET EXPORTED");
  }

  function importAsset() {
    try {
      const value = JSON.parse(importText) as Partial<Asset>;
      if (typeof value.title !== "string" || typeof value.prompt !== "string" || !value.title.trim() || !value.prompt.trim()) {
        throw new Error("invalid asset");
      }
      const id = `imported-${Date.now()}`;
      const asset: Asset = {
        id,
        title: value.title.trim(),
        prompt: value.prompt.trim(),
        category: typeof value.category === "string" ? value.category : "general",
        score: typeof value.score === "number" ? value.score : 0,
        version: 1,
        updatedAt: "just now",
        favorite: false,
      };
      setAssets((current) => [asset, ...current]);
      setSelectedId(id);
      setImportText("");
      setImportOpen(false);
      setNotice("ASSET IMPORTED");
    } catch {
      setNotice("IMPORT REJECTED / LIST UNCHANGED");
    }
  }

  return (
    <main className="prompt-assets-page">
      <header className="prompt-assets-header">
        <div><span className="eyebrow">PROMPT ASSETS / LIBRARY</span><h1>Keep the prompts worth reusing.</h1><p>Search, compare, and send a chosen prompt back to Composer without sending it.</p></div>
        <div className="prompt-assets-state"><FileJson size={16} aria-hidden="true" /> LOCAL ASSET INDEX</div>
      </header>

      <div className="prompt-assets-toolbar">
        <div className="prompt-assets-tabs" role="tablist" aria-label="Asset views"><button type="button" role="tab" aria-selected={view === "templates"} className={view === "templates" ? "active" : ""} onClick={() => changeView("templates")}>TEMPLATES</button><button type="button" role="tab" aria-selected={view === "history"} className={view === "history" ? "active" : ""} onClick={() => changeView("history")}>HISTORY</button></div>
        <label className="prompt-assets-search"><Search size={15} aria-hidden="true" /><input type="search" aria-label="Search prompt assets" value={query} onChange={(event) => { setQuery(event.target.value); setPage(0); }} placeholder="Search assets" /></label>
        <label className="prompt-assets-filter"><Filter size={15} aria-hidden="true" /><select aria-label="Asset category" value={category} onChange={(event) => { setCategory(event.target.value); setPage(0); }}><option value="all">ALL CATEGORIES</option><option value="tech">TECH</option><option value="business">BUSINESS</option><option value="creative">CREATIVE</option><option value="education">EDUCATION</option><option value="general">GENERAL</option></select></label>
        <button type="button" aria-label="Open import dialog" title="Open import dialog" onClick={() => setImportOpen(true)}><Upload size={15} aria-hidden="true" /> IMPORT</button>
        <button type="button" title="Export selected asset" onClick={exportAsset}><Download size={15} aria-hidden="true" /> EXPORT</button>
      </div>

      <div className="prompt-assets-shell">
        <aside className="prompt-assets-list" aria-label={view === "templates" ? "Prompt templates" : "Prompt history"}>
          <div className="prompt-assets-list-heading"><span className="eyebrow">{view === "templates" ? "ASSETS" : "VERSIONS"}</span><span>{view === "templates" ? filteredAssets.length : history.length}</span></div>
          {view === "templates" ? (
            <div className="prompt-assets-items">{visibleAssets.map((asset) => <button key={asset.id} type="button" className={asset.id === selectedAsset.id ? "active" : ""} onClick={() => setSelectedId(asset.id)}><span><strong>{asset.title}</strong><small>{asset.category} / v{asset.version}</small></span><b>{asset.score}</b></button>)}</div>
          ) : (
            <div className="prompt-assets-items">{history.map((entry) => <button key={entry.id} type="button" className={entry.id === compareId ? "active" : ""} onClick={() => { setSelectedId(entry.assetId); setCompareId(entry.id); }}><span><strong>{entry.label}</strong><small>{entry.assetId} / v{entry.version}</small></span><b>{entry.score}</b></button>)}</div>
          )}
          {view === "templates" ? <div className="prompt-assets-pagination"><button type="button" aria-label="Previous asset page" title="Previous asset page" disabled={page === 0} onClick={() => setPage((current) => Math.max(0, current - 1))}><ChevronLeft size={15} aria-hidden="true" /></button><span>{page + 1} / {pageCount}</span><button type="button" aria-label="Next asset page" title="Next asset page" disabled={page >= pageCount - 1} onClick={() => setPage((current) => Math.min(pageCount - 1, current + 1))}><ChevronRight size={15} aria-hidden="true" /></button></div> : null}
        </aside>

        <section className="prompt-asset-detail" aria-label="Selected prompt asset">
          <div className="prompt-asset-detail-heading"><div><span className="eyebrow">{selectedAsset.category.toUpperCase()} / VERSION {selectedAsset.version}</span><h2>{selectedAsset.title}</h2><p>Updated {selectedAsset.updatedAt}</p></div><button type="button" aria-label={selectedAsset.favorite ? "Remove favorite" : "Add favorite"} title={selectedAsset.favorite ? "Remove favorite" : "Add favorite"} onClick={() => toggleFavorite(selectedAsset.id)}><Heart size={18} fill={selectedAsset.favorite ? "currentColor" : "none"} aria-hidden="true" /></button></div>
          <div className="prompt-asset-score"><span>SCORE</span><strong>{selectedAsset.score}</strong><small>/ 100</small></div>
          <pre className="prompt-asset-prompt">{selectedAsset.prompt}</pre>
          <div className="prompt-asset-actions"><AppLink href={`/workspace?template=${selectedAsset.id}`} className="prompt-asset-use"><Check size={15} aria-hidden="true" /> USE IN COMPOSER</AppLink><button type="button" title="Export selected asset as JSON" onClick={exportAsset}><Download size={15} aria-hidden="true" /> EXPORT JSON</button></div>
          <div className="prompt-asset-history"><div className="prompt-assets-list-heading"><span className="eyebrow">VERSION HISTORY</span><span>{historyForAsset.length}</span></div>{historyForAsset.map((entry) => <div className="prompt-asset-history-row" key={entry.id}><span>v{entry.version} / {entry.label}</span><b>{entry.score}</b><button type="button" onClick={() => setCompareId(entry.id)}><ArrowLeftRight size={14} aria-hidden="true" /> COMPARE</button></div>)}</div>
          {selectedHistory ? <section className="prompt-asset-compare" aria-label="Version comparison"><div><span className="eyebrow">COMPARING VERSIONS</span><button type="button" aria-label="Close version comparison" title="Close comparison" onClick={() => setCompareId(null)}><X size={15} aria-hidden="true" /></button></div><div className="prompt-asset-compare-grid"><div><small>SELECTED / v{selectedAsset.version}</small><p>{selectedAsset.prompt}</p></div><div><small>HISTORY / v{selectedHistory.version}</small><p>{selectedHistory.prompt}</p></div></div></section> : null}
        </section>
      </div>

      <UiDialog
        open={importOpen}
        accessibleName="Import prompt asset"
        title="Bring in one reusable prompt."
        description="Invalid input is rejected without changing the library."
        onClose={() => setImportOpen(false)}
        onConfirm={importAsset}
        confirmLabel="IMPORT ASSET"
      >
        <form className="prompt-assets-import-form" onSubmit={(event) => { event.preventDefault(); importAsset(); }}>
          <textarea aria-label="Import JSON" value={importText} onChange={(event) => setImportText(event.target.value)} placeholder='{"title":"...","prompt":"..."}' />
        </form>
      </UiDialog>
      {notice ? <p className="prompt-assets-notice" role="status">{notice}</p> : null}
    </main>
  );
}

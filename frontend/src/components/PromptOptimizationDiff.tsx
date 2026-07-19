import { Clipboard, RotateCcw, Undo2, X } from "lucide-react";
import { useMemo, useRef, useState } from "react";

// RC ID: RC-140. Render editable prompt diffs without mounting every long-text row.

type DiffMode = "inline" | "side-by-side";
type DiffKind = "same" | "changed" | "removed" | "added";
type DiffRow = { index: number; left: string | null; right: string | null; kind: DiffKind };

type PromptOptimizationDiffProps = {
  original: string;
  optimized: string;
  onOptimizedChange: (value: string) => void;
  onReplaceSelected: (value: string) => void;
  onReplaceAll: () => void;
  onRetry: () => void;
  onClose?: () => void;
};

const ROW_HEIGHT = 28;
const VIEWPORT_HEIGHT = 260;
const OVERSCAN = 8;

export function PromptOptimizationDiff({ original, optimized, onOptimizedChange, onReplaceSelected, onReplaceAll, onRetry, onClose }: PromptOptimizationDiffProps) {
  const [mode, setMode] = useState<DiffMode>("inline");
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());
  const [undoStack, setUndoStack] = useState<string[]>([]);
  const [scrollTop, setScrollTop] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  const rows = useMemo(() => buildDiffRows(original, optimized), [original, optimized]);
  const start = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN);
  const end = Math.min(rows.length, Math.ceil((scrollTop + VIEWPORT_HEIGHT) / ROW_HEIGHT) + OVERSCAN);

  function updateOptimized(next: string) {
    setUndoStack((current) => [...current, optimized]);
    onOptimizedChange(next);
  }

  function undo() {
    const previous = undoStack[undoStack.length - 1];
    if (previous === undefined) {
      return;
    }
    setUndoStack((current) => current.slice(0, -1));
    onOptimizedChange(previous);
  }

  function replaceSelected() {
    if (selectedRows.size === 0) {
      return;
    }
    onReplaceSelected(buildSelectedText(original, optimized, selectedRows));
    setSelectedRows(new Set());
  }

  async function copyOptimized() {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(optimized);
    }
    setNotice("OPTIMIZED PROMPT COPIED");
  }

  return (
    <section className="prompt-diff" role="dialog" aria-modal="false" aria-label="Prompt optimization comparison">
      <div className="prompt-diff-toolbar">
        <div className="prompt-diff-modes" role="group" aria-label="Diff view mode">
          <button type="button" aria-pressed={mode === "inline"} className={mode === "inline" ? "active" : ""} onClick={() => setMode("inline")}>INLINE</button>
          <button type="button" aria-pressed={mode === "side-by-side"} className={mode === "side-by-side" ? "active" : ""} onClick={() => setMode("side-by-side")}>SIDE BY SIDE</button>
        </div>
        <span className="prompt-diff-count">{rows.filter((row) => row.kind !== "same").length} CHANGED LINES</span>
        {onClose ? <button type="button" className="icon-button" aria-label="关闭优化结果" title="关闭优化结果" onClick={onClose}><X size={15} aria-hidden="true" /></button> : null}
      </div>
      <div
        ref={viewportRef}
        className={`prompt-diff-viewport prompt-diff-${mode}`}
        style={{ height: VIEWPORT_HEIGHT }}
        onScroll={(event) => setScrollTop(event.currentTarget.scrollTop)}
        role="region"
        aria-label="Prompt diff lines"
      >
        <div style={{ height: rows.length * ROW_HEIGHT, position: "relative" }}>
          <div className="prompt-diff-window" style={{ transform: `translateY(${start * ROW_HEIGHT}px)` }}>
            {rows.slice(start, end).map((row) => (
              <button
                type="button"
                className={`prompt-diff-row prompt-diff-row-${row.kind}${selectedRows.has(row.index) ? " selected" : ""}`}
                key={row.index}
                aria-pressed={selectedRows.has(row.index)}
                aria-label={`Diff line ${row.index + 1}`}
                onClick={() => setSelectedRows((current) => {
                  const next = new Set(current);
                  if (next.has(row.index)) next.delete(row.index); else next.add(row.index);
                  return next;
                })}
              >
                <span>{row.left ?? ""}</span>
                <span>{row.right ?? ""}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
      <textarea className="prompt-diff-editor" aria-label="Optimized prompt preview" value={optimized} onChange={(event) => updateOptimized(event.target.value)} />
      <div className="prompt-diff-actions">
        <button type="button" onClick={() => void copyOptimized()}><Clipboard size={14} aria-hidden="true" /> COPY OPTIMIZED</button>
        <button type="button" onClick={replaceSelected} disabled={selectedRows.size === 0}>REPLACE SELECTED</button>
        <button type="button" onClick={onReplaceAll}>REPLACE ALL</button>
        <button type="button" onClick={undo} disabled={undoStack.length === 0}><Undo2 size={14} aria-hidden="true" /> UNDO</button>
        <button type="button" onClick={() => updateOptimized(original)}><RotateCcw size={14} aria-hidden="true" /> RESTORE ORIGINAL</button>
        <button type="button" onClick={onRetry}>RETRY</button>
      </div>
      {notice ? <p className="prompt-diff-notice" role="status">{notice}</p> : null}
    </section>
  );
}

function buildDiffRows(original: string, optimized: string): DiffRow[] {
  const left = original.split("\n");
  const right = optimized.split("\n");
  const length = Math.max(left.length, right.length);
  return Array.from({ length }, (_, index) => {
    const leftLine = left[index] ?? null;
    const rightLine = right[index] ?? null;
    const kind: DiffKind = leftLine === rightLine
      ? "same"
      : leftLine === null
        ? "added"
        : rightLine === null
          ? "removed"
          : "changed";
    return { index, left: leftLine, right: rightLine, kind };
  });
}

function buildSelectedText(original: string, optimized: string, selectedRows: Set<number>): string {
  const left = original.split("\n");
  const right = optimized.split("\n");
  const length = Math.max(left.length, right.length);
  return Array.from({ length }, (_, index) => selectedRows.has(index) ? right[index] : left[index])
    .filter((line): line is string => line !== undefined)
    .join("\n");
}

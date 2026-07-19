import { AlertTriangle, Check, ChevronRight, File, GitBranch, RotateCcw, ShieldCheck, X } from "lucide-react";
import { useState } from "react";

// RC ID: RC-112. Render checkpoint changes with hunk controls and drift protection.

type HunkStatus = "pending" | "accepted" | "rejected";
type Hunk = { id: string; title: string; lines: string[]; status: HunkStatus };
type ChangedFile = { path: string; kind: "modified" | "added"; hunks: Hunk[] };

const initialFiles: ChangedFile[] = [
  {
    path: "backend/rabbit_code/agent.py",
    kind: "modified",
    hunks: [{ id: "agent-1", title: "Add cancellation state", lines: ["+    if cancel_event.is_set():", "+        return AgentEvent.cancelled()"], status: "pending" }],
  },
  {
    path: "backend/tests/test_agent.py",
    kind: "added",
    hunks: [{ id: "test-1", title: "Cover cancellation", lines: ["+def test_cancel_stops_agent():", "+    assert result.cancelled"], status: "pending" }],
  },
];

export function ChangeReview() {
  const [files, setFiles] = useState(initialFiles);
  const [selectedPath, setSelectedPath] = useState(initialFiles[0].path);
  const [showOriginal, setShowOriginal] = useState(false);
  const [testsPassed, setTestsPassed] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const driftDetected = localStorage.getItem("rabbit_code_workspace_drift") === "true";
  const selectedFile = files.find((file) => file.path === selectedPath) ?? files[0];

  function updateHunk(status: HunkStatus) {
    if (driftDetected) {
      setNotice("Resolve workspace drift before applying changes.");
      return;
    }
    setFiles((current) => current.map((file) => (
      file.path === selectedFile.path
        ? { ...file, hunks: file.hunks.map((hunk) => ({ ...hunk, status })) }
        : file
    )));
    setNotice(null);
  }

  function rollback() {
    setFiles((current) => current.map((file) => ({
      ...file,
      hunks: file.hunks.map((hunk) => ({ ...hunk, status: "pending" })),
    })));
    setNotice("ROLLBACK READY");
  }

  return (
    <main className="change-review-page">
      <header className="change-review-header">
        <div>
          <span className="eyebrow">CHANGE REVIEW / CHECKPOINT</span>
          <h1>Review the proposed changes.</h1>
          <p>Inspect each file and hunk before anything reaches the workspace.</p>
        </div>
        <div className={`change-review-drift ${driftDetected ? "is-drifted" : ""}`}>
          {driftDetected ? <AlertTriangle size={16} aria-hidden="true" /> : <ShieldCheck size={16} aria-hidden="true" />}
          {driftDetected ? "WORKSPACE DRIFT DETECTED" : "BASELINE MATCHES"}
        </div>
      </header>

      <div className="change-review-shell">
        <aside className="change-file-tree" aria-label="Changed files">
          <div className="change-panel-heading"><span className="eyebrow">FILES</span><span>{files.length}</span></div>
          <div className="change-file-list">
            {files.map((file) => (
              <button
                key={file.path}
                type="button"
                className={selectedPath === file.path ? "active" : ""}
                onClick={() => setSelectedPath(file.path)}
              >
                <File size={15} aria-hidden="true" />
                <span>{file.path}</span>
                <ChevronRight size={14} aria-hidden="true" />
              </button>
            ))}
          </div>
          <div className="change-file-footer"><GitBranch size={14} aria-hidden="true" /> checkpoint / agent-run</div>
        </aside>

        <section className="change-diff-pane" aria-label="Diff review" role="region">
          <div className="change-diff-heading">
            <div><span className="eyebrow">{selectedFile.kind}</span><h2>{selectedFile.path}</h2></div>
            <button type="button" onClick={() => setShowOriginal((shown) => !shown)}>
              {showOriginal ? "SHOW DIFF" : "VIEW ORIGINAL"}
            </button>
          </div>
          {selectedFile.hunks.map((hunk) => (
            <section className="change-hunk" key={hunk.id}>
              <div className="change-hunk-heading">
                <span>{hunk.title}</span>
                <strong className={`hunk-status-${hunk.status}`}>{hunk.status.toUpperCase()}</strong>
              </div>
              <pre className={showOriginal ? "original-view" : ""}>{showOriginal ? "# Original file content is loaded from the checkpoint baseline." : hunk.lines.join("\n")}</pre>
              <div className="change-hunk-actions">
                <button type="button" onClick={() => updateHunk("accepted")} disabled={hunk.status === "accepted"}>
                  <Check size={15} aria-hidden="true" /> ACCEPT HUNK
                </button>
                <button type="button" onClick={() => updateHunk("rejected")} disabled={hunk.status === "rejected"}>
                  <X size={15} aria-hidden="true" /> REJECT HUNK
                </button>
              </div>
            </section>
          ))}
          {notice ? <p className="change-review-notice" role="status">{notice}</p> : null}
        </section>

        <aside className="change-review-sidebar" aria-label="Review actions">
          <div className="change-panel-heading"><span className="eyebrow">VALIDATION</span><ShieldCheck size={16} aria-hidden="true" /></div>
          <div className={`change-test-status ${testsPassed ? "passed" : ""}`}>
            <span>TEST STATUS</span>
            <strong>{testsPassed ? "TESTS PASSED" : "TESTS NOT RUN"}</strong>
          </div>
          <button className="change-run-tests" type="button" onClick={() => setTestsPassed(true)}>
            <ShieldCheck size={15} aria-hidden="true" /> RUN VERIFICATION
          </button>
          <button className="change-rollback" type="button" onClick={rollback}>
            <RotateCcw size={15} aria-hidden="true" /> ROLLBACK AGENT CHANGES
          </button>
          <p className="change-review-help">Accept or reject each hunk. A changed baseline blocks application until it is reviewed again.</p>
        </aside>
      </div>
    </main>
  );
}

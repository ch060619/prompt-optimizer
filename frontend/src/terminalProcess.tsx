import { Check, CircleCheck, CircleStop, Maximize2, Plus, RotateCcw, SquareTerminal, X } from "lucide-react";
import { useState, type FormEvent } from "react";
import { PermissionDialog } from "./components/UiStates";

// RC ID: RC-113. Render terminal tabs, process controls, resize state, and close cleanup.

type TerminalStatus = "ready" | "running" | "exited";
type ProcessStatus = "running" | "exited" | "stopped";
type TerminalSize = { columns: number; rows: number };
type Terminal = {
  id: string;
  name: string;
  cwd: string;
  status: TerminalStatus;
  size: TerminalSize;
  output: string[];
};
type BackgroundProcess = { id: string; command: string; pid: number; status: ProcessStatus };

const initialTerminals: Terminal[] = [
  {
    id: "terminal-1",
    name: "TERMINAL 01",
    cwd: "~/prompt-optimizer",
    status: "ready",
    size: { columns: 120, rows: 32 },
    output: ["$ rabbit status", "workspace: ready", "pty: service boundary"],
  },
  {
    id: "terminal-2",
    name: "TERMINAL 02",
    cwd: "~/prompt-optimizer",
    status: "exited",
    size: { columns: 100, rows: 28 },
    output: ["$ npm --prefix frontend run build", "process exited with code 0"],
  },
];

const initialProcesses: BackgroundProcess[] = [
  { id: "proc-1", command: "python -m pytest backend/tests/test_rc094_process_tools.py", pid: 4128, status: "running" },
  { id: "proc-2", command: "npm --prefix frontend run build", pid: 4130, status: "exited" },
];

export function TerminalProcessPanel() {
  const [terminals, setTerminals] = useState(initialTerminals);
  const [activeId, setActiveId] = useState(initialTerminals[0].id);
  const [processes, setProcesses] = useState(initialProcesses);
  const [command, setCommand] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const [closeConfirm, setCloseConfirm] = useState(false);
  const [closed, setClosed] = useState(false);
  const activeTerminal = terminals.find((terminal) => terminal.id === activeId) ?? terminals[0];

  function addTerminal() {
    const nextNumber = terminals.length + 1;
    const terminal: Terminal = {
      id: `terminal-${nextNumber}`,
      name: `TERMINAL ${String(nextNumber).padStart(2, "0")}`,
      cwd: "~/prompt-optimizer",
      status: "ready",
      size: { columns: 120, rows: 32 },
      output: ["$", "new terminal ready"],
    };
    setTerminals((current) => [...current, terminal]);
    setActiveId(terminal.id);
    setNotice("NEW TERMINAL READY");
  }

  function submitCommand(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = command.trim();
    if (!value || closed) {
      return;
    }
    setTerminals((current) => current.map((terminal) => (
      terminal.id === activeTerminal.id
        ? { ...terminal, status: "running", output: [...terminal.output, `$ ${value}`, "command queued"] }
        : terminal
    )));
    setCommand("");
    setNotice("COMMAND SENT");
  }

  function stopTerminal() {
    setTerminals((current) => current.map((terminal) => (
      terminal.id === activeTerminal.id
        ? { ...terminal, status: "exited", output: [...terminal.output, "process stopped"] }
        : terminal
    )));
    setNotice("TERMINAL PROCESS STOPPED");
  }

  function restartTerminal() {
    setTerminals((current) => current.map((terminal) => (
      terminal.id === activeTerminal.id
        ? { ...terminal, status: "ready", output: [...terminal.output, "terminal recovered"] }
        : terminal
    )));
    setNotice("TERMINAL RECOVERED");
  }

  function updateSize(key: keyof TerminalSize, value: string) {
    const nextValue = Number(value);
    if (!Number.isInteger(nextValue) || nextValue < 20) {
      return;
    }
    setTerminals((current) => current.map((terminal) => (
      terminal.id === activeTerminal.id
        ? { ...terminal, size: { ...terminal.size, [key]: nextValue } }
        : terminal
    )));
  }

  function syncSize() {
    setTerminals((current) => current.map((terminal) => (
      terminal.id === activeTerminal.id
        ? { ...terminal, output: [...terminal.output, `[size synchronized: ${terminal.size.columns}x${terminal.size.rows}]`] }
        : terminal
    )));
    setNotice("TERMINAL SIZE SYNCHRONIZED");
  }

  function updateProcess(processId: string, status: ProcessStatus) {
    setProcesses((current) => current.map((process) => process.id === processId ? { ...process, status } : process));
    setNotice(status === "stopped" ? "BACKGROUND PROCESS STOPPED" : "BACKGROUND PROCESS RESTARTED");
  }

  function confirmClose() {
    setProcesses((current) => current.map((process) => process.status === "running" ? { ...process, status: "stopped" } : process));
    setTerminals((current) => current.map((terminal) => ({ ...terminal, status: "exited" })));
    setCloseConfirm(false);
    setClosed(true);
    setNotice("TERMINAL CLOSED / NO RUNNING PROCESS REMAINS");
  }

  return (
    <main className="terminal-process-page">
      <header className="terminal-process-header">
        <div>
          <span className="eyebrow">TERMINAL / PROCESS CONTROL</span>
          <h1>Shells that stay inside the workspace.</h1>
          <p>Switch terminals, follow background work, and close the workspace cleanly.</p>
        </div>
        <div className="terminal-process-state">
          {closed ? <Check size={16} aria-hidden="true" /> : <CircleCheck size={16} aria-hidden="true" />}
          {closed ? "CLOSED CLEANLY" : "WORKSPACE BOUND"}
        </div>
      </header>

      <div className="terminal-process-shell">
        <aside className="terminal-tabs-panel" aria-label="Terminal tabs">
          <div className="terminal-panel-heading"><span className="eyebrow">TERMINALS</span><button type="button" aria-label="Add terminal" title="Add terminal" onClick={addTerminal}><Plus size={16} aria-hidden="true" /></button></div>
          <div className="terminal-tab-list" role="tablist" aria-label="Workspace terminals">
            {terminals.map((terminal) => (
              <button
                key={terminal.id}
                type="button"
                role="tab"
                aria-selected={activeTerminal.id === terminal.id}
                className={activeTerminal.id === terminal.id ? "active" : ""}
                onClick={() => setActiveId(terminal.id)}
              >
                <SquareTerminal size={15} aria-hidden="true" />
                <span>{terminal.name}</span>
                <small>{terminal.status.toUpperCase()}</small>
              </button>
            ))}
          </div>
          <div className="terminal-tabs-footer"><SquareTerminal size={14} aria-hidden="true" /> {terminals.length} SESSIONS</div>
        </aside>

        <section className="terminal-console" aria-label="Active terminal" role="region">
          <div className="terminal-console-header">
            <div><span className="eyebrow">{activeTerminal.name}</span><strong>{activeTerminal.cwd}</strong></div>
            <span className={`terminal-status terminal-status-${activeTerminal.status}`}>{activeTerminal.status.toUpperCase()}</span>
          </div>
          <div className="terminal-console-toolbar">
            <label>COLS <input aria-label="Terminal columns" type="number" min="20" value={activeTerminal.size.columns} onChange={(event) => updateSize("columns", event.target.value)} /></label>
            <label>ROWS <input aria-label="Terminal rows" type="number" min="10" value={activeTerminal.size.rows} onChange={(event) => updateSize("rows", event.target.value)} /></label>
            <button type="button" title="Synchronize terminal size" onClick={syncSize}><Maximize2 size={14} aria-hidden="true" /> SYNC SIZE</button>
          </div>
          <pre className="terminal-output" aria-label="Terminal output" role="log">{activeTerminal.output.join("\n")}</pre>
          <form className="terminal-command-form" onSubmit={submitCommand}>
            <span aria-hidden="true">$</span>
            <input aria-label="Terminal command" placeholder="Type a command" value={command} onChange={(event) => setCommand(event.target.value)} disabled={closed} />
            <button type="submit" aria-label="Send terminal command" title="Send terminal command" disabled={closed}><SquareTerminal size={15} aria-hidden="true" /></button>
          </form>
          <div className="terminal-console-actions">
            {activeTerminal.status === "running" ? (
              <button type="button" onClick={stopTerminal}><CircleStop size={15} aria-hidden="true" /> STOP COMMAND</button>
            ) : (
              <button type="button" onClick={restartTerminal}><RotateCcw size={15} aria-hidden="true" /> RESTART TERMINAL</button>
            )}
            <button type="button" onClick={() => setCloseConfirm(true)} disabled={closed}><X size={15} aria-hidden="true" /> CLOSE WORKSPACE</button>
          </div>
          <PermissionDialog
            open={closeConfirm}
            accessibleName="Close workspace confirmation"
            title="Stop active commands and close this workspace?"
            description="Running background tasks will be marked stopped before the terminal exits."
            onClose={() => setCloseConfirm(false)}
            onConfirm={confirmClose}
            confirmLabel="CONFIRM CLOSE"
          />
          {notice ? <p className="terminal-notice" role="status">{notice}</p> : null}
        </section>

        <aside className="terminal-process-list" aria-label="Background processes">
          <div className="terminal-panel-heading"><span className="eyebrow">BACKGROUND</span><span>{processes.length}</span></div>
          <div className="terminal-process-items">
            {processes.map((process) => (
              <article key={process.id} className="terminal-process-item">
                <div className="terminal-process-item-heading"><span>{process.id}</span><strong className={`process-status-${process.status}`}>{process.status.toUpperCase()}</strong></div>
                <code>{process.command}</code>
                <small>PID {process.pid}</small>
                <button type="button" onClick={() => updateProcess(process.id, process.status === "running" ? "stopped" : "running")}>
                  {process.status === "running" ? <><CircleStop size={14} aria-hidden="true" /> STOP PROCESS</> : <><RotateCcw size={14} aria-hidden="true" /> RESTART PROCESS</>}
                </button>
              </article>
            ))}
          </div>
          <p className="terminal-process-help">Processes inherit the selected workspace boundary and remain visible after exit.</p>
        </aside>
      </div>
    </main>
  );
}

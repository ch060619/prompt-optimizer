import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  FileDiff,
  Folder,
  GitBranch,
  Menu,
  PanelRightClose,
  PanelRightOpen,
  Plus,
  Send,
  SquareTerminal,
} from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { notifyWorkspace, readWindowPreferences, updateWindowPreferences, type WindowPanel } from "./windowPreferences";

// RC ID: RC-111. Render the task conversation, session rail, inspector, and terminal drawer.

type Message = { id: number; role: "user" | "agent"; text: string };
type InspectorPanel = WindowPanel;

const initialMessages: Message[] = [
  { id: 1, role: "agent", text: "Ready to work in this shared workspace." },
];

export function TaskWorkspace() {
  const [draft, setDraft] = useState(() => localStorage.getItem("rabbit_code_task_draft") || "");
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [activePanel, setActivePanel] = useState<InspectorPanel>(() => readWindowPreferences().activePanel);
  const [inspectorOpen, setInspectorOpen] = useState(() => readWindowPreferences().inspectorOpen);
  const [terminalOpen, setTerminalOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState(() => localStorage.getItem("rabbit_code_task_session") || "session-1");

  useEffect(() => {
    localStorage.setItem("rabbit_code_task_draft", draft);
  }, [draft]);

  useEffect(() => {
    localStorage.setItem("rabbit_code_task_session", sessionId);
  }, [sessionId]);

  useEffect(() => {
    updateWindowPreferences({ activePanel, inspectorOpen });
  }, [activePanel, inspectorOpen]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = draft.trim();
    if (!value) {
      return;
    }
    setMessages((current) => [
      ...current,
      { id: Date.now(), role: "user", text: value },
      { id: Date.now() + 1, role: "agent", text: "Task received. The shared agent is ready for the next step." },
    ]);
    setDraft("");
    localStorage.removeItem("rabbit_code_task_draft");
  }

  function newSession() {
    const nextSession = `session-${Date.now()}`;
    setSessionId(nextSession);
    setMessages(initialMessages);
    setNotice("NEW SESSION READY");
    notifyWorkspace("Rabbit Code", "A new workspace session is ready.");
  }

  return (
    <main className="task-workspace-page">
      <div className="task-workspace-shell">
        <aside className="task-session-rail" aria-label="Workspace sessions">
          <div className="task-rail-heading">
            <span className="eyebrow">WORKSPACE</span>
            <button type="button" aria-label="Collapse workspace rail" title="Collapse workspace rail">
              <ChevronLeft size={16} aria-hidden="true" />
            </button>
          </div>
          <a className="task-project-link" href="/workspace/home">
            <Folder size={16} aria-hidden="true" />
            <span>Recent projects</span>
            <ChevronRight size={14} aria-hidden="true" />
          </a>
          <div className="task-session-heading">
            <span>SESSIONS</span>
            <button type="button" aria-label="Add session" title="Add session" onClick={newSession}>
              <Plus size={15} aria-hidden="true" />
            </button>
          </div>
          <button className="task-session-item active" type="button">
            <span>{sessionId}</span>
            <small>ACTIVE</small>
          </button>
          <button className="task-new-session" type="button" onClick={newSession}>
            <Plus size={15} aria-hidden="true" /> NEW SESSION
          </button>
          <div className="task-rail-footer">
            <GitBranch size={14} aria-hidden="true" /> main
          </div>
        </aside>

          <section className="task-conversation" aria-label="Task conversation">
          <div className="task-conversation-header">
            <div>
              <span className="eyebrow">TASK / {sessionId}</span>
              <h1 id="task-conversation-title">What should we work on?</h1>
            </div>
            <button className="task-header-menu" type="button" aria-label="Task menu" title="Task menu">
              <Menu size={18} aria-hidden="true" />
            </button>
          </div>
          <div className="task-message-list" aria-live="polite">
            {messages.map((message) => (
              <article className={`task-message task-message-${message.role}`} key={message.id}>
                <span className="task-message-label">{message.role === "user" ? "YOU" : "RABBIT CODE"}</span>
                <p>{message.text}</p>
              </article>
            ))}
            {notice ? <p className="task-notice" role="status">{notice}</p> : null}
          </div>
          <form className="task-composer" onSubmit={submit}>
            <textarea
              aria-label="Task composer"
              placeholder="Describe the task, ask a question, or point to a file..."
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              rows={4}
            />
            <div className="task-composer-footer">
              <span>PLAN MODE / LOCAL CONTEXT</span>
              <button className="task-send" type="submit" data-action="send-task" aria-label="Send task" title="Send task">
                <Send size={16} aria-hidden="true" /> SEND TASK
              </button>
            </div>
          </form>
          <button className="task-terminal-toggle" type="button" title={terminalOpen ? "Close terminal" : "Open terminal"} onClick={() => setTerminalOpen((open) => !open)}>
            <SquareTerminal size={15} aria-hidden="true" /> {terminalOpen ? "CLOSE TERMINAL" : "OPEN TERMINAL"}
          </button>
          {terminalOpen ? (
            <section className="task-terminal-drawer" aria-label="Terminal drawer" role="region">
              <div className="task-terminal-heading"><span>TERMINAL / WORKSPACE</span><span>READY</span></div>
              <pre>$ rabbit status{"\n"}workspace: ready{"\n"}session: {sessionId}</pre>
            </section>
          ) : null}
        </section>

        {inspectorOpen ? (
          <aside className="task-inspector" aria-label="Task inspector">
            <div className="task-inspector-heading">
              <span className="eyebrow">INSPECTOR</span>
              <button type="button" aria-label="Collapse inspector" title="Collapse inspector" onClick={() => setInspectorOpen(false)}>
                <PanelRightClose size={16} aria-hidden="true" />
              </button>
            </div>
            <div className="task-inspector-tabs" role="tablist" aria-label="Task inspector panels">
              {(["plan", "diff", "context"] as const).map((panel) => (
                <button
                  key={panel}
                  type="button"
                  role="tab"
                  id={`task-inspector-tab-${panel}`}
                  aria-selected={activePanel === panel}
                  aria-controls={`task-inspector-panel-${panel}`}
                  className={activePanel === panel ? "active" : ""}
                  onClick={() => setActivePanel(panel)}
                >
                  {panel === "diff" ? <FileDiff size={14} aria-hidden="true" /> : null}
                  {panel.toUpperCase()}
                </button>
              ))}
            </div>
            <InspectorContent panel={activePanel} />
          </aside>
        ) : (
          <button className="task-inspector-open" type="button" aria-label="Open inspector" title="Open inspector" onClick={() => setInspectorOpen(true)}>
            <PanelRightOpen size={17} aria-hidden="true" />
          </button>
        )}
      </div>
    </main>
  );
}

function InspectorContent({ panel }: { panel: InspectorPanel }) {
  const [planOpen, setPlanOpen] = useState(true);
  const panelId = `task-inspector-panel-${panel}`;
  if (panel === "diff") {
    return <div className="task-inspector-content" role="tabpanel" id={panelId} aria-labelledby={`task-inspector-tab-${panel}`} tabIndex={0}><span className="eyebrow">DIFF</span><p>No file changes in this task yet.</p></div>;
  }
  if (panel === "context") {
    return <div className="task-inspector-content" role="tabpanel" id={panelId} aria-labelledby={`task-inspector-tab-${panel}`} tabIndex={0}><span className="eyebrow">CONTEXT</span><p>Workspace files and instructions will appear here.</p></div>;
  }
  return (
    <div className="task-inspector-content" role="tabpanel" id={panelId} aria-labelledby={`task-inspector-tab-${panel}`} tabIndex={0}>
      <span className="eyebrow">PLAN</span>
      <ol id="task-plan-list" hidden={!planOpen}><li>Understand the request</li><li>Inspect the workspace</li><li>Run focused verification</li></ol>
      <button type="button" className="task-plan-collapse" aria-expanded={planOpen} aria-controls="task-plan-list" onClick={() => setPlanOpen((open) => !open)}><ChevronDown size={14} aria-hidden="true" /> PLAN MODE</button>
    </div>
  );
}

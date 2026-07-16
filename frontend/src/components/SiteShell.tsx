import { ArrowUpRight, Menu, X } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

const productLinks = [
  ["Prompt workspace", "/"],
  ["Evaluations", "/evaluations"],
  ["Templates", "/prompt-management"],
  ["History & diff", "/models"],
  ["Background tasks", "/workflows"]
] as const;

const companyLinks = [
  ["Documentation", "/blog"],
  ["About this project", "/case-studies"],
  ["Contact", "/contact"]
] as const;

export function SiteShell({ children }: { children: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    document.body.classList.toggle("menu-open", menuOpen);
    return () => document.body.classList.remove("menu-open");
  }, [menuOpen]);

  return (
    <div className="site-frame">
      <ActivityBar />
      <SiteHeader menuOpen={menuOpen} onMenuToggle={() => setMenuOpen((open) => !open)} />
      <div className="site-content">{children}</div>
      <SiteFooter />
      {menuOpen ? <SiteMenu onClose={() => setMenuOpen(false)} /> : null}
    </div>
  );
}

function ActivityBar() {
  return (
    <div className="activity-bar" role="status">
      <span className="activity-mark" aria-hidden="true">+</span>
      <span>OFFLINE-FIRST PROMPT WORKSPACE</span>
      <span className="activity-separator" aria-hidden="true">·</span>
      <a href="/blog">READ THE BUILD NOTES <ArrowUpRight size={13} aria-hidden="true" /></a>
    </div>
  );
}

function SiteHeader({ menuOpen, onMenuToggle }: { menuOpen: boolean; onMenuToggle: () => void }) {
  return (
    <header className="site-header">
      <div className="site-menu-cell">
        <button
          className="menu-trigger"
          type="button"
          aria-expanded={menuOpen}
          aria-controls="site-navigation"
          aria-label={menuOpen ? "Close navigation" : "Open navigation"}
          onClick={onMenuToggle}
        >
          {menuOpen ? <X size={23} strokeWidth={1.5} /> : <Menu size={23} strokeWidth={1.5} />}
        </button>
      </div>
      <a className="site-logo" href="/" aria-label="Prompt Optimizer home">
        Prompt Optimizer
      </a>
      <nav className="site-nav" aria-label="Primary navigation">
        <a href="/prompt-management">WORKSPACE</a>
        <a href="/evaluations">EVALUATIONS</a>
        <a href="/blog">BUILD NOTES</a>
        <a href="/contact">CONTACT</a>
      </nav>
      <a className="header-action" href="/" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
        OPEN WORKSPACE <ArrowUpRight size={14} aria-hidden="true" />
      </a>
    </header>
  );
}

function SiteMenu({ onClose }: { onClose: () => void }) {
  return (
    <aside id="site-navigation" className="site-menu" aria-label="Full-screen navigation">
      <div className="site-menu-inner">
        <div className="site-menu-group">
          <span className="eyebrow">PRODUCTS</span>
          {productLinks.map(([label, href]) => (
            <a key={href} className="menu-link" href={href} onClick={onClose}>
              <span>{label}</span>
              <ArrowUpRight size={18} aria-hidden="true" />
            </a>
          ))}
        </div>
        <div className="site-menu-group">
          <span className="eyebrow">PROJECT</span>
          {companyLinks.map(([label, href]) => (
            <a key={href} className="menu-link" href={href} onClick={onClose}>
              <span>{label}</span>
              <ArrowUpRight size={18} aria-hidden="true" />
            </a>
          ))}
          <button className="menu-close-link" type="button" onClick={onClose}>
            CLOSE MENU <X size={16} aria-hidden="true" />
          </button>
        </div>
      </div>
      <div className="site-menu-footer">
        <ServiceStatus />
        <span>LOCAL BY DEFAULT / MIT LICENSE</span>
      </div>
    </aside>
  );
}

function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-topline">
        <span className="eyebrow">PROMPT OPTIMIZER / V3.0</span>
        <ServiceStatus />
      </div>
      <div className="footer-brandline">
        <p>Build better prompts. Keep the work close.</p>
        <a href="/" className="footer-mark">Prompt Optimizer</a>
      </div>
      <div className="footer-links">
        <div>
          <span className="eyebrow">PRODUCTS</span>
          <a href="/prompt-management">Workspace</a>
          <a href="/evaluations">Evaluations</a>
          <a href="/workflows">Tasks & exports</a>
        </div>
        <div>
          <span className="eyebrow">PROJECT</span>
          <a href="/blog">Build notes</a>
          <a href="/case-studies">Use cases</a>
          <a href="/contact">Contact</a>
        </div>
        <div>
          <span className="eyebrow">LEGAL</span>
          <a href="/privacy">Privacy</a>
          <a href="/terms">Terms</a>
          <a href="/cookies">Cookies</a>
        </div>
      </div>
      <div className="footer-bottomline">
        <span>LOCAL DATA / NO REMOTE MODEL REQUIRED</span>
        <span>© 2026 PROMPT OPTIMIZER CONTRIBUTORS</span>
      </div>
    </footer>
  );
}

function ServiceStatus() {
  return (
    <span className="service-status">
      <i aria-hidden="true" />
      LOCAL SERVICES OPERATIONAL
    </span>
  );
}

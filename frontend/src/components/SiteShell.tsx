import { ArrowUpRight, Menu, X } from "lucide-react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { useEffect, useRef, useState, type ReactNode, type RefObject } from "react";

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
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLElement>(null);
  const frameRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.body.classList.toggle("menu-open", menuOpen);
    return () => document.body.classList.remove("menu-open");
  }, [menuOpen]);

  useEffect(() => {
    if (!menuOpen) {
      return;
    }
    const menuButton = menuButtonRef.current;
    const focusFrame = window.requestAnimationFrame(() => menuRef.current?.focus());
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    }
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      window.cancelAnimationFrame(focusFrame);
      document.removeEventListener("keydown", closeOnEscape);
      menuButton?.focus();
    };
  }, [menuOpen]);

  useEffect(() => {
    if (typeof window.matchMedia !== "function" || typeof window.requestAnimationFrame !== "function") {
      return;
    }
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reducedMotion) {
      return;
    }

    const previousScrollRestoration = window.history.scrollRestoration;
    window.history.scrollRestoration = "manual";
    window.scrollTo(0, 0);
    gsap.registerPlugin(ScrollTrigger);
    const lenis = new Lenis({ autoRaf: false, lerp: 0.08 });
    let frame = 0;
    const raf = (time: number) => {
      lenis.raf(time);
      frame = window.requestAnimationFrame(raf);
    };
    frame = window.requestAnimationFrame(raf);
    const context = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>(".reveal-on-scroll").forEach((element) => {
        gsap.fromTo(element, { autoAlpha: 0, y: 28 }, {
          autoAlpha: 1,
          duration: 0.7,
          ease: "power2.out",
          scrollTrigger: { once: true, start: "top 86%", trigger: element },
          y: 0
        });
      });
    }, frameRef);
    ScrollTrigger.refresh();

    return () => {
      window.cancelAnimationFrame(frame);
      context.revert();
      lenis.destroy();
      window.history.scrollRestoration = previousScrollRestoration;
    };
  }, []);

  return (
    <div className="site-frame" ref={frameRef}>
      <ActivityBar />
      <SiteHeader menuOpen={menuOpen} menuButtonRef={menuButtonRef} onMenuToggle={() => setMenuOpen((open) => !open)} />
      <div className="site-content">{children}</div>
      <SiteFooter />
      {menuOpen ? <SiteMenu menuRef={menuRef} onClose={() => setMenuOpen(false)} /> : null}
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

function SiteHeader({ menuOpen, menuButtonRef, onMenuToggle }: { menuOpen: boolean; menuButtonRef: RefObject<HTMLButtonElement>; onMenuToggle: () => void }) {
  return (
    <header className="site-header">
      <div className="site-menu-cell">
        <button
          className="menu-trigger"
          ref={menuButtonRef}
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

function SiteMenu({ menuRef, onClose }: { menuRef: RefObject<HTMLElement>; onClose: () => void }) {
  return (
    <aside id="site-navigation" ref={menuRef} className="site-menu" role="dialog" aria-modal="true" aria-label="Full-screen navigation" tabIndex={-1}>
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

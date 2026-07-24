import { ArrowUpRight, Menu, X } from "lucide-react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { useEffect, useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type ReactNode, type RefObject } from "react";

import { PRODUCT_NAME } from "../brand";
import { AppLink } from "../navigation";
import { recordViewport } from "../windowPreferences";
import { RabbitMark, type RabbitVariant } from "./RabbitMark";

// RC ID: RC-054. Render the Rabbit Code brand while retaining route compatibility.
// RC ID: RC-129. Keep route Rabbit artwork below the content hierarchy and decorative-only.

const productLinks = [
  ["Workspace home", "/workspace/home"],
  ["Agent tasks", "/workspace/task"],
  ["Change review", "/workspace/review"],
  ["Prompt assets", "/workspace/assets"]
] as const;

const companyLinks = [
  ["Providers and models", "/workspace/providers"],
  ["Diagnostics", "/workspace/diagnostics"],
  ["Settings", "/workspace/settings"]
] as const;

export function SiteShell({ children, authenticated = false, isWorkspace = false, showSharedRabbit = false, rabbitVariant, hideHeader = false, onSignOut }: { children: ReactNode; authenticated?: boolean; isWorkspace?: boolean; showSharedRabbit?: boolean; rabbitVariant?: RabbitVariant; hideHeader?: boolean; onSignOut?: () => void }) {
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

    const revealElements = Array.from(frameRef.current?.querySelectorAll<HTMLElement>(".reveal-on-scroll") ?? []);
    if (revealElements.length === 0) {
      return;
    }

    const previousScrollRestoration = window.history.scrollRestoration;
    window.history.scrollRestoration = "manual";
    window.scrollTo(0, 0);
    gsap.registerPlugin(ScrollTrigger);
    const lenis = new Lenis({ autoRaf: false, lerp: 0.08 });
    let frame: number | null = null;
    const raf = (time: number) => {
      lenis.raf(time);
      frame = window.requestAnimationFrame(raf);
    };
    const startFrame = () => {
      if (frame === null && document.visibilityState === "visible") {
        frame = window.requestAnimationFrame(raf);
      }
    };
    const stopFrame = () => {
      if (frame !== null) {
        window.cancelAnimationFrame(frame);
        frame = null;
      }
    };
    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        startFrame();
      } else {
        stopFrame();
      }
    };
    startFrame();
    const context = gsap.context(() => {
      revealElements.forEach((element) => {
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
    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      stopFrame();
      document.removeEventListener("visibilitychange", handleVisibility);
      context.revert();
      lenis.destroy();
      window.history.scrollRestoration = previousScrollRestoration;
    };
  }, []);

  useEffect(() => {
    const saveViewport = () => { recordViewport(); };
    saveViewport();
    window.addEventListener("resize", saveViewport);
    window.addEventListener("beforeunload", saveViewport);
    return () => {
      window.removeEventListener("resize", saveViewport);
      window.removeEventListener("beforeunload", saveViewport);
    };
  }, []);

  return (
    <div className={hideHeader ? "site-frame site-frame-bare-workspace" : "site-frame"} ref={frameRef}>
      {hideHeader ? null : <SiteHeader authenticated={authenticated} isWorkspace={isWorkspace} menuOpen={menuOpen} menuButtonRef={menuButtonRef} onMenuToggle={() => setMenuOpen((open) => !open)} onSignOut={onSignOut} />}
      <div className="site-content">
        {showSharedRabbit ? <SharedRabbit /> : null}
        {rabbitVariant ? <div aria-hidden="true" data-rabbit-layer="decorative" data-rabbit-route={window.location.pathname} className={`route-rabbit-slot route-rabbit-slot-${rabbitVariant}`}><RabbitMark variant={rabbitVariant} decorative /></div> : null}
        {children}
      </div>
      {menuOpen ? <SiteMenu menuRef={menuRef} onClose={() => setMenuOpen(false)} /> : null}
    </div>
  );
}

function SiteHeader({ authenticated, isWorkspace, menuOpen, menuButtonRef, onMenuToggle, onSignOut }: { authenticated: boolean; isWorkspace: boolean; menuOpen: boolean; menuButtonRef: RefObject<HTMLButtonElement>; onMenuToggle: () => void; onSignOut?: () => void }) {
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
          title={menuOpen ? "Close navigation" : "Open navigation"}
          onClick={onMenuToggle}
        >
          {menuOpen ? <X size={23} strokeWidth={1.5} /> : <Menu size={23} strokeWidth={1.5} />}
        </button>
      </div>
      <AppLink className="site-logo" href={isWorkspace ? "/workspace/home" : "/"} aria-label={`${PRODUCT_NAME} home`}>
        {PRODUCT_NAME}
      </AppLink>
      <nav className="site-nav" aria-label="Primary navigation">
        <AppLink href="/workspace/home">WORKSPACE</AppLink>
        <AppLink href="/workspace/task">TASKS</AppLink>
        <AppLink href="/workspace/review">REVIEW</AppLink>
        <AppLink href="/workspace/settings">SETTINGS</AppLink>
      </nav>
      {authenticated ? (
        <button className="header-action" type="button" onClick={onSignOut}>SIGN OUT <ArrowUpRight size={14} aria-hidden="true" /></button>
      ) : (
        <AppLink className="header-action" href={isWorkspace ? "/login" : "/workspace/home"}>
          {isWorkspace ? "LOGIN" : "OPEN WORKSPACE"} <ArrowUpRight size={14} aria-hidden="true" />
        </AppLink>
      )}
    </header>
  );
}

function SiteMenu({ menuRef, onClose }: { menuRef: RefObject<HTMLElement>; onClose: () => void }) {
  return (
    <aside id="site-navigation" ref={menuRef} className="site-menu" role="dialog" aria-modal="true" aria-label="Full-screen navigation" tabIndex={-1} onKeyDown={(event) => trapMenuFocus(event, menuRef)}>
      <div className="site-menu-inner">
        <div className="site-menu-group">
          <span className="eyebrow">PRODUCTS</span>
          {productLinks.map(([label, href]) => (
            <AppLink key={href} className="menu-link" href={href} onClick={onClose}>
              <span>{label}</span>
              <ArrowUpRight size={18} aria-hidden="true" />
            </AppLink>
          ))}
        </div>
        <div className="site-menu-group">
          <span className="eyebrow">PROJECT</span>
          {companyLinks.map(([label, href]) => (
            <AppLink key={href} className="menu-link" href={href} onClick={onClose}>
              <span>{label}</span>
              <ArrowUpRight size={18} aria-hidden="true" />
            </AppLink>
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

function SharedRabbit() {
  return (
    <div className="shared-rabbit-mark">
      <RabbitMark variant="mark" alt="PromptLayer 风格复古版画兔兔插画" loading="eager" />
    </div>
  );
}

function trapMenuFocus(event: ReactKeyboardEvent<HTMLElement>, menuRef: RefObject<HTMLElement>) {
  if (event.key !== "Tab") {
    return;
  }
  const menu = menuRef.current;
  if (!menu) {
    return;
  }
  const focusable = Array.from(menu.querySelectorAll<HTMLElement>(
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )).filter((element) => element.getAttribute("aria-hidden") !== "true");
  if (focusable.length === 0) {
    event.preventDefault();
    menu.focus();
    return;
  }
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function ServiceStatus() {
  return (
    <span className="service-status">
      <i aria-hidden="true" />
      LOCAL SERVICES OPERATIONAL
    </span>
  );
}

import { ArrowUpRight, Cloud, Cpu, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState, type ReactNode } from "react";

import { PRODUCT_NAME } from "./brand";
import { RabbitMark } from "./components/RabbitMark";

// RC IDs: RC-109, RC-159, RC-183. Provide explicit local/API configuration choices.

type ServiceState = "ready" | "not-configured" | "unavailable";
type OnboardingPhase = "checking" | "new" | "configured" | "error";

type OnboardingSnapshot = {
  configuration: ServiceState;
  appServer: ServiceState;
  keyVault: ServiceState;
  localRunner: ServiceState;
};

const initialSnapshot: OnboardingSnapshot = {
  configuration: "not-configured",
  appServer: "not-configured",
  keyVault: "not-configured",
  localRunner: "not-configured",
};

export function OnboardingPage() {
  const [phase, setPhase] = useState<OnboardingPhase>("checking");
  const [snapshot, setSnapshot] = useState(initialSnapshot);

  const checkEnvironment = useCallback(async () => {
    setPhase("checking");
    const configured = localStorage.getItem("rabbit_code_onboarding_configured") === "true";
    const apiConfigured = localStorage.getItem("rabbit_code_api_configured") === "true";
    const localRunnerReady = localStorage.getItem("rabbit_code_local_runner_ready") === "true";
    let appServer: ServiceState = "not-configured";
    let unavailable = false;

    try {
      const response = await fetch("/api/v1/health", { cache: "no-store" });
      appServer = response.ok
        ? "ready"
        : response.status === 404
          ? "not-configured"
          : "unavailable";
      unavailable = appServer === "unavailable";
    } catch {
      appServer = "unavailable";
      unavailable = true;
    }

    setSnapshot({
      configuration: configured ? "ready" : "not-configured",
      appServer,
      keyVault: apiConfigured ? "ready" : "not-configured",
      localRunner: localRunnerReady ? "ready" : "not-configured",
    });
    setPhase(unavailable ? "error" : configured ? "configured" : "new");
  }, []);

  useEffect(() => {
    void checkEnvironment();
  }, [checkEnvironment]);

  const stateLabel = phase === "checking"
    ? "CHECKING LOCAL RUNTIME"
    : phase === "error"
      ? "LOCAL SERVICE UNAVAILABLE"
      : phase === "configured"
        ? "CONFIGURATION FOUND"
        : "NEW INSTALLATION";

  return (
    <main className="onboarding-page">
      <section className="onboarding-hero" aria-labelledby="onboarding-title">
        <div className="onboarding-topline">
          <span className="eyebrow">FIRST RUN / LOCAL WORKSPACE</span>
          <span className="onboarding-version">RABBIT CODE / V3.0</span>
        </div>
        <div className="onboarding-hero-grid">
          <div className="onboarding-copy">
            <span className="onboarding-mark"><RabbitMark variant="mark" decorative size={20} /> {PRODUCT_NAME}</span>
            <h1 id="onboarding-title">Start Rabbit Code.</h1>
            <p>Choose the route that fits this workspace. You can switch providers and local models later.</p>
          </div>
          <div className="onboarding-artwork">
            <span className="onboarding-art-label">LOCAL FIRST / OPEN SOURCE</span>
            <RabbitMark
              variant="full"
              alt="Rabbit Code 兔兔品牌插画"
              loading="eager"
            />
          </div>
        </div>
      </section>

      <section className="onboarding-panel" aria-labelledby="onboarding-choice-title">
        <div className="onboarding-panel-heading">
          <div>
            <span className="eyebrow">SETUP STATUS</span>
            <h2 id="onboarding-choice-title">Choose your starting point.</h2>
          </div>
          <p role="status" className={`onboarding-state onboarding-state-${phase}`}>
            {stateLabel}
          </p>
        </div>

        <div className="onboarding-status-grid" aria-label="Environment status">
          <StatusRow label="Configuration" value={snapshot.configuration} />
          <StatusRow label="App Server" value={snapshot.appServer} />
          <StatusRow label="Key vault" value={snapshot.keyVault} />
          <StatusRow label="Local runner" value={snapshot.localRunner} />
        </div>

        <div className="onboarding-choice-grid">
          <SetupChoice
            entry="api"
            icon={<Cloud size={20} aria-hidden="true" />}
            eyebrow="REMOTE ROUTE"
            label="USE API / CONFIGURE PROVIDER"
            detail="Use a provider you configure with an API credential."
            points={[
              "DATA / SENT TO SELECTED PROVIDER",
              "NETWORK / INTERNET REQUIRED",
              "ACCOUNT / PROVIDER CREDENTIAL, NOT RABBIT CODE",
            ]}
          />
          <SetupChoice
            entry="local"
            icon={<Cpu size={20} aria-hidden="true" />}
            eyebrow="LOCAL ROUTE"
            label="NO API / LOCAL MODEL"
            detail="Run a local model on this device after a hardware check."
            points={[
              "DATA / STAYS ON THIS DEVICE",
              "NETWORK / NOT REQUIRED AFTER SETUP",
              "HARDWARE / CPU, GPU, AND DISK CHECK",
            ]}
          />
        </div>

        {phase === "error" ? (
          <button className="onboarding-recheck" type="button" onClick={() => void checkEnvironment()}>
            <RefreshCw size={15} aria-hidden="true" /> RECHECK LOCAL SERVICES
          </button>
        ) : null}
      </section>
    </main>
  );
}

function StatusRow({ label, value }: { label: string; value: ServiceState }) {
  const valueLabel = value === "ready" ? "READY" : value === "unavailable" ? "UNAVAILABLE" : "NOT CONFIGURED";
  return (
    <div className="onboarding-status-row">
      <span>{label}</span>
      <strong className={`status-value status-value-${value}`}>
        <i aria-hidden="true" /> {valueLabel}
      </strong>
    </div>
  );
}

function SetupChoice({
  entry,
  icon,
  eyebrow,
  label,
  detail,
  points,
}: {
  entry: "api" | "local";
  icon: ReactNode;
  eyebrow: string;
  label: string;
  detail: string;
  points: readonly string[];
}) {
  return (
    <a
      className="onboarding-choice"
      href={entry === "api" ? "/workspace/providers?entry=api" : "/workspace/models?entry=local"}
      onClick={() => localStorage.setItem("rabbit_code_onboarding_choice", entry)}
    >
      <span className="onboarding-choice-icon">{icon}</span>
      <span className="onboarding-choice-copy">
        <span className="onboarding-choice-eyebrow">{eyebrow}</span>
        <strong>{label}</strong>
        <small>{detail}</small>
        <ul className="onboarding-choice-points">
          {points.map((point) => <li key={point}>{point}</li>)}
        </ul>
      </span>
      <ArrowUpRight size={18} aria-hidden="true" />
    </a>
  );
}

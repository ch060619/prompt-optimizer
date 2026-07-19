import { useEffect, useId, useRef, useState, type ReactNode, type RefObject } from "react";

// RC IDs: RC-135, RC-136, RC-137. Keep state, naming, and input snapshots request-scoped.

export type PromptOptimizeState =
  | "idle"
  | "hover"
  | "pressed"
  | "loading"
  | "success"
  | "error"
  | "disabled"
  | "cancelling";

export type PromptOptimizationSnapshot = {
  text: string;
  revision: number;
  cursor: { start: number; end: number };
  attachmentRefs: string[];
};

export type PromptOptimizeButtonProps = {
  icon: ReactNode;
  label?: ReactNode;
  ariaLabel?: string;
  tooltip?: string;
  disabled?: boolean;
  input?: string;
  revision?: number;
  cursor?: { start: number; end: number };
  attachmentRefs?: readonly string[];
  maxCharacters?: number;
  onValidationError?: (message: string) => void;
  buttonRef?: RefObject<HTMLButtonElement>;
  onOptimize: (requestId: string, signal: AbortSignal, snapshot: PromptOptimizationSnapshot) => Promise<void>;
};

const busyStates = new Set<PromptOptimizeState>(["loading", "cancelling"]);

export function PromptOptimizeButton({
  icon,
  label = "优化",
  ariaLabel = "优化输入内容",
  tooltip = "优化输入内容",
  disabled = false,
  input = "Test prompt",
  revision = 0,
  cursor = { start: 0, end: 0 },
  attachmentRefs = [],
  maxCharacters = 12000,
  onValidationError,
  buttonRef,
  onOptimize,
}: PromptOptimizeButtonProps) {
  const effectiveDisabled = disabled || (!input.trim() && attachmentRefs.length === 0);
  const [state, setState] = useState<PromptOptimizeState>(effectiveDisabled ? "disabled" : "idle");
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const sequenceRef = useRef(0);
  const activeRef = useRef<{ id: string; controller: AbortController; snapshot: PromptOptimizationSnapshot } | null>(null);
  const tooltipTimerRef = useRef<number | null>(null);
  const tooltipId = useId();

  useEffect(() => {
    if (activeRef.current) {
      return;
    }
    setState((current) => {
      if (effectiveDisabled) {
        return "disabled";
      }
      return current === "disabled" ? "idle" : current;
    });
  }, [effectiveDisabled]);

  useEffect(() => () => {
    if (tooltipTimerRef.current !== null) {
      window.clearTimeout(tooltipTimerRef.current);
    }
  }, []);

  function hideTooltip() {
    if (tooltipTimerRef.current !== null) {
      window.clearTimeout(tooltipTimerRef.current);
      tooltipTimerRef.current = null;
    }
    setTooltipVisible(false);
  }

  function scheduleTooltip() {
    if (effectiveDisabled && !busyStates.has(state)) {
      return;
    }
    if (tooltipTimerRef.current !== null) {
      window.clearTimeout(tooltipTimerRef.current);
    }
    tooltipTimerRef.current = window.setTimeout(() => {
      setTooltipVisible(true);
      tooltipTimerRef.current = null;
    }, 500);
  }

  function cancel() {
    const active = activeRef.current;
    if (!active) {
      return;
    }
    active.controller.abort();
    activeRef.current = null;
    setState("cancelling");
    queueMicrotask(() => {
      setState((current) => current === "cancelling" ? "idle" : current);
    });
  }

  function start() {
    if (effectiveDisabled || activeRef.current) {
      return;
    }
    if (!input.trim() && attachmentRefs.length > 0) {
      onValidationError?.("只有附件暂不支持优化，请先输入提示词。");
      setState("error");
      return;
    }
    if (!input.trim()) {
      onValidationError?.("请输入提示词后再优化。");
      setState("error");
      return;
    }
    if (input.length > maxCharacters) {
      onValidationError?.(`提示词超过 ${maxCharacters} 个字符限制，未截断原文。`);
      setState("error");
      return;
    }
    const requestId = `prompt-optimize-${++sequenceRef.current}`;
    const controller = new AbortController();
    const snapshot: PromptOptimizationSnapshot = {
      text: input,
      revision,
      cursor: { start: cursor.start, end: cursor.end },
      attachmentRefs: [...attachmentRefs],
    };
    activeRef.current = { id: requestId, controller, snapshot };
    setState("loading");
    void Promise.resolve()
      .then(() => onOptimize(requestId, controller.signal, snapshot))
      .then(() => {
        if (activeRef.current?.id !== requestId) {
          return;
        }
        activeRef.current = null;
        setState("success");
      })
      .catch(() => {
        if (activeRef.current?.id !== requestId) {
          return;
        }
        activeRef.current = null;
        setState("error");
      });
  }

  function handleClick() {
    if (busyStates.has(state)) {
      cancel();
      return;
    }
    start();
  }

  const isBusy = busyStates.has(state);
  return (
    <button
      ref={buttonRef}
      className="prompt-optimize-button"
      type="button"
      data-state={state}
      data-action="prompt-optimize"
      data-tooltip={tooltip}
      aria-label={ariaLabel}
      aria-describedby={tooltipVisible ? tooltipId : undefined}
      aria-busy={isBusy}
      disabled={effectiveDisabled && !isBusy}
      onClick={handleClick}
      onFocus={scheduleTooltip}
      onBlur={hideTooltip}
      onPointerEnter={() => { setState((current) => current === "idle" ? "hover" : current); scheduleTooltip(); }}
      onPointerLeave={() => { setState((current) => current === "hover" ? "idle" : current); hideTooltip(); }}
      onPointerDown={() => setState((current) => current === "idle" || current === "hover" ? "pressed" : current)}
    >
      {icon}
      <span className="prompt-optimize-label">{label}</span>
      <span className="sr-only">{state}</span>
      {tooltipVisible ? <span className="prompt-optimize-tooltip" id={tooltipId} role="tooltip">{tooltip}</span> : null}
    </button>
  );
}

import { GitCompare, History, SlidersHorizontal, X } from "lucide-react";
import { useState } from "react";

import type { PromptTemplate, VersionSummary } from "../types";

export type OptimizationStrength = "light" | "balanced" | "strong";

type PromptOptimizationControlsProps = {
  templates: PromptTemplate[];
  selectedTemplate?: string;
  onTemplateChange: (templateId: string) => void;
  scenario: string;
  onScenarioChange: (scenario: string) => void;
  role: string;
  onRoleChange: (role: string) => void;
  strength: OptimizationStrength;
  onStrengthChange: (strength: OptimizationStrength) => void;
  scoreEnabled: boolean;
  onScoreEnabledChange: (enabled: boolean) => void;
  history: VersionSummary[];
  activeVersion: number | null;
  onCompareVersion: (versionId: number) => void;
};

export function PromptOptimizationControls({
  templates,
  selectedTemplate,
  onTemplateChange,
  scenario,
  onScenarioChange,
  role,
  onRoleChange,
  strength,
  onStrengthChange,
  scoreEnabled,
  onScoreEnabledChange,
  history,
  activeVersion,
  onCompareVersion,
}: PromptOptimizationControlsProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="composer-controls">
      <button
        type="button"
        className="composer-controls-trigger"
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((current) => !current)}
        title="打开优化控制"
      >
        <SlidersHorizontal size={15} aria-hidden="true" />
        优化控制
      </button>
      {open ? (
        <div className="composer-controls-popover" role="dialog" aria-label="优化控制">
          <div className="composer-controls-heading">
            <strong>优化控制</strong>
            <button
              type="button"
              className="icon-button"
              aria-label="关闭优化控制"
              title="关闭优化控制"
              onClick={() => setOpen(false)}
            >
              <X size={15} aria-hidden="true" />
            </button>
          </div>
          <label className="composer-control-field">
            <span>模板</span>
            <select
              aria-label="优化模板"
              value={selectedTemplate ?? ""}
              onChange={(event) => onTemplateChange(event.target.value)}
            >
              <option value="">不使用模板</option>
              {templates.map((template) => (
                <option key={template.id} value={template.id}>{template.name}</option>
              ))}
            </select>
          </label>
          <details className="composer-controls-advanced">
            <summary>高级优化控制</summary>
            <div className="composer-controls-fields">
              <label className="composer-control-field">
                <span>场景</span>
                <select aria-label="优化场景" value={scenario} onChange={(event) => onScenarioChange(event.target.value)}>
                  <option value="通用">通用</option>
                  <option value="代码生成">代码生成</option>
                  <option value="内容改写">内容改写</option>
                  <option value="分析决策">分析决策</option>
                </select>
              </label>
              <label className="composer-control-field">
                <span>角色</span>
                <select aria-label="优化角色" value={role} onChange={(event) => onRoleChange(event.target.value)}>
                  <option value="不指定">不指定</option>
                  <option value="领域专家">领域专家</option>
                  <option value="产品经理">产品经理</option>
                  <option value="教师">教师</option>
                </select>
              </label>
              <label className="composer-control-field">
                <span>优化强度</span>
                <select aria-label="优化强度" value={strength} onChange={(event) => onStrengthChange(event.target.value as OptimizationStrength)}>
                  <option value="light">轻量</option>
                  <option value="balanced">平衡</option>
                  <option value="strong">深入</option>
                </select>
              </label>
              <label className="composer-control-toggle">
                <span>生成评分</span>
                <input
                  type="checkbox"
                  aria-label="生成评分"
                  checked={scoreEnabled}
                  onChange={(event) => onScoreEnabledChange(event.target.checked)}
                />
              </label>
            </div>
            <div className="composer-controls-history">
              <div className="composer-controls-subheading">
                <History size={14} aria-hidden="true" />
                <span>历史版本</span>
              </div>
              {history.length ? history.slice(0, 5).map((item) => (
                <div className="composer-history-row" key={item.id}>
                  <span>#{item.id} · {item.score}</span>
                  <button
                    type="button"
                    className="icon-button"
                    aria-label={`比较版本 ${item.id}`}
                    title={activeVersion === item.id ? "当前版本" : `比较版本 ${item.id}`}
                    disabled={activeVersion === null || activeVersion === item.id}
                    onClick={() => onCompareVersion(item.id)}
                  >
                    <GitCompare size={14} aria-hidden="true" />
                  </button>
                </div>
              )) : <span className="composer-controls-empty">暂无保存版本</span>}
            </div>
          </details>
        </div>
      ) : null}
    </div>
  );
}

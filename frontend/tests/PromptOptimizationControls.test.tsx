import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PromptOptimizationControls } from "../src/components/PromptOptimizationControls";

const templates = [
  {
    id: "tech-code-generation",
    name: "代码生成",
    category: "tech",
    description: "生成可维护实现",
    tags: ["code"],
    template: "实现 {feature}",
    variables: ["feature"],
    best_practices: []
  }
];

const history = [
  { id: 1, original_preview: "原始提示词", optimized_preview: "优化结果", score: 84, created_at: "2026-07-18T00:00:00Z" }
];

function renderControls() {
  const props = {
    templates,
    selectedTemplate: undefined,
    onTemplateChange: vi.fn(),
    scenario: "通用",
    onScenarioChange: vi.fn(),
    role: "不指定",
    onRoleChange: vi.fn(),
    strength: "balanced" as const,
    onStrengthChange: vi.fn(),
    scoreEnabled: true,
    onScoreEnabledChange: vi.fn(),
    history,
    activeVersion: 2,
    onCompareVersion: vi.fn()
  };
  render(<PromptOptimizationControls {...props} />);
  return props;
}

describe("PromptOptimizationControls", () => {
  it("keeps the composer control state available in a closed and reopened popover", () => {
    renderControls();

    fireEvent.click(screen.getByRole("button", { name: "优化控制" }));
    fireEvent.click(screen.getByText("高级优化控制"));
    fireEvent.change(screen.getByRole("combobox", { name: "优化场景" }), { target: { value: "代码生成" } });
    fireEvent.click(screen.getByRole("button", { name: "关闭优化控制" }));
    fireEvent.click(screen.getByRole("button", { name: "优化控制" }));
    fireEvent.click(screen.getByText("高级优化控制"));

    expect(screen.getByRole("button", { name: "优化控制" })).toHaveAttribute("aria-expanded", "true");
  });

  it("supports template selection and version comparison from the composer", () => {
    const props = renderControls();

    fireEvent.click(screen.getByRole("button", { name: "优化控制" }));
    fireEvent.click(screen.getByText("高级优化控制"));
    fireEvent.change(screen.getByRole("combobox", { name: "优化模板" }), { target: { value: "tech-code-generation" } });
    fireEvent.click(screen.getByRole("button", { name: "比较版本 1" }));

    expect(props.onTemplateChange).toHaveBeenCalledWith("tech-code-generation");
    expect(props.onCompareVersion).toHaveBeenCalledWith(1);
  });
});

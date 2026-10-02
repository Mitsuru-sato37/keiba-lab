import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { goldenRaceCases } from "../goldenRaceFixture";
import { LogicExplorerView } from "./LogicExplorerView";

describe("Logic Explorer view", () => {
  it("shows stage evidence, lineage, and explicit gated values", () => {
    const onBack = vi.fn();
    const onSelectStage = vi.fn();
    render(
      <LogicExplorerView
        race={goldenRaceCases[1]}
        stageId="ability_prediction"
        onBack={onBack}
        onSelectStage={onSelectStage}
      />,
    );

    expect(screen.getByRole("heading", { name: "Logic Explorer" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Ability prediction" })).toBeVisible();
    expect(screen.getByText("Form score features")).toBeVisible();
    expect(screen.getByText("FEATURE-CORE-V1")).toBeVisible();
    expect(screen.queryByText("Current-race odds")).not.toBeInTheDocument();
    expect(screen.getAllByText("未提供").length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Recommendation" }));
    expect(onSelectStage).toHaveBeenCalledWith("recommendation");
    fireEvent.click(screen.getByRole("button", { name: "Back to Race" }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });
});

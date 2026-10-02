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

    expect(screen.getByRole("heading", { name: "予想の根拠" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "能力予測" })).toBeVisible();
    expect(screen.getByText("走力スコアの特徴量")).toBeVisible();
    expect(screen.getByText("FEATURE-CORE-V1")).toBeVisible();
    expect(screen.queryByText("当該レースのオッズ")).not.toBeInTheDocument();
    expect(screen.getAllByText("未提供").length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "最終判定" }));
    expect(onSelectStage).toHaveBeenCalledWith("recommendation");
    fireEvent.click(screen.getByRole("button", { name: "レース詳細に戻る" }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });
});

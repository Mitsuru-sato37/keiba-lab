import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  GOLDEN_STAGE_ORDER,
  getGoldenRaceCase,
} from "../goldenRaceFixture";
import { EvidenceRow } from "./EvidenceRow";
import { StageTimeline } from "./StageTimeline";
import { StatusBadge } from "./StatusBadge";

describe("Golden Race shared components", () => {
  it("renders BUY and SKIP as visible statuses", () => {
    render(
      <>
        <StatusBadge decision="BUY" />
        <StatusBadge decision="SKIP" />
      </>,
    );

    expect(screen.getByText("BUY")).toBeVisible();
    expect(screen.getByText("SKIP")).toBeVisible();
  });

  it("renders missing evidence explicitly", () => {
    render(<EvidenceRow label="Result" value={null} />);

    expect(screen.getByText("Result")).toBeVisible();
    expect(screen.getByText("未提供")).toBeVisible();
  });

  it("renders the fixed stage order and reports selected stages", () => {
    const race = getGoldenRaceCase("golden-buy");
    const onSelect = vi.fn();
    render(
      <StageTimeline
        stages={race.stages}
        selectedStageId={GOLDEN_STAGE_ORDER[0]}
        onSelect={onSelect}
      />,
    );

    expect(screen.getAllByRole("button").map((button) => button.textContent)).toEqual(
      race.stages.map((stage) => stage.label),
    );
    expect(screen.getAllByRole("button")[0]).toHaveAttribute(
      "aria-current",
      "step",
    );

    fireEvent.click(screen.getByRole("button", { name: "Recommendation" }));
    expect(onSelect).toHaveBeenCalledWith("recommendation");
  });
});

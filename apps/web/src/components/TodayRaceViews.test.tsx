import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { goldenRaceCases } from "../goldenRaceFixture";
import { RaceView } from "./RaceView";
import { TodayView } from "./TodayView";

describe("Today and Race views", () => {
  it("renders both fixture cases and reports the selected race", () => {
    const onSelectRace = vi.fn();
    render(<TodayView cases={goldenRaceCases} onSelectRace={onSelectRace} />);

    expect(screen.getByRole("heading", { name: "Today" })).toBeVisible();
    expect(screen.getByText("Golden Race BUY")).toBeVisible();
    expect(screen.getByText("Golden Race SKIP")).toBeVisible();

    fireEvent.click(
      screen.getByRole("button", { name: "Open Golden Race SKIP" }),
    );
    expect(onSelectRace).toHaveBeenCalledWith("golden-skip");
  });

  it("uses the same summary structure for BUY and SKIP", () => {
    const onBack = vi.fn();
    const onExploreStage = vi.fn();
    const { rerender } = render(
      <RaceView
        race={goldenRaceCases[0]}
        onBack={onBack}
        onExploreStage={onExploreStage}
      />,
    );

    expect(screen.getByRole("heading", { name: "Race" })).toBeVisible();
    expect(screen.getAllByText("BUY").length).toBeGreaterThan(0);
    expect(screen.getByText("Stable")).toBeVisible();
    expect(screen.getByText(/Result and payout: unavailable/)).toBeVisible();

    rerender(
      <RaceView
        race={goldenRaceCases[1]}
        onBack={onBack}
        onExploreStage={onExploreStage}
      />,
    );

    expect(screen.getAllByText("SKIP").length).toBeGreaterThan(0);
    expect(screen.getByText("SKIP_NO_VALUE")).toBeVisible();
    expect(screen.getByText("Stable")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Recommendation" }));
    expect(onExploreStage).toHaveBeenCalledWith("recommendation");
    fireEvent.click(screen.getByRole("button", { name: "Back to Today" }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });
});

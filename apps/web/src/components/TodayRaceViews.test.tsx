import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { goldenRaceCases } from "../goldenRaceFixture";
import { RaceView } from "./RaceView";
import { TodayView } from "./TodayView";

describe("Today and Race views", () => {
  it("renders both fixture cases and reports the selected race", () => {
    const onSelectRace = vi.fn();
    render(<TodayView cases={goldenRaceCases} onSelectRace={onSelectRace} />);

    expect(screen.getByRole("heading", { name: "レース一覧" })).toBeVisible();
    expect(screen.getByText("ゴールデンレース（購入）")).toBeVisible();
    expect(screen.getByText("ゴールデンレース（見送り）")).toBeVisible();

    fireEvent.click(
      screen.getByRole("button", { name: "詳細を見る：ゴールデンレース（見送り）" }),
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

    expect(screen.getByRole("heading", { name: "レース詳細" })).toBeVisible();
    expect(screen.getAllByText("購入").length).toBeGreaterThan(0);
    expect(screen.getByText("安定型")).toBeVisible();
    expect(screen.getByText(/結果と払戻は表示されません/)).toBeVisible();

    rerender(
      <RaceView
        race={goldenRaceCases[1]}
        onBack={onBack}
        onExploreStage={onExploreStage}
      />,
    );

    expect(screen.getAllByText("見送り").length).toBeGreaterThan(0);
    expect(screen.getByText(/SKIP_NO_VALUE/)).toBeVisible();
    expect(screen.getByText("安定型")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "最終判定" }));
    expect(onExploreStage).toHaveBeenCalledWith("recommendation");
    fireEvent.click(screen.getByRole("button", { name: "レース一覧に戻る" }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("shows the first 2022 validation race with predictions and revealed result", () => {
    const onSelectRace = vi.fn();
    render(<TodayView cases={goldenRaceCases} onSelectRace={onSelectRace} />);

    expect(screen.getByRole("heading", { name: "まず見る情報" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "2022年1月5日 1R" })).toBeVisible();
    expect(screen.getByText(/validation-2022-0105-r01/)).toBeVisible();
    expect(screen.getByText("2022年1月5日 10:00（日本時間）")).toBeVisible();
    expect(screen.getByText("66.7%")).toBeVisible();
    expect(screen.getByText("33.3%")).toBeVisible();
    expect(screen.getAllByText("購入").length).toBeGreaterThan(0);
    expect(screen.getByText("勝ち馬")).toBeVisible();
    expect(screen.getAllByText("1番")).toHaveLength(2);
    expect(screen.getByText("280円")).toBeVisible();
    expect(screen.getByText(/合成テストデータです/)).toBeVisible();
  });
});

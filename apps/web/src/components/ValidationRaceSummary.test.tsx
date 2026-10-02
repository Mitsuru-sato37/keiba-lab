import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ValidationRaceSummary } from "./ValidationRaceSummary";

describe("ValidationRaceSummary", () => {
  it("organizes the validation race into overview, details, and notes", () => {
    render(<ValidationRaceSummary />);

    expect(screen.getByRole("heading", { name: "まず見る情報" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "2022年1月5日 1R" })).toBeVisible();
    expect(screen.getByText("勝ち馬")).toBeVisible();
    expect(screen.getAllByText("1番")).toHaveLength(2);

    expect(screen.getByRole("heading", { name: "詳しい内容" })).toBeVisible();
    expect(screen.getByText("2022年1月5日 10:00（日本時間）")).toBeVisible();
    expect(screen.getByRole("table", { name: "出走馬の予想" })).toBeVisible();
    expect(screen.getAllByText("1番")).toHaveLength(2);
    expect(screen.getByText("2番")).toBeVisible();

    expect(screen.getByRole("heading", { name: "備考" })).toBeVisible();
    expect(screen.getByText(/実際のJRAデータ/)).toBeVisible();
    expect(screen.getByText(/追跡用レースID/)).toBeVisible();
  });
});

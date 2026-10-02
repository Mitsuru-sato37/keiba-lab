import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("navigates from the Japanese race list to details and evidence", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "レース一覧" })).toBeVisible();
    expect(
      screen.getByRole("navigation", { name: "メインメニュー" }),
    ).toBeVisible();
    expect(screen.getByText(/合成テストデータ/)).toBeVisible();
    expect(screen.getByRole("navigation")).toHaveClass("app-navigation");
    expect(screen.getByRole("main")).toHaveClass("app-shell");

    fireEvent.click(
      screen.getByRole("button", { name: "詳細を見る：ゴールデンレース（見送り）" }),
    );
    expect(screen.getByRole("heading", { name: "レース詳細" })).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "最終判定" }));
    expect(screen.getByRole("heading", { name: "予想の根拠" })).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "レース詳細に戻る" }));
    expect(screen.getByRole("heading", { name: "レース詳細" })).toBeVisible();
  });
});

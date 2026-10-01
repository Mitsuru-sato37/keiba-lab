import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("shows the Phase 0 product status", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "keiba-lab" })).toBeVisible();
    expect(screen.getByText("Phase 0 project skeleton")).toBeVisible();
  });
});

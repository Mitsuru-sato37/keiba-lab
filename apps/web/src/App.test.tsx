import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("navigates from Today to Race and Logic Explorer", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Today" })).toBeVisible();

    fireEvent.click(
      screen.getByRole("button", { name: "Open Golden Race SKIP" }),
    );
    expect(screen.getByRole("heading", { name: "Race" })).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Recommendation" }));
    expect(screen.getByRole("heading", { name: "Logic Explorer" })).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Back to Race" }));
    expect(screen.getByRole("heading", { name: "Race" })).toBeVisible();
  });
});

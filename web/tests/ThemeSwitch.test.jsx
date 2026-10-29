import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ThemeSwitch from "../components/ThemeSwitch.jsx";

afterEach(cleanup);

describe("ThemeSwitch", () => {
  it("shows the three themes as one labelled group", () => {
    render(<ThemeSwitch theme="system" />);
    expect(screen.getByRole("group", { name: "Theme" })).toBeTruthy();
    expect(screen.getAllByRole("button").map((b) => b.getAttribute("aria-label"))).toEqual([
      "System theme",
      "Light theme",
      "Dark theme",
    ]);
  });

  it("marks only the current theme as pressed", () => {
    render(<ThemeSwitch theme="dark" />);
    expect(screen.getByRole("button", { name: "Dark theme" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByRole("button", { name: "Light theme" }).getAttribute("aria-pressed")).toBe("false");
    expect(screen.getByRole("button", { name: "System theme" }).getAttribute("aria-pressed")).toBe("false");
  });

  it("gives the chosen theme to onChange", () => {
    const onChange = vi.fn();
    render(<ThemeSwitch theme="system" onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: "Light theme" }));
    expect(onChange).toHaveBeenCalledWith("light");
  });

  it("does nothing when the reader picks the current theme again", () => {
    const onChange = vi.fn();
    render(<ThemeSwitch theme="light" onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: "Light theme" }));
    expect(onChange).not.toHaveBeenCalled();
  });
});

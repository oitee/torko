import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ThemeSwitch from "../components/ThemeSwitch.jsx";

afterEach(cleanup);

describe("ThemeSwitch", () => {
  it("renders a single button with accessible name describing current and next theme", () => {
    render(<ThemeSwitch theme="system" />);
    const button = screen.getByRole("button", { name: "System theme. Change to light theme" });
    expect(button).toBeTruthy();
    expect(button.getAttribute("title")).toBe("System theme. Change to light theme");
  });

  it("cycles from system to light theme on click", () => {
    const onChange = vi.fn();
    render(<ThemeSwitch theme="system" onChange={onChange} />);
    const button = screen.getByRole("button", { name: /System theme/i });
    fireEvent.click(button);
    expect(onChange).toHaveBeenCalledWith("light");
  });

  it("cycles from light to dark theme on click", () => {
    const onChange = vi.fn();
    render(<ThemeSwitch theme="light" onChange={onChange} />);
    const button = screen.getByRole("button", { name: "Light theme. Change to dark theme" });
    fireEvent.click(button);
    expect(onChange).toHaveBeenCalledWith("dark");
  });

  it("cycles from dark to system theme on click", () => {
    const onChange = vi.fn();
    render(<ThemeSwitch theme="dark" onChange={onChange} />);
    const button = screen.getByRole("button", { name: "Dark theme. Change to system theme" });
    fireEvent.click(button);
    expect(onChange).toHaveBeenCalledWith("system");
  });
});

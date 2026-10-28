import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SiteHeader from "../components/SiteHeader.jsx";

afterEach(cleanup);

describe("SiteHeader", () => {
  it("renders Logo and Search link", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <SiteHeader theme="system" />
      </MemoryRouter>
    );

    expect(screen.getByRole("link", { name: "Torko home" })).toBeTruthy();
    const searchLink = screen.getByRole("link", { name: "Search" });
    expect(searchLink.getAttribute("href")).toBe("/search");
    expect(searchLink.getAttribute("aria-current")).toBeNull();
  });

  it("marks Search link active when on /search", () => {
    render(
      <MemoryRouter initialEntries={["/search"]}>
        <SiteHeader theme="system" />
      </MemoryRouter>
    );

    const searchLink = screen.getByRole("link", { name: "Search" });
    expect(searchLink.getAttribute("aria-current")).toBe("page");
    expect(searchLink.classList.contains("site-header__link--active")).toBe(true);
  });

  it("shows current theme label and calls onThemeChange on click", () => {
    const onThemeChange = vi.fn();
    render(
      <MemoryRouter initialEntries={["/"]}>
        <SiteHeader theme="light" onThemeChange={onThemeChange} />
      </MemoryRouter>
    );

    const button = screen.getByRole("button", { name: "Theme: Light" });
    expect(button).toBeTruthy();

    fireEvent.click(button);
    expect(onThemeChange).toHaveBeenCalledWith("dark");
  });
});

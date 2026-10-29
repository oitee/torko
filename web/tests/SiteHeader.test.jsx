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
    expect(screen.getByRole("link", { name: "Method" }).getAttribute("href")).toBe("/method");
  });

  it("marks the Method link active on /method", () => {
    render(
      <MemoryRouter initialEntries={["/method"]}>
        <SiteHeader theme="system" />
      </MemoryRouter>
    );

    expect(screen.getByRole("link", { name: "Method" }).getAttribute("aria-current")).toBe("page");
    expect(screen.getByRole("link", { name: "Search" }).getAttribute("aria-current")).toBeNull();
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

  it("shows the theme switch with the current theme and passes on the chosen theme", () => {
    const onThemeChange = vi.fn();
    render(
      <MemoryRouter initialEntries={["/"]}>
        <SiteHeader theme="light" onThemeChange={onThemeChange} />
      </MemoryRouter>
    );

    const themeButton = screen.getByRole("button", { name: "Light theme. Change to dark theme" });
    expect(themeButton).toBeTruthy();
    expect(screen.queryByText(/Theme:/)).toBeNull();

    fireEvent.click(themeButton);
    expect(onThemeChange).toHaveBeenCalledWith("dark");
  });
});

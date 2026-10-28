import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Breadcrumb from "../components/Breadcrumb.jsx";

afterEach(cleanup);

describe("Breadcrumb", () => {
  it("renders nav and ol elements with correct attributes", () => {
    const items = [
      { label: "Home", href: "/" },
      { label: "Members", href: "/members" },
      { label: "Mahua Moitra" },
    ];

    render(
      <MemoryRouter>
        <Breadcrumb items={items} />
      </MemoryRouter>
    );

    const nav = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(nav).toBeTruthy();

    const current = screen.getByText("Mahua Moitra");
    expect(current.getAttribute("aria-current")).toBe("page");
    expect(current.tagName).toBe("SPAN");
  });

  it("renders links for earlier items only", () => {
    const items = [
      { label: "Home", href: "/" },
      { label: "Tag", href: "/tag/arrears" },
      { label: "Current", href: "/should/not/link" },
    ];

    render(
      <MemoryRouter>
        <Breadcrumb items={items} />
      </MemoryRouter>
    );

    const homeLink = screen.getByRole("link", { name: "Home" });
    expect(homeLink.getAttribute("href")).toBe("/");

    const tagLink = screen.getByRole("link", { name: "Tag" });
    expect(tagLink.getAttribute("href")).toBe("/tag/arrears");

    expect(screen.queryByRole("link", { name: "Current" })).toBeNull();
  });

  it("marks separators as hidden from screen readers", () => {
    const items = [
      { label: "Home", href: "/" },
      { label: "Current" },
    ];

    const { container } = render(
      <MemoryRouter>
        <Breadcrumb items={items} />
      </MemoryRouter>
    );

    const separator = container.querySelector(".breadcrumb__separator");
    expect(separator).toBeTruthy();
    expect(separator.getAttribute("aria-hidden")).toBe("true");
    expect(separator.textContent).toBe("/");
  });

  it("renders collapsed marker when there are more than 3 items", () => {
    const items = [
      { label: "17th Lok Sabha", href: "/term/17" },
      { label: "Session 15", href: "/session/15" },
      { label: "12 Mar 2024", href: "/date/2024-03-12" },
      { label: "Debate title", href: "/debate/1" },
      { label: "Speech" },
    ];

    const { container } = render(
      <MemoryRouter>
        <Breadcrumb items={items} />
      </MemoryRouter>
    );

    const collapsed = container.querySelector(".breadcrumb__item--collapsed");
    expect(collapsed).toBeTruthy();
    expect(collapsed.getAttribute("aria-hidden")).toBe("true");
  });

  it("returns null when items is empty or omitted", () => {
    const { container } = render(<Breadcrumb items={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("keeps the middle item of a 3-item breadcrumb on phones", () => {
    const items = [
      { label: "Members", href: "/members" },
      { label: "West Bengal", href: "/place/west-bengal" },
      { label: "Krishnanagar" },
    ];

    const { container } = render(
      <MemoryRouter>
        <Breadcrumb items={items} />
      </MemoryRouter>
    );

    expect(container.querySelector(".breadcrumb__item--middle")).toBeNull();
    expect(container.querySelector(".breadcrumb__item--collapsed")).toBeNull();
    expect(screen.getByText("West Bengal")).toBeTruthy();
  });
});

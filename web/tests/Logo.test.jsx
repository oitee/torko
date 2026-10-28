import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Logo from "../components/Logo.jsx";

afterEach(cleanup);

describe("Logo", () => {
  it("renders a link to the home page with aria-label", () => {
    render(
      <MemoryRouter>
        <Logo />
      </MemoryRouter>
    );

    const link = screen.getByRole("link", { name: "Torko home" });
    expect(link).toBeTruthy();
    expect(link.getAttribute("href")).toBe("/");
  });

  it("renders the SVG mark with 33 seats and one marked seat", () => {
    const { container } = render(
      <MemoryRouter>
        <Logo />
      </MemoryRouter>
    );

    const svg = container.querySelector("svg");
    expect(svg).toBeTruthy();
    expect(svg.getAttribute("viewBox")).toBe("0 0 100 100");
    expect(svg.getAttribute("width")).toBe("28");
    expect(svg.getAttribute("height")).toBe("28");

    const circles = svg.querySelectorAll("circle");
    expect(circles.length).toBe(33);

    const marked = Array.from(circles).filter(
      (c) => c.getAttribute("fill") === "var(--header-action)"
    );
    expect(marked.length).toBe(1);
  });

  it("renders the text torko in lowercase", () => {
    render(
      <MemoryRouter>
        <Logo />
      </MemoryRouter>
    );

    expect(screen.getByText("torko")).toBeTruthy();
  });
});

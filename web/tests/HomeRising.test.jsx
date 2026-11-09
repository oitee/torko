import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import HomeRising, { MAX_RISING, sessionLine } from "../pages/home/HomeRising.jsx";
import homeAnswer from "./fixtures/home/home.json";

afterEach(cleanup);

function renderRising(props) {
  return render(
    <MemoryRouter>
      <HomeRising {...props} />
    </MemoryRouter>
  );
}

const base = { typical: homeAnswer.typical, sessionLabel: "Budget 2026", term: homeAnswer.term };

describe("HomeRising", () => {
  it("shows the first topics of the answer as chips, in the order of the answer", () => {
    const { container } = renderRising(base);
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(Math.min(MAX_RISING, homeAnswer.typical.length));
    const names = [...container.querySelectorAll(".home-rising__name")].map((n) => n.textContent);
    expect(names).toEqual(homeAnswer.typical.slice(0, MAX_RISING).map((s) => s.name));
    expect(links[0].getAttribute("href")).toBe(`/tag/${homeAnswer.typical[0].slug}`);
  });

  it("shows the speeches of the session in brackets after an up arrow, and no other text", () => {
    const { container } = renderRising(base);
    const first = homeAnswer.typical[0];
    expect(container.querySelector(".home-rising__count").textContent).toBe(`(${first.speeches_in_session ?? first.n})`);
    expect(container.querySelector(".home-rising__up")).toBeTruthy();
    expect(container.querySelector(".home-rising__meta")).toBeNull();
  });

  it("names the session under the title", () => {
    renderRising(base);
    expect(screen.getByText("(Budget 2026 session, 18th Lok Sabha)")).toBeTruthy();
    expect(sessionLine(null, 18)).toBe("(18th Lok Sabha)");
  });

  it("links a place to its place page", () => {
    renderRising({ ...base, typical: [{ name: "Iran", slug: "iran", type: "place", n: 14 }] });
    expect(screen.getByRole("link", { name: /^Iran, trending/ }).getAttribute("href")).toBe("/place/iran");
  });

  it("shows nothing without subjects", () => {
    expect(renderRising({ ...base, typical: [] }).container.innerHTML).toBe("");
  });
});

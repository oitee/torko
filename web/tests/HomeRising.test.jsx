import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import HomeRising, { MAX_RISING } from "../pages/home/HomeRising.jsx";
import homeAnswer from "./fixtures/home/home.json";

afterEach(cleanup);

function renderRising(props) {
  return render(
    <MemoryRouter>
      <HomeRising {...props} />
    </MemoryRouter>
  );
}

const base = {
  typical: homeAnswer.typical,
  session: homeAnswer.session,
  term: homeAnswer.term,
  first: homeAnswer.first,
  last: homeAnswer.last,
};

describe("HomeRising", () => {
  it("lists the first subjects of the answer, in the order of the answer", () => {
    renderRising(base);
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(MAX_RISING);
    expect(links.map((a) => a.textContent)).toEqual(homeAnswer.typical.slice(0, MAX_RISING).map((s) => s.name));
    expect(links[0].getAttribute("href")).toBe(`/tag/${homeAnswer.typical[0].slug}`);
  });

  it("shows the count of speeches of each subject in the session", () => {
    const { container } = renderRising(base);
    const first = homeAnswer.typical[0];
    expect(container.querySelector(".home-rising__count").textContent).toBe(`${first.n} speeches`);
  });

  it("states the session, its dates and the rule of the order", () => {
    const { container } = renderRising(base);
    const meta = container.querySelector(".home-rising__meta").textContent;
    expect(meta).toContain(`session ${homeAnswer.session} of the 18th Lok Sabha`);
    expect(meta).toContain("share of the speeches of this session");
  });

  it("links a place to its place page", () => {
    renderRising({ ...base, typical: [{ name: "Iran", slug: "iran", type: "place", n: 14 }] });
    expect(screen.getByRole("link", { name: "Iran" }).getAttribute("href")).toBe("/place/iran");
  });

  it("shows nothing without subjects", () => {
    expect(renderRising({ ...base, typical: [] }).container.innerHTML).toBe("");
  });
});

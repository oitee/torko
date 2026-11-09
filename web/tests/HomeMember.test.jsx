import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import HomeMember, { termList } from "../pages/home/HomeMember.jsx";
import featuredAnswer from "./fixtures/home/home_featured.json";

afterEach(cleanup);

function renderMember(member) {
  return render(
    <MemoryRouter>
      <HomeMember member={member} />
    </MemoryRouter>
  );
}

describe("termList", () => {
  it("joins the terms in running text", () => {
    expect(termList([18])).toBe("18th Lok Sabha");
    expect(termList([17, 18])).toBe("17th and 18th Lok Sabha");
    expect(termList([15, 17, 18])).toBe("15th, 17th and 18th Lok Sabha");
    expect(termList([])).toBe("");
  });
});

describe("HomeMember", () => {
  it("shows the printed label and the member that Torko finds for it", () => {
    const { container } = renderMember(featuredAnswer.member);
    expect(screen.getByText("SUSHRI MAHUA MOITRA (KRISHNANAGAR)")).toBeTruthy();
    const links = screen.getAllByRole("link", { name: /Mahua Moitra/ });
    for (const link of links) expect(link.getAttribute("href")).toBe("/member/1052");
    expect(container.querySelector(".home-member__counts").textContent).toBe("66 speeches in the 17th and 18th Lok Sabha");
    expect(container.querySelector(".home-member__speeches").textContent).toBe("66 speeches");
  });

  it("makes the whole part a target through the link of its text", () => {
    renderMember(featuredAnswer.member);
    const stretch = screen.getByRole("link", { name: /Read the 66 speeches by/ });
    expect(stretch.className).toContain("home-feature__stretch");
    expect(stretch.getAttribute("href")).toBe("/member/1052");
  });

  it("links the seat to its place page and names the state", () => {
    renderMember(featuredAnswer.member);
    expect(screen.getByRole("link", { name: "Krishnanagar" }).getAttribute("href")).toBe("/place/krishnanagar");
    expect(screen.getByText(/, West Bengal/)).toBeTruthy();
  });

  it("shows the seat as text when it has no place page", () => {
    renderMember({ ...featuredAnswer.member, seat_slug: null });
    expect(screen.queryByRole("link", { name: "Krishnanagar" })).toBeNull();
    expect(screen.getByText(/MP for Krishnanagar/)).toBeTruthy();
  });

  it("hides the seat line when the answer has no seat", () => {
    renderMember({ ...featuredAnswer.member, seat: null });
    expect(screen.queryByText(/MP for/)).toBeNull();
  });

  it("writes one speech in the singular", () => {
    const { container } = renderMember({ ...featuredAnswer.member, speeches: 1, terms: [18] });
    expect(container.querySelector(".home-member__counts").textContent).toBe("1 speech in the 18th Lok Sabha");
  });

  it("shows nothing without a member", () => {
    const { container } = renderMember(null);
    expect(container.innerHTML).toBe("");
  });
});

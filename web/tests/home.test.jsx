import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Home from "../pages/home.jsx";
import * as api from "../assets/js/api.js";
import homeAnswer from "./fixtures/home/home.json";
import featuredAnswer from "./fixtures/home/home_featured.json";
import methodAnswer from "./fixtures/method/method.json";

afterEach(cleanup);

// Answer each API address with its saved real answer.
function mockAnswers(overrides = {}) {
  const answers = { "/api/home": homeAnswer, "/api/home/featured": featuredAnswer, "/api/method": methodAnswer, ...overrides };
  return vi.spyOn(api, "getJSON").mockImplementation((path) => {
    const answer = answers[path];
    if (answer instanceof Error || (answer && answer.status)) return Promise.reject(answer);
    if (answer === undefined) return Promise.reject({ status: 404, message: "Not found" });
    return Promise.resolve(answer);
  });
}

function renderHome() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Home page", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the headline and the search box before any answer arrives", () => {
    vi.spyOn(api, "getJSON").mockReturnValue(new Promise(() => {}));
    renderHome();
    expect(screen.getByRole("heading", { level: 1, name: "Search what members said in the Lok Sabha" })).toBeTruthy();
    expect(screen.getByRole("search")).toBeTruthy();
    expect(screen.getAllByRole("status").length).toBeGreaterThan(0);
  });

  it("reads both answers of the Home page", async () => {
    const spy = mockAnswers();
    renderHome();
    await screen.findByText("64,921");
    const paths = spy.mock.calls.map((c) => c[0]);
    expect(paths).toContain("/api/home");
    expect(paths).toContain("/api/home/featured");
  });

  it("shows every site figure from corpus, with the error rate and no source line", async () => {
    mockAnswers();
    renderHome();
    expect(await screen.findByText("64,921")).toBeTruthy();
    expect(screen.getByText("2,062")).toBeTruthy();
    expect(screen.getByText("7,027")).toBeTruthy();
    expect(screen.getByText("0.24%")).toBeTruthy();
    expect(screen.getByText(/in 6 terms \(13th–18th Lok Sabha\)/)).toBeTruthy();
    expect(screen.queryByText(/No query computes it/)).toBeNull();
    expect(screen.getByText("20 Oct 1999")).toBeTruthy();
    expect(screen.getByText("18 Apr 2026")).toBeTruthy();
  });

  it("shows the real featured member, quote, trend and search ideas", async () => {
    mockAnswers();
    renderHome();
    expect(await screen.findByText("SUSHRI MAHUA MOITRA (KRISHNANAGAR)")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Krishnanagar" }).getAttribute("href")).toBe("/place/krishnanagar");
    expect(screen.getByText(/allocation-based scheme which the Central Government can alter at whim/)).toBeTruthy();
    expect(screen.getByText("3 of 13 tags of this speech")).toBeTruthy();
    expect(screen.getByText("205 speeches carry the tag Arrears in all years.")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Latur" }).getAttribute("href")).toBe("/place/latur");
  });

  it("shows the subjects that rose in the newest session, with a count for each", async () => {
    mockAnswers();
    renderHome();
    const first = homeAnswer.typical[0];
    const link = await screen.findByRole("link", { name: first.name });
    expect(link.getAttribute("href")).toBe(`/tag/${first.slug}`);
    expect(screen.getByRole("heading", { level: 2, name: "Subjects that rose in the newest session" })).toBeTruthy();
  });

  it("shows the steps of Torko with their counts, from the Method answer", async () => {
    mockAnswers();
    renderHome();
    const link = await screen.findByRole("link", { name: /turns read from the debates/ });
    expect(link.getAttribute("href")).toBe("/method#read");
  });

  it("keeps the text of the Method part when the Method answer fails", async () => {
    mockAnswers({ "/api/method": { status: 500, message: "The server could not answer. Try again." } });
    renderHome();
    await screen.findByText("SUSHRI MAHUA MOITRA (KRISHNANAGAR)");
    expect(screen.getByRole("link", { name: "Read how Torko works" })).toBeTruthy();
    expect(screen.queryByLabelText("The steps of Torko, with their counts")).toBeNull();
  });

  it("shows three blocks of a fixed size while the examples load", () => {
    vi.spyOn(api, "getJSON").mockReturnValue(new Promise(() => {}));
    const { container } = renderHome();
    expect(container.querySelectorAll(".home-skeleton__block")).toHaveLength(3);
  });

  it("keeps the search and the figures when the featured answer fails, and can retry it", async () => {
    const spy = mockAnswers({ "/api/home/featured": { status: 500, message: "The server could not answer. Try again." } });
    renderHome();
    expect(await screen.findByText("The server could not answer. Try again.")).toBeTruthy();
    expect(screen.getByText("64,921")).toBeTruthy();
    expect(screen.getByRole("search")).toBeTruthy();

    spy.mockImplementation((path) =>
      Promise.resolve(path === "/api/home" ? homeAnswer : featuredAnswer)
    );
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("SUSHRI MAHUA MOITRA (KRISHNANAGAR)")).toBeTruthy();
  });

  it("keeps the search and the featured parts when the site figures fail", async () => {
    mockAnswers({ "/api/home": { status: 500, message: "The server could not answer. Try again." } });
    renderHome();
    expect(await screen.findByText("SUSHRI MAHUA MOITRA (KRISHNANAGAR)")).toBeTruthy();
    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.queryByText("64,921")).toBeNull();
    expect(screen.getByRole("search")).toBeTruthy();
  });

  it("leaves out a featured part that the API omits", async () => {
    mockAnswers({ "/api/home/featured": { ...featuredAnswer, member: null, quote: null } });
    renderHome();
    expect(await screen.findByText("205 speeches carry the tag Arrears in all years.")).toBeTruthy();
    expect(screen.queryByText("Read every speech by one member.")).toBeNull();
    expect(screen.queryByText("Find speeches by subject.")).toBeNull();
  });

  it("has no link to a page that does not exist yet", async () => {
    mockAnswers();
    renderHome();
    await screen.findByText("SUSHRI MAHUA MOITRA (KRISHNANAGAR)");
    expect(screen.queryByText(/Start here/i)).toBeNull();
    const hrefs = screen.getAllByRole("link").map((a) => a.getAttribute("href"));
    for (const href of hrefs) {
      // The one outside link is the source page of the quote on sansad.in.
      expect(href).toMatch(/^(\/(member|place|speech|tag|my-mp|search|method)|https:\/\/sansad\.in\/)/);
    }
  });

  it("links to the Method page, also when the featured answer fails", async () => {
    mockAnswers({ "/api/home/featured": { status: 500, message: "The server could not answer. Try again." } });
    renderHome();
    await screen.findByText("The server could not answer. Try again.");
    expect(screen.getByRole("link", { name: "Read how Torko works" }).getAttribute("href")).toBe("/method");
  });

  it("uses no word that the writing rules ban", async () => {
    mockAnswers();
    const { container } = renderHome();
    await screen.findByText("SUSHRI MAHUA MOITRA (KRISHNANAGAR)");
    const text = container.textContent;
    expect(text).not.toMatch(/\b(AI|LLM|entity|item)\b/);
    expect(text).not.toMatch(/[;—]/);
  });
});

describe("ideaLabel", () => {
  it("shows the short form of a long name that ends in brackets", async () => {
    const { ideaLabel } = await import("../pages/home/HomeHero.jsx");
    expect(ideaLabel("Mahatma Gandhi National Rural Employment Guarantee Act (MNREGA)")).toBe("MNREGA");
    expect(ideaLabel("Minimum Support Prices (MSP)")).toBe("MSP");
    expect(ideaLabel("Gaya")).toBe("Gaya");
    expect(ideaLabel("Delhi (NCT)")).toBe("Delhi (NCT)");
  });
});

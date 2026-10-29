import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Home from "../pages/home.jsx";
import * as api from "../assets/js/api.js";
import homeAnswer from "./fixtures/home/home.json";
import featuredAnswer from "./fixtures/home/home_featured.json";

afterEach(cleanup);

// Answer each API address with its saved real answer.
function mockAnswers(overrides = {}) {
  const answers = { "/api/home": homeAnswer, "/api/home/featured": featuredAnswer, ...overrides };
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
    expect(screen.getByRole("heading", { level: 1, name: "Search what members said in the Lok Sabha." })).toBeTruthy();
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
    expect(screen.getByText("about 0.24%")).toBeTruthy();
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
      expect(href).toMatch(/^\/(member|place|speech|tag|search|method)/);
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

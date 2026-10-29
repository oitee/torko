import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Method from "../pages/method.jsx";
import * as api from "../assets/js/api.js";
import methodAnswer from "./fixtures/method/method.json";

afterEach(cleanup);

function renderMethod() {
  return render(
    <MemoryRouter initialEntries={["/method"]}>
      <Routes>
        <Route path="/method" element={<Method />} />
      </Routes>
    </MemoryRouter>
  );
}

const ANSWER = "Torko reads the Lok Sabha debates, finds who spoke each turn, and tags each speech with its subjects.";

describe("Method page", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the answer and the loading state before the answer arrives", () => {
    vi.spyOn(api, "getJSON").mockReturnValue(new Promise(() => {}));
    renderMethod();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(ANSWER);
    expect(screen.getByRole("status")).toBeTruthy();
  });

  it("reads /api/method", async () => {
    const spy = vi.spyOn(api, "getJSON").mockResolvedValue(methodAnswer);
    renderMethod();
    await screen.findByText("Read the debates");
    expect(spy).toHaveBeenCalledWith("/api/method");
  });

  it("shows the four steps in order", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValue(methodAnswer);
    renderMethod();
    await screen.findByText("Read the debates");
    expect(screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent)).toEqual([
      "Read the debates",
      "Find who spoke",
      "Join turns into speeches",
      "Give each speech its subjects",
      "What Torko gets wrong",
      "Sources",
    ]);
  });

  it("states each figure with its denominator, from the API", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValue(methodAnswer);
    const { container } = renderMethod();
    await screen.findByText("Read the debates");
    const text = container.textContent;
    expect(text).toContain("64,921 debates, 20 Oct 1999 to 18 Apr 2026 · 526,701 turns");
    // 526,701 turns less 172,482 turns of the chair and of many members at once.
    expect(text).toContain("248,051 of 354,219 turns of one speaker have a member name");
    expect(text).toContain("137,781 of 173,225 have a member");
    expect(text).toContain(
      "Of the 116,387 speeches of a member with 50 words or more, 109,726 have a TLDR and 107,481 have at least one tag"
    );
  });

  it("follows the API, not a number written into the page", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValue({
      ...methodAnswer,
      speeches: { ...methodAnswer.speeches, eligible: 200000 },
    });
    const { container } = renderMethod();
    await screen.findByText("Read the debates");
    expect(container.textContent).toContain("Of the 200,000 speeches");
  });

  it("links to the sources and the code", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValue(methodAnswer);
    renderMethod();
    await screen.findByText("Sources");
    expect(screen.getByRole("link", { name: "github.com/oitee/torko" }).getAttribute("href")).toBe(
      "https://github.com/oitee/torko"
    );
    expect(screen.getByRole("link", { name: "sansad.in" }).getAttribute("href")).toContain("sansad.in");
  });

  it("shows the error state and retries", async () => {
    const spy = vi.spyOn(api, "getJSON").mockRejectedValueOnce({ status: 500, message: "The server could not answer. Try again." });
    spy.mockResolvedValueOnce(methodAnswer);
    renderMethod();
    fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
    expect(await screen.findByText("Read the debates")).toBeTruthy();
  });

  it("uses no word that the writing rules ban", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValue(methodAnswer);
    const { container } = renderMethod();
    await screen.findByText("Read the debates");
    const text = container.textContent;
    expect(text).not.toMatch(/\b(AI|LLM|entity|item|Unattributed)\b/);
    expect(text).not.toMatch(/[;—]/);
  });
});

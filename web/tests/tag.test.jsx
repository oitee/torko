import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Tag from "../pages/tag.jsx";
import * as api from "../assets/js/api.js";

afterEach(cleanup);

const mockTagData = {
  name: "Arrears",
  slug: "arrears",
  type: "topic",
  domain: "Economy, Finance and Taxation",
  description: "Outstanding payments due.",
  total: 205,
  n_members: 145,
  n_subjects: 11,
  first: "1999-10-28",
  last: "2025-12-17",
  sessions: [
    { term: 13, year: 1999, n: 5 },
    { term: 16, year: 2014, n: 20 },
    { term: 17, year: 2019, n: 41 },
    { term: 17, year: 2020, n: 15 },
  ],
  parties: [
    { party: "BJP", n: 72, colour: "#FF9933" },
    { party: "INC", n: 35, colour: "#00BFFF" },
  ],
  members: [
    {
      id: 844,
      name: "Kunwar Danish Ali",
      party: "BSP",
      seat: "Amroha",
      first: "2019-07-29",
      last: "2022-08-05",
      n: 8,
      terms: [17],
    },
  ],
  recent: [
    {
      id: 178379,
      member: "Mahua Moitra",
      party: "AITC",
      seat: "Krishnanagar",
      date: "2025-12-17",
      debate: "Viksit Bharat Gurantee Bill",
      summary: "Opposes the proposed bill and argues it weakens legal guarantees.",
      quote: "The MGNREGA has been replaced by an allocation-based scheme.",
      quote_lang: "en",
      subject: null,
      words: 1962,
    },
  ],
  subjects: [
    { id: 23204, label: "Wage and salary arrears", speeches: 44, peak: 2001 },
  ],
  related: [
    { name: "Farmers", slug: "farmers", n: 70 },
  ],
};

function renderTagPage(initialRoute = "/tag/arrears") {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Routes>
        <Route path="/tag/:slug" element={<Tag />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Tag page integration", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows loading state while fetching and then renders page content", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce(mockTagData);

    renderTagPage();

    expect(screen.getByRole("status").textContent).toContain("Loading");

    await waitFor(() => {
      const heading = screen.getByRole("heading", { level: 1 });
      expect(heading.textContent).toBe("Arrears");
    });

    expect(document.title).toBe("Arrears · Torko");
    expect(screen.getByText("Topics")).toBeTruthy();
    expect(screen.getByText("Economy, Finance and Taxation")).toBeTruthy();
    expect(screen.getByText("Outstanding payments due.")).toBeTruthy();
    expect(screen.getByText("205")).toBeTruthy();
    expect(screen.getByText("145")).toBeTruthy();
    expect(screen.getByText("11")).toBeTruthy();
    expect(screen.getByText("1999–2025")).toBeTruthy();

    // Chart and member sections
    expect(screen.getByRole("heading", { name: "When" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "From which party" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Who spoke" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Speeches" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Subjects under this tag" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Related tags" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "How Torko counts" })).toBeTruthy();
  });

  it("handles 404 error with Page not found and document title", async () => {
    vi.spyOn(api, "getJSON").mockRejectedValueOnce({ status: 404, message: "Not found" });

    renderTagPage("/tag/no-such-tag");

    await waitFor(() => {
      expect(screen.getByText("Page not found")).toBeTruthy();
    });

    expect(document.title).toBe("Page not found · Torko");
  });

  it("handles network error with retry button", async () => {
    vi.spyOn(api, "getJSON")
      .mockRejectedValueOnce({ status: 500, message: "Network error" })
      .mockResolvedValueOnce(mockTagData);

    renderTagPage();

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeTruthy();
    });

    const retryBtn = screen.getByRole("button", { name: "Try again" });
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Arrears");
    });
  });

  it("switches term and calls API with term filter, keeping head visible", async () => {
    vi.spyOn(api, "getJSON")
      .mockResolvedValueOnce(mockTagData)
      .mockResolvedValueOnce({
        ...mockTagData,
        parties: [{ party: "BJP", n: 40, colour: "#FF9933" }],
      });

    renderTagPage();

    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Arrears");
    });

    const term17Btn = screen.getByRole("button", { name: "17th · 2019–24" });
    fireEvent.click(term17Btn);

    await waitFor(() => {
      expect(api.getJSON).toHaveBeenCalledWith("/api/tag/arrears", { term: "17" });
    });

    // Head stays on screen
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Arrears");
    // Meta count line appears under term bar: 41 + 15 = 56
    expect(
      screen.getByText("56 of 205 speeches in the 17th Lok Sabha")
    ).toBeTruthy();
  });
});

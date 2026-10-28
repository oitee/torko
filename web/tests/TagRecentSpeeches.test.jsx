import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import TagRecentSpeeches from "../pages/tag/TagRecentSpeeches.jsx";

afterEach(cleanup);

describe("TagRecentSpeeches component", () => {
  const mockSpeeches = [
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
      subject: "Fund release to states",
      words: 1962,
    },
    {
      id: 178378,
      member: "Naresh Chandra Patel",
      party: "SP",
      seat: "Fatehpur",
      date: "2025-12-17",
      debate: "Viksit Bharat Gurantee Bill",
      summary: null,
      quote: "मेरे जिले फतेहपुर में मोबाइल नेटवर्क नहीं है।",
      quote_lang: "hi",
      subject: null,
      words: 824,
    },
  ];

  it("renders speech cards with speaker, debate, TLDR, quotes, and primary action button", () => {
    render(
      <MemoryRouter>
        <TagRecentSpeeches
          speeches={mockSpeeches}
          slug="arrears"
          selectedTerm=""
        />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: "Speeches" })).toBeTruthy();
    expect(screen.getByText("latest · all terms")).toBeTruthy();

    expect(screen.getByText("Mahua Moitra")).toBeTruthy();
    expect(screen.getByText("· AITC · Krishnanagar")).toBeTruthy();
    expect(screen.getAllByText("17 Dec 2025").length).toBe(2);
    expect(screen.getAllByText("Viksit Bharat Gurantee Bill").length).toBe(2);
    expect(screen.getByText("TLDR")).toBeTruthy();
    expect(
      screen.getByText("Opposes the proposed bill and argues it weakens legal guarantees.")
    ).toBeTruthy();
    expect(
      screen.getByText("“The MGNREGA has been replaced by an allocation-based scheme.”")
    ).toBeTruthy();
    expect(screen.getByText("Fund release to states")).toBeTruthy();
    expect(screen.getByText("1,962 words")).toBeTruthy();

    // Hindi quote
    const hindiQuote = screen.getByText("“मेरे जिले फतेहपुर में मोबाइल नेटवर्क नहीं है।”");
    expect(hindiQuote.getAttribute("lang")).toBe("hi");

    // Action button
    const actionBtn = screen.getByRole("link", { name: "See all speeches" });
    expect(actionBtn.getAttribute("href")).toBe("/search?tag=arrears");
    expect(actionBtn.classList.contains("button--primary")).toBe(true);
  });
});

import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import DebateHead, {
  buildDebateCitation,
  formatDateWithWeekday,
} from "../pages/debate/DebateHead.jsx";

afterEach(cleanup);

describe("DebateHead", () => {
  const sampleDebate = {
    id: 683,
    title: "Viksit Bharat Gurantee Bill",
    term: 18,
    session: 6,
    session_label: "Winter 2025",
    date: "2025-12-17",
    kind_label: "Bill",
    laid: true,
    source_url: "https://sansad.in/debate/683",
  };

  it("computes weekday date using Date.UTC correctly", () => {
    // 2024-03-12 is a Tuesday
    expect(formatDateWithWeekday("2024-03-12")).toBe("Tuesday, 12 March 2024");
    // 2025-12-17 is a Wednesday
    expect(formatDateWithWeekday("2025-12-17")).toBe("Wednesday, 17 December 2025");
  });

  it("builds debate citation string correctly", () => {
    const cit = buildDebateCitation(sampleDebate);
    expect(cit).toBe(
      "Lok Sabha Debates, 17 Dec 2025. “Viksit Bharat Gurantee Bill”. 18th Lok Sabha, Winter 2025. Source: https://sansad.in/debate/683"
    );
  });

  it("renders breadcrumb, kicker, title, date, laid notice, and actions", () => {
    render(
      <MemoryRouter>
        <DebateHead debate={sampleDebate} />
      </MemoryRouter>
    );

    expect(screen.getByRole("navigation", { name: "Breadcrumb" })).toBeTruthy();
    expect(screen.getByText("18th Lok Sabha")).toBeTruthy();
    expect(screen.getByText("Winter 2025")).toBeTruthy();
    expect(screen.getByText("17 Dec 2025")).toBeTruthy();

    expect(screen.getByText("Bill")).toBeTruthy();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
      "Viksit Bharat Gurantee Bill"
    );
    expect(screen.getByText("Wednesday, 17 December 2025")).toBeTruthy();
    expect(
      screen.getByText("Laid on the table. The text was not read aloud.")
    ).toBeTruthy();

    const originalBtn = screen.getByRole("link", {
      name: "Read the original on sansad.in",
    });
    expect(originalBtn.getAttribute("href")).toBe(
      "https://sansad.in/debate/683"
    );

    const citeBtn = screen.getByRole("button", { name: "Cite this debate" });
    expect(citeBtn).toBeTruthy();
    fireEvent.click(citeBtn);

    expect(
      screen.getByText(
        "Cite the record on sansad.in. Torko is the place you found it."
      )
    ).toBeTruthy();
  });
});

describe("DebateHead title", () => {
  it("has no title button when the title fits", () => {
    render(
      <MemoryRouter>
        <DebateHead debate={{ title: "Short title", date: "2024-03-12", term: 17, session: 3 }} />
      </MemoryRouter>
    );
    expect(screen.queryByRole("button", { name: "Show full title" })).toBeNull();
  });
});

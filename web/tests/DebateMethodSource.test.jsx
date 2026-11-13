import React from "react";
import { describe, it, expect, afterEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import DebateMethodSource from "../pages/debate/DebateMethodSource.jsx";

afterEach(cleanup);

describe("DebateMethodSource", () => {
  it("links to the Method page and renders Source metadata", () => {
    render(
      <MemoryRouter>
        <DebateMethodSource
          term={17}
          session_label="Winter 2025"
          date="2024-03-12"
          source_url="https://sansad.in/ls/debates/2024-03-12/58204"
        />
      </MemoryRouter>
    );

    // One link to the Method page, in place of the rules
    expect(screen.getByRole("link", { name: "How counts work" }).getAttribute("href")).toBe("/method");

    // Source block
    expect(screen.getByText("Source")).toBeTruthy();
    expect(screen.getByText("Lok Sabha Debates, 17th Lok Sabha, Winter 2025")).toBeTruthy();
    expect(screen.getByText("2024-03-12")).toBeTruthy();

    // Source link stripped of https://
    const link = screen.getByRole("link", { name: "sansad.in/ls/debates/2024-03-12/58204" });
    expect(link).toBeTruthy();
    expect(link.getAttribute("href")).toBe("https://sansad.in/ls/debates/2024-03-12/58204");

    // TLDR rule
    expect(screen.getByText("Cite the speech, not the TLDR.")).toBeTruthy();
  });

  it("handles missing source_url and session_label gracefully", () => {
    render(<MemoryRouter><DebateMethodSource term={18} date="2024-07-01" /></MemoryRouter>);

    expect(screen.getByText("Lok Sabha Debates, 18th Lok Sabha")).toBeTruthy();
    expect(screen.getByText("Not given")).toBeTruthy();
  });
});

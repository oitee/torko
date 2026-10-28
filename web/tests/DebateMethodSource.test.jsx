import React from "react";
import { describe, it, expect, afterEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import DebateMethodSource from "../pages/debate/DebateMethodSource.jsx";

afterEach(cleanup);

describe("DebateMethodSource", () => {
  it("renders How Torko counts and Source metadata", () => {
    render(
      <DebateMethodSource
        term={17}
        session_label="Winter 2025"
        date="2024-03-12"
        source_url="https://sansad.in/ls/debates/2024-03-12/58204"
      />
    );

    // How Torko counts title and items
    expect(screen.getByText("How Torko counts")).toBeTruthy();
    expect(screen.getByText("Speech.")).toBeTruthy();
    expect(screen.getByText("Interruption.")).toBeTruthy();
    expect(screen.getByText("TLDR.")).toBeTruthy();
    expect(screen.getByText("Filters.")).toBeTruthy();
    expect(screen.getByText("No member.")).toBeTruthy();

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
    render(<DebateMethodSource term={18} date="2024-07-01" />);

    expect(screen.getByText("Lok Sabha Debates, 18th Lok Sabha")).toBeTruthy();
    expect(screen.getByText("Not given")).toBeTruthy();
  });
});

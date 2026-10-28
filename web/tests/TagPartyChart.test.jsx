import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import TagPartyChart from "../pages/tag/TagPartyChart.jsx";

afterEach(cleanup);

describe("TagPartyChart component", () => {
  const mockParties = [
    { party: "BJP", n: 72, colour: "#FF9933" },
    { party: "INC", n: 35, colour: "#00BFFF" },
    { party: "CPI(M)", n: 18, colour: "#CC0D0D" },
  ];

  it("renders party chart heading, total speeches meta line, bars, and note", () => {
    render(
      <MemoryRouter>
        <TagPartyChart parties={mockParties} selectedTerm="17" />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: "From which party" })).toBeTruthy();
    // 72 + 35 + 18 = 125
    expect(screen.getByText("125 speeches · 17th Lok Sabha")).toBeTruthy();
    expect(screen.getAllByText("BJP").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("INC").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("CPI(M)").length).toBeGreaterThanOrEqual(1);

    expect(
      screen.getByText(
        "Party is the member's party on the day of the speech. Parties after the largest 6 are counted in Others, in grey."
      )
    ).toBeTruthy();
  });
});

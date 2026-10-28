import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import MemberLine from "../components/MemberLine.jsx";

afterEach(cleanup);

describe("MemberLine component", () => {
  it("renders member name as an h2 heading", () => {
    const member = {
      name: "Mahua Moitra",
      terms: [],
    };

    render(<MemberLine member={member} />);

    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading).toBeTruthy();
    expect(heading.textContent).toBe("Mahua Moitra");
  });

  it("formats term rows with termShort, seat, parties, and speeches count", () => {
    const member = {
      name: "Mahua Moitra",
      terms: [
        {
          term: 17,
          seat: "Krishnanagar",
          state: "West Bengal",
          parties: ["AITC"],
          speeches: 51,
        },
        {
          term: 18,
          seat: "Krishnanagar",
          state: "West Bengal",
          parties: ["AITC"],
          speeches: 15,
        },
      ],
    };

    render(<MemberLine member={member} />);

    expect(
      screen.getByText("17th LS · Krishnanagar · AITC · 51 speeches")
    ).toBeTruthy();
    expect(
      screen.getByText("18th LS · Krishnanagar · AITC · 15 speeches")
    ).toBeTruthy();
  });

  it("joins multiple parties with comma and space", () => {
    const member = {
      name: "Sample MP",
      terms: [
        {
          term: 16,
          seat: "Varanasi",
          parties: ["BJP", "NDA"],
          speeches: 100,
        },
      ],
    };

    render(<MemberLine member={member} />);

    expect(
      screen.getByText("16th LS · Varanasi · BJP, NDA · 100 speeches")
    ).toBeTruthy();
  });

  it("omits missing parts cleanly without double dots", () => {
    const member = {
      name: "Nominated Member",
      terms: [
        {
          term: 17,
          // seat missing
          parties: ["IND"],
          speeches: 12,
        },
        {
          term: 18,
          seat: "South Delhi",
          // parties missing
          speeches: 0,
        },
        {
          term: 16,
          seat: "Amethi",
          parties: ["INC"],
          // speeches missing
        },
      ],
    };

    render(<MemberLine member={member} />);

    const row1 = screen.getByText("17th LS · IND · 12 speeches");
    expect(row1).toBeTruthy();
    expect(row1.textContent).not.toContain("· ·");

    const row2 = screen.getByText("18th LS · South Delhi · 0 speeches");
    expect(row2).toBeTruthy();
    expect(row2.textContent).not.toContain("· ·");

    const row3 = screen.getByText("16th LS · Amethi · INC");
    expect(row3).toBeTruthy();
    expect(row3.textContent).not.toContain("· ·");
  });

  it("handles null, undefined, and empty data gracefully", () => {
    const { container: emptyContainer } = render(<MemberLine member={null} />);
    expect(emptyContainer.firstChild).toBeNull();

    const { container: noTermsContainer } = render(
      <MemberLine member={{ name: "Ghost MP" }} />
    );
    expect(screen.getByRole("heading", { level: 2 }).textContent).toBe(
      "Ghost MP"
    );
    expect(noTermsContainer.querySelectorAll("li").length).toBe(0);
  });
});

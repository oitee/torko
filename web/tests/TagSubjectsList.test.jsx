import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import TagSubjectsList from "../pages/tag/TagSubjectsList.jsx";

afterEach(cleanup);

describe("TagSubjectsList component", () => {
  const mockSubjects = [
    { id: 23204, label: "Wage and salary arrears", speeches: 44, peak: 2001 },
    { id: 25731, label: "Agricultural dues", speeches: 13, peak: 2002 },
  ];

  it("renders subjects heading, cards, speech counts, and peak years", () => {
    render(<TagSubjectsList subjects={mockSubjects} />);

    expect(screen.getByRole("heading", { name: "Subjects under this tag" })).toBeTruthy();
    expect(
      screen.getByText("The specific things members raised. Across all terms.")
    ).toBeTruthy();

    expect(screen.getByText("Wage and salary arrears")).toBeTruthy();
    expect(screen.getByText("44 speeches")).toBeTruthy();
    expect(screen.getByText("peak 2001")).toBeTruthy();

    expect(screen.getByText("Agricultural dues")).toBeTruthy();
    expect(screen.getByText("13 speeches")).toBeTruthy();
    expect(screen.getByText("peak 2002")).toBeTruthy();
  });

  it("returns null when subjects array is empty", () => {
    const { container } = render(<TagSubjectsList subjects={[]} />);
    expect(container.firstChild).toBeNull();
  });
});

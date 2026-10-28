import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import TagHead, { formatSpan } from "../pages/tag/TagHead.jsx";

afterEach(cleanup);

describe("TagHead component", () => {
  it("formats date span correctly", () => {
    expect(formatSpan("1999-10-28", "2025-12-17")).toBe("1999–2025");
    expect(formatSpan("2024-01-01", "2024-11-20")).toBe("2024");
    expect(formatSpan("2019-05-15", null)).toBe("2019");
    expect(formatSpan(null, null)).toBeNull();
  });

  it("renders kicker, tag name, description, and four summary counts", () => {
    const mockTag = {
      name: "Rural employment",
      description: "Speeches on work schemes in villages.",
      total: 2773,
      n_members: 611,
      n_subjects: 21,
      first: "2004-05-10",
      last: "2025-12-17",
    };

    render(<TagHead tag={mockTag} />);

    expect(screen.getByText("Tag")).toBeTruthy();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Rural employment");
    expect(screen.getByText("Speeches on work schemes in villages.")).toBeTruthy();
    expect(screen.getByText("2,773")).toBeTruthy();
    expect(screen.getByText("speeches")).toBeTruthy();
    expect(screen.getByText("611")).toBeTruthy();
    expect(screen.getByText("members spoke")).toBeTruthy();
    expect(screen.getByText("21")).toBeTruthy();
    expect(screen.getByText("subjects under this tag")).toBeTruthy();
    expect(screen.getByText("2004–2025")).toBeTruthy();
    expect(screen.getByText("first and latest speech")).toBeTruthy();
  });

  it("omits missing counts gracefully", () => {
    const sparseTag = {
      name: "Sparse Tag",
      total: 10,
      first: "2020-01-01",
    };

    render(<TagHead tag={sparseTag} />);

    expect(screen.getByText("10")).toBeTruthy();
    expect(screen.queryByText("members spoke")).toBeNull();
    expect(screen.queryByText("subjects under this tag")).toBeNull();
  });
});

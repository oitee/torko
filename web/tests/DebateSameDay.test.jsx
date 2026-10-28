import React from "react";
import { describe, it, expect, afterEach } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import DebateSameDay from "../pages/debate/DebateSameDay.jsx";

afterEach(cleanup);

describe("DebateSameDay", () => {
  const mockSameDay = [
    {
      id: 101,
      title: "Zero Hour Discussions",
      kind_label: "Zero Hour",
      speeches: 27,
    },
    {
      id: 102,
      title: "Papers Laid on the Table",
      kind_label: "Papers",
      speeches: 0,
    },
    {
      id: 103,
      title: "Special Mention",
      kind_label: "Other",
      speeches: 1,
    },
  ];

  it("renders the list of same day debates with correct counts and links", () => {
    render(
      <MemoryRouter>
        <DebateSameDay sameDay={mockSameDay} date="2024-03-12" />
      </MemoryRouter>
    );

    expect(screen.getByText(/Other debates on\s+12 Mar 2024/)).toBeTruthy();

    const link1 = screen.getByRole("link", { name: "Zero Hour Discussions" });
    expect(link1).toBeTruthy();
    expect(link1.getAttribute("href")).toBe("/debate/101");
    expect(screen.getByText("27 speeches")).toBeTruthy();

    const link2 = screen.getByRole("link", { name: "Papers Laid on the Table" });
    expect(link2).toBeTruthy();
    expect(screen.getByText("no speeches")).toBeTruthy();

    const link3 = screen.getByRole("link", { name: "Special Mention" });
    expect(link3).toBeTruthy();
    expect(screen.getByText("1 speech")).toBeTruthy();
  });

  it("returns null when sameDay is empty or missing", () => {
    const { container: c1 } = render(
      <MemoryRouter>
        <DebateSameDay sameDay={[]} date="2024-03-12" />
      </MemoryRouter>
    );
    expect(c1.firstChild).toBeNull();

    const { container: c2 } = render(
      <MemoryRouter>
        <DebateSameDay date="2024-03-12" />
      </MemoryRouter>
    );
    expect(c2.firstChild).toBeNull();
  });
});

describe("DebateSameDay with a long list", () => {
  it("shows the first 5 debates and a button for all of them", () => {
    const many = Array.from({ length: 8 }, (_, i) => ({
      id: 200 + i,
      title: `Debate ${i + 1}`,
      kind_label: "Other",
      speeches: 1,
    }));
    render(
      <MemoryRouter>
        <DebateSameDay sameDay={many} date="2024-03-12" />
      </MemoryRouter>
    );
    expect(screen.getAllByRole("link")).toHaveLength(5);
    fireEvent.click(screen.getByRole("button", { name: "Show all 8 debates" }));
    expect(screen.getAllByRole("link")).toHaveLength(8);
  });
});

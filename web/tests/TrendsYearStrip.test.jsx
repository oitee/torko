import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import YearStrip from "../pages/trends/YearStrip.jsx";

afterEach(cleanup);

const subject = (name) => ({ name, slug: name.toLowerCase(), type: "topic", n: 30, share: 3, typical: 0.5 });

describe("YearStrip", () => {
  it("lists the latest year first, also when the API sends the oldest year first", () => {
    const years = [
      { year: 2001, tagged: 3000, subjects: [subject("Old")] },
      { year: 2002, tagged: 3000, subjects: [subject("Middle")] },
      { year: 2003, tagged: 3000, subjects: [subject("New")] },
    ];
    const { container } = render(<MemoryRouter><YearStrip years={years} slugs={[]} onAdd={() => {}} lastDate="1 May 2003" /></MemoryRouter>);
    const order = [...container.querySelectorAll(".year-strip__number")].map((e) => e.textContent);
    expect(order).toEqual(["2003", "2002", "2001"]);
    expect(screen.getAllByText(/3,000 tagged speeches/).length).toBe(3);
    expect(screen.getByText(/Part year: 1 Jan to 1 May 2003 only/)).toBeTruthy();
  });
});


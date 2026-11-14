import React from "react";
import { MemoryRouter } from "react-router-dom";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { BillMembers, BillParties, BillSamples, countText, dateRange } from "../pages/bill.jsx";

afterEach(cleanup);

const bill = {
  members: 6,
  speeches: 9,
  member_counts: { for: 3, against: 2, mixed: 0, unclear: 1 },
  parties: [
    { party: "BJP", members: 4, counts: { for: 3, against: 0, mixed: 0, unclear: 1 } },
    { party: "Others", members: 2, no_party: 1, counts: { for: 0, against: 2, mixed: 0, unclear: 0 } },
  ],
  samples: [{ id: 11, member_id: 5, member: "Member One", party: "BJP", seat: "Seat", date: "2026-04-17", stance: "for", summary: "Supports the bill." }],
};

const wrap = (ui) => render(<MemoryRouter>{ui}</MemoryRouter>);

describe("Bill page parts", () => {
  it("writes counts with no empty stance", () => {
    expect(countText({ for: 3, against: 0, mixed: 0, unclear: 1 })).toBe("3 for, 1 not clear");
  });

  it("writes one date or a range", () => {
    expect(dateRange("2026-04-16", "2026-04-16")).not.toContain(" to ");
    expect(dateRange("2026-04-16", "2026-04-17")).toContain(" to ");
  });

  it("shows the member counts", () => {
    wrap(<BillMembers bill={bill} />);
    expect(screen.getByText(/6 members spoke on this bill/)).toBeTruthy();
    expect(screen.getByText("not clear")).toBeTruthy();
  });

  it("shows party rows and the no-party note", () => {
    wrap(<BillParties bill={bill} />);
    expect(screen.getByRole("link", { name: "BJP" })).toBeTruthy();
    expect(screen.getByText("3 for, 1 not clear")).toBeTruthy();
    expect(screen.getByText(/1 member has no party in the data and is in Others/)).toBeTruthy();
  });

  it("shows sample speeches and the read-all button", () => {
    wrap(<BillSamples bill={{ ...bill, id: 4644 }} />);
    expect(screen.getByRole("link", { name: "Member One" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "For" })).toBeTruthy();
    const all = screen.getByRole("link", { name: "Read all 9 speeches on this bill" });
    expect(all.getAttribute("href")).toBe("/search?bill=4644&sort=oldest");
  });
});

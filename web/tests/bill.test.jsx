import React from "react";
import { MemoryRouter } from "react-router-dom";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { fireEvent } from "@testing-library/react";
import { BillAllSpeeches, BillMembers, BillParties, BillReasons, BillSamples, readAllText, reasonCount, SameNameCallout, countText, dateRange } from "../pages/bill.jsx";

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
    expect(screen.getByText(/Stance of a member is derived from the text of their speech/)).toBeTruthy();
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
  it("links a bill of the same name in another term", () => {
    wrap(<SameNameCallout bill={{ same_name: [{ id: 9456, name: "Citizenship (Amendment) Bill", year: 2019, term: 16, side: "previous" }] }} />);
    expect(screen.getByText(/A different bill with the same name was debated in the 16th Lok Sabha/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Read it here" }).getAttribute("href")).toBe("/bill/9456");
  });

  it("shows no callout when no bill shares the name", () => {
    const { container } = wrap(<SameNameCallout bill={{ same_name: [] }} />);
    expect(container.textContent).toBe("");
  });

  it("writes the count of a reason", () => {
    expect(reasonCount({ members: 9, points: 12 })).toBe("9 members");
    expect(reasonCount({ members: 1, points: 3 })).toBe("1 member");
    expect(reasonCount({ members: 0, points: 1 })).toBe("Speaker not identified");
  });

  it("shows the first reasons of each side and the rest on a click", () => {
    const reason = (id, members) => ({ id, label: `Reason ${id}`, members, points: members,
      quotes: [{ member_id: 5, member: "Member One", party: "BJP", speech_id: 11, quote: `Quote ${id}` }] });
    const reasons = { for: [1, 2, 3].map((i) => reason(i, 4 - i)), against: [reason(9, 2)] };
    wrap(<BillReasons bill={{ reasons, top_reasons: 2, reason_rule: "Rule." }} />);
    expect(screen.getByRole("heading", { name: "Reasons for the bill" })).toBeTruthy();
    expect(screen.queryByText("Reason 3")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Show all 3 reasons" }));
    expect(screen.getByText("Reason 3")).toBeTruthy();
    expect(screen.getByText("Quote 9")).toBeTruthy();
    expect(screen.getAllByRole("link", { name: "Read the speech" })[0].getAttribute("href")).toBe("/speech/11");
  });

  it("shows the points of one member in one last row, after all the reasons", () => {
    const quote = (id) => [{ member_id: 5, member: "Member One", party: "BJP", speech_id: 11, quote: `Quote ${id}` }];
    const reasons = { for: [1, 2, 3].map((i) => ({ id: i, label: `Reason ${i}`, members: 5 - i, points: 5 - i, quotes: quote(i) })) };
    const reason_others = { for: [7, 8].map((i) => ({ id: i, label: `Point ${i}`, members: 1, points: 1, quotes: quote(i) })) };
    wrap(<BillReasons bill={{ reasons, reason_others, top_reasons: 2, reason_rule: "Rule." }} />);
    expect(screen.queryByText("Points supported by a single member")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Show all 3 reasons" }));
    expect(screen.getByText("Points supported by a single member")).toBeTruthy();
    expect(screen.getByText("2 reasons")).toBeTruthy();
    expect(screen.getByText("Point 7")).toBeTruthy();
    expect(screen.getByText("Quote 8")).toBeTruthy();
  });

  it("lists every speech of a small bill with its stance", () => {
    const samples = [{ ...bill.samples[0] }, { ...bill.samples[0], id: 12, stance: "unclear", member: "Member Two", member_id: 6 }];
    wrap(<BillAllSpeeches bill={{ samples, small_bill_members: 5 }} />);
    expect(screen.getByRole("heading", { name: "The speeches" })).toBeTruthy();
    expect(screen.getByText(/Fewer than 5 members spoke on this bill/)).toBeTruthy();
    expect(screen.getByText(/For · BJP/)).toBeTruthy();
    expect(screen.getByText(/Not clear · BJP/)).toBeTruthy();
  });

  it("names one speech in the singular", () => {
    wrap(<BillAllSpeeches bill={{ samples: bill.samples, small_bill_members: 5 }} />);
    expect(screen.getByRole("heading", { name: "The speech" })).toBeTruthy();
    expect(readAllText(1)).toBe("Read the speech on this bill");
    expect(readAllText(1200)).toBe("Read all 1,200 speeches on this bill");
  });

  it("shows no reasons section when the bill has no reasons", () => {
    const { container } = wrap(<BillReasons bill={{ reasons: { for: [], against: [] } }} />);
    expect(container.textContent).toBe("");
  });
});

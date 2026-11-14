import { describe, expect, it } from "vitest";
import { againstShare, filterBills, matchBills } from "../pages/bills.jsx";

const counts = (f, a) => ({ for: f, against: a, mixed: 0, unclear: 0 });
const bills = [
  { id: 1, name: "Citizenship (Amendment) Bill", year: 2019, members: 71, term: 17, amendment: false, tags: [0], counts: counts(30, 41) },
  { id: 2, name: "Constitution (One Hundred and Third Amendment) Bill", year: 2019, members: 40, term: 17, amendment: true, tags: [1], counts: counts(38, 2) },
  { id: 3, name: "Finance Bill", year: 2004, members: 20, term: 14, amendment: false, tags: [], counts: counts(10, 0) },
];

describe("Bills landing rules", () => {
  it("finds a bill by the start of each word, most members first", () => {
    expect(matchBills(bills, "citiz amend").map((b) => b.id)).toEqual([1]);
    expect(matchBills(bills, "2019").map((b) => b.id)).toEqual([1, 2]);
    expect(matchBills(bills, "  ")).toEqual([]);
  });

  it("filters by amendment, tag and term", () => {
    expect(filterBills(bills, { amendment: true }).map((b) => b.id)).toEqual([2]);
    expect(filterBills(bills, { tag: 0 }).map((b) => b.id)).toEqual([1]);
    expect(filterBills(bills, { term: 14 }).map((b) => b.id)).toEqual([3]);
  });

  it("gives the share against over the members", () => {
    expect(againstShare(bills[0])).toBeCloseTo(41 / 71);
  });
});

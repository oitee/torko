import { describe, expect, it } from "vitest";
import { topSubjectByCount } from "../pages/member/MemberHead.jsx";

describe("topSubjectByCount", () => {
  it("puts a topic, law or scheme before a tag that only names a body, from the data of Mahua Moitra", () => {
    const typical = [
      { name: "Right to Privacy", type: "law", n: 4, lift_terms: 33.5 },
      { name: "All India Trinamool Congress", type: "institution", n: 5, lift_terms: 53.5 },
      { name: "Data Protection", type: "law", n: 4, lift_terms: 15.1 },
    ];
    expect(topSubjectByCount(typical).name).toBe("Right to Privacy");
  });

  it("uses a naming tag when the member has no other tag", () => {
    expect(topSubjectByCount([{ name: "Kerala", type: "place", n: 2 }]).name).toBe("Kerala");
  });
});

import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import AroundSpeech from "../pages/speech/AroundSpeech.jsx";

afterEach(cleanup);

describe("AroundSpeech", () => {
  it("lists the turns before, the speech itself, and the turns after, with a link to the debate", () => {
    const before = [{ seq: 12, attributed: true, member: "Member A", member_id: 1, text: "Before text" }];
    const current = { seq: 13, attributed: true, member: "Member B", member_id: 2, text: "Own text", own: true };
    const after = [{ seq: 14, attributed: false, role_kind: "presiding", text: "After text" }];
    const { container } = render(
      <MemoryRouter>
        <AroundSpeech before={before} after={after} current={current} debateId={683} />
      </MemoryRouter>
    );

    const rows = [...container.querySelectorAll(".around-speech__row")];
    expect(rows.map((r) => r.querySelector(".around-speech__seq").textContent)).toEqual(["12", "13", "14"]);
    expect(rows[1].getAttribute("aria-current")).toBe("true");
    expect(rows[1].textContent).toContain("this speech");
    expect(rows[2].textContent).toContain("The Chair");
    expect(screen.getByRole("link", { name: "Read the whole debate" }).getAttribute("href")).toBe("/debate/683");
  });
});

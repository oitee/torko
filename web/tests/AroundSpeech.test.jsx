import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import AroundSpeech from "../pages/speech/AroundSpeech.jsx";

afterEach(cleanup);

describe("AroundSpeech", () => {
  it("links the words of a turn to its speech, except the current speech and a turn with no speech", () => {
    const before = [{ seq: 1, attributed: true, member: "A", member_id: 1, text: "Before words", speech_id: 7 }];
    const current = { seq: 2, attributed: true, member: "B", member_id: 2, text: "Own words", speech_id: 8, own: true };
    const after = [{ seq: 3, role_kind: "presiding", text: "Chair words", speech_id: null }];
    render(<MemoryRouter><AroundSpeech before={before} after={after} current={current} debateId={1} /></MemoryRouter>);
    expect(screen.getByRole("link", { name: "Before words" }).getAttribute("href")).toBe("/speech/7");
    expect(screen.queryByRole("link", { name: "Own words" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Chair words" })).toBeNull();
  });

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

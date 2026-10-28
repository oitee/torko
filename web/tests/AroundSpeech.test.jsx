import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import AroundSpeech from "../pages/speech/AroundSpeech.jsx";

afterEach(cleanup);

describe("AroundSpeech", () => {
  const beforeTurns = [
    {
      seq: 34,
      attributed: true,
      member: "Prior Speaker",
      member_id: 111,
      text: "This is a short turn before the speech.",
    },
  ];

  const afterTurns = [
    {
      seq: 40,
      role_kind: "presiding",
      text: "Now Shrimati Kanimozhi Karunanidhi will speak. A longer text that will definitely exceed one hundred and twenty characters in length so that we can verify whether truncation with an ellipsis works properly.",
    },
  ];

  it("renders heading, before turns, current marker, after turns and debate link", () => {
    render(
      <MemoryRouter>
        <AroundSpeech before={beforeTurns} after={afterTurns} debateId={683} />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: "Around this speech" })).toBeTruthy();

    const priorLink = screen.getByRole("link", { name: "Prior Speaker" });
    expect(priorLink).toBeTruthy();
    expect(priorLink.getAttribute("href")).toBe("/member/111");
    expect(screen.getByText("This is a short turn before the speech.")).toBeTruthy();

    expect(screen.getByText("This speech")).toBeTruthy();

    expect(screen.getByText("The Chair")).toBeTruthy();
    const truncated = screen.getByText(/Now Shrimati Kanimozhi Karunanidhi will speak\..*…/);
    expect(truncated).toBeTruthy();

    const debateLink = screen.getByRole("link", { name: "Read the whole debate" });
    expect(debateLink).toBeTruthy();
    expect(debateLink.getAttribute("href")).toBe("/debate/683");
  });
});

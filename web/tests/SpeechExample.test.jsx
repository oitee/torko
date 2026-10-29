import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SpeechExample from "../pages/method/SpeechExample.jsx";

afterEach(cleanup);

// The shape of /api/method → examples.speech.
const EXAMPLE = {
  speech_id: 9,
  member_id: 3,
  member: "Member A",
  date: "2024-07-01",
  words: 140,
  turns: [
    { seq: 1, own: true, speaker: "Member A", words: 60, text: "First part of the speech." },
    { seq: 2, own: false, speaker: "Member B", words: 6, text: "That is not correct." },
    { seq: 3, own: false, speaker: "The Chair", words: 4, text: "Please let her speak." },
    { seq: 4, own: true, speaker: "Member A", words: 70, text: "Second part of the speech." },
  ],
};

function renderSpeech(example) {
  return render(
    <MemoryRouter>
      <SpeechExample example={example} />
    </MemoryRouter>
  );
}

describe("SpeechExample", () => {
  it("shows every turn with its speaker and its words, and sets the interruptions in", () => {
    const { container } = renderSpeech(EXAMPLE);
    expect(screen.getAllByRole("listitem")).toHaveLength(4);
    expect(container.querySelectorAll(".speech-example__turn--other")).toHaveLength(2);
    expect(screen.getByText("That is not correct.")).toBeTruthy();
    expect(screen.getByText("· 6 words")).toBeTruthy();
  });

  it("states the result: the turns and interruptions that become one speech", () => {
    const { container } = renderSpeech(EXAMPLE);
    expect(container.querySelector(".speech-example__result").textContent).toBe(
      "2 turns of Member A and 2 interruptions become one speech of 140 words."
    );
    expect(screen.getByRole("link", { name: "one speech of 140 words" }).getAttribute("href")).toBe("/speech/9");
  });

  it("shows nothing without turns", () => {
    expect(renderSpeech(null).container.innerHTML).toBe("");
  });
});

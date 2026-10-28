import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SpeechText, { splitParagraphs } from "../pages/speech/SpeechText.jsx";

afterEach(cleanup);

describe("SpeechText", () => {
  it("splits paragraphs across blank lines preserving offsets", () => {
    const text = "First paragraph.\n\nSecond paragraph.";
    const paras = splitParagraphs(text);
    expect(paras).toHaveLength(2);
    expect(paras[0].text).toBe("First paragraph.");
    expect(paras[0].start).toBe(0);
    expect(paras[1].text).toBe("Second paragraph.");
    expect(paras[1].start).toBe(18);
  });

  it("renders own turn with paragraph numbers ¶1, ¶2 across whole speech", () => {
    const turns = [
      {
        seq: 1,
        own: true,
        text: "Paragraph one.\n\nParagraph two.",
      },
      {
        seq: 2,
        own: false,
        role_kind: "presiding",
        text: "Please conclude.",
      },
      {
        seq: 3,
        own: true,
        text: "Paragraph three.",
      },
    ];

    render(
      <MemoryRouter>
        <SpeechText turns={turns} hasMember={true} />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: "The speech" })).toBeTruthy();
    expect(screen.getByText("¶1")).toBeTruthy();
    expect(screen.getByText("¶2")).toBeTruthy();
    expect(screen.getByText("¶3")).toBeTruthy();
  });

  it("renders interruption with The Chair when role_kind is presiding", () => {
    const turns = [
      {
        seq: 1,
        own: false,
        role_kind: "presiding",
        text: "Order in the House.",
      },
    ];

    render(
      <MemoryRouter>
        <SpeechText turns={turns} hasMember={true} />
      </MemoryRouter>
    );

    expect(screen.getByText("The Chair")).toBeTruthy();
    expect(screen.getByText("· interruption")).toBeTruthy();
    expect(screen.getByText("Order in the House.")).toBeTruthy();
  });

  it("renders interruption with member link when attributed", () => {
    const turns = [
      {
        seq: 1,
        own: false,
        attributed: true,
        member: "Other Member",
        member_id: 456,
        text: "An interruption remark.",
      },
    ];

    render(
      <MemoryRouter>
        <SpeechText turns={turns} hasMember={true} />
      </MemoryRouter>
    );

    const link = screen.getByRole("link", { name: "Other Member" });
    expect(link).toBeTruthy();
    expect(link.getAttribute("href")).toBe("/member/456");
  });

  it("renders unidentified speaker banner and treats every turn as own for speech with no member", () => {
    const turns = [
      {
        seq: 1,
        own: false,
        label: "SHRI UNKNOWN",
        text: "Some speech words from unidentified speaker.",
      },
    ];

    render(
      <MemoryRouter>
        <SpeechText turns={turns} hasMember={false} />
      </MemoryRouter>
    );

    expect(screen.getByText("Speaker not identified")).toBeTruthy();
    expect(
      screen.getByText(
        "Speaker not identified. Torko could not match this name to one member."
      )
    ).toBeTruthy();
    expect(screen.queryByText("SHRI UNKNOWN")).toBeNull();
    expect(screen.getByText("¶1")).toBeTruthy();
  });

  it("marks exact ranges in paragraphs when activeMarks are supplied", () => {
    const turns = [
      {
        seq: 10,
        own: true,
        text: "We demand rural employment guarantee for all workers.",
      },
    ];
    // "rural employment guarantee" is from index 10 to 36
    const marks = [{ seq: 10, start: 10, end: 36 }];

    const { container } = render(
      <MemoryRouter>
        <SpeechText turns={turns} hasMember={true} activeMarks={marks} />
      </MemoryRouter>
    );

    const markEl = container.querySelector("mark");
    expect(markEl).toBeTruthy();
    expect(markEl.textContent).toBe("rural employment guarantee");
    expect(markEl.getAttribute("id")).toBe("first-speech-mark");
  });
});

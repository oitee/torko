import React from "react";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SpeechText, { paragraphIdFromHash, splitParagraphs } from "../pages/speech/SpeechText.jsx";

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

describe("SpeechText paragraph links and copy with source", () => {
  const turns = [{ seq: 1, own: true, text: "Paragraph one.\n\nParagraph two." }];
  const speaker = { id: 178379, member: "Mahua Moitra", party: "AITC", seat: "Krishnanagar", date: "2025-12-17" };

  it("reads a paragraph id only from a hash such as #p7", () => {
    expect(paragraphIdFromHash("#p7")).toBe("p7");
    expect(paragraphIdFromHash("p12")).toBe("p12");
    expect(paragraphIdFromHash("#speech-5")).toBeNull();
    expect(paragraphIdFromHash("")).toBeNull();
  });

  it("gives each paragraph an id and a ¶ link that copies the paragraph address", async () => {
    const writeText = vi.fn().mockResolvedValue();
    Object.assign(navigator, { clipboard: { writeText } });
    render(
      <MemoryRouter>
        <SpeechText turns={turns} hasMember={true} speaker={speaker} />
      </MemoryRouter>
    );
    const link = screen.getByRole("link", { name: "Paragraph 2. Copy the link." });
    expect(link.getAttribute("href")).toBe("#p2");
    expect(document.getElementById("p2").textContent).toContain("Paragraph two.");
    await act(async () => {
      fireEvent.click(link);
    });
    expect(writeText).toHaveBeenCalledWith(`${window.location.origin}${window.location.pathname}#p2`);
    expect(window.location.hash).toBe("#p2");
    expect(document.getElementById("p2").className).toContain("speech-text__paragraph--target");
    expect(screen.getByRole("status").textContent).toBe("The link to paragraph 2 is copied.");
    window.history.replaceState(null, "", window.location.pathname);
  });

  it("offers to copy the selected words with the source and the paragraph", async () => {
    const writeText = vi.fn().mockResolvedValue();
    Object.assign(navigator, { clipboard: { writeText } });
    render(
      <MemoryRouter>
        <SpeechText turns={turns} hasMember={true} speaker={speaker} />
      </MemoryRouter>
    );
    expect(screen.getByText(/Select words in the speech to copy them with the source/)).toBeTruthy();

    const words = document.getElementById("p1").querySelector(".speech-text__para-body").firstChild;
    const range = document.createRange();
    range.setStart(words, 0);
    range.setEnd(words, "Paragraph one.".length);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);
    await act(async () => {
      document.dispatchEvent(new Event("selectionchange"));
    });

    const button = screen.getByRole("button", { name: "Copy the selected words with the source" });
    await act(async () => {
      fireEvent.click(button);
    });
    expect(writeText).toHaveBeenCalledWith(
      `“Paragraph one.” - Mahua Moitra (AITC, Krishnanagar), Lok Sabha, 17 Dec 2025. ${window.location.origin}/speech/178379#p1`
    );
    window.getSelection().removeAllRanges();
  });
});

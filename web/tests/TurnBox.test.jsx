import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import TurnBox from "../components/TurnBox.jsx";

afterEach(cleanup);

describe("TurnBox", () => {
  it("renders a member turn with link and metadata", () => {
    const turn = {
      seq: 1,
      kind: "member",
      member: "Om Birla",
      member_id: 225,
      label: "माननीय अध्यक्ष",
      text: "Single paragraph of text.",
      words: 37,
    };

    render(
      <MemoryRouter>
        <TurnBox turn={turn} meta="Speech 2 of 23" />
      </MemoryRouter>
    );

    const link = screen.getByRole("link", { name: "Om Birla" });
    expect(link.getAttribute("href")).toBe("/member/225");
    expect(screen.getByText("Speech 2 of 23 · 37 words")).toBeTruthy();
    expect(screen.getByText("Single paragraph of text.")).toBeTruthy();
    expect(screen.queryByText("माननीय अध्यक्ष")).toBeNull();
  });

  it("renders presiding officer as The Chair", () => {
    const turn = {
      seq: 2,
      kind: "presiding",
      text: "Order in the house.",
      words: 4,
    };

    render(<TurnBox turn={turn} />);
    expect(screen.getByText("The Chair")).toBeTruthy();
  });

  it("renders crowd turn as Several members", () => {
    const turn = {
      seq: 3,
      kind: "crowd",
      text: "Yes.",
      words: 1,
    };

    render(<TurnBox turn={turn} />);
    expect(screen.getByText("Several members")).toBeTruthy();
  });

  it("renders unattributed turn with standard identification lines", () => {
    const turn = {
      seq: 0,
      kind: "unattributed",
      label: "Printed Title",
      text: "VB-G RAM G Bill",
      words: 4,
    };

    render(<TurnBox turn={turn} />);

    expect(screen.getByText("Speaker not identified")).toBeTruthy();
    expect(
      screen.getByText(
        "Speaker not identified. Torko could not match this name to one member."
      )
    ).toBeTruthy();
    expect(screen.queryByText("Printed Title")).toBeNull();
  });

  it("limits text to two paragraphs and reveals rest on Read more", () => {
    const turn = {
      seq: 4,
      kind: "member",
      member: "Mahua Moitra",
      member_id: 1052,
      text: "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3.\n\nParagraph 4.",
      words: 100,
    };

    render(
      <MemoryRouter>
        <TurnBox turn={turn} />
      </MemoryRouter>
    );

    expect(screen.getByText("Paragraph 1.")).toBeTruthy();
    expect(screen.getByText("Paragraph 2.")).toBeTruthy();
    expect(screen.queryByText("Paragraph 3.")).toBeNull();

    const button = screen.getByRole("button", { name: "Read more" });
    fireEvent.click(button);

    expect(screen.getByText("Paragraph 3.")).toBeTruthy();
    expect(screen.getByText("Paragraph 4.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Read more" })).toBeNull();
  });

  it("sets lang attribute on Devanagari text", () => {
    const turn = {
      seq: 5,
      kind: "member",
      member: "Om Birla",
      member_id: 225,
      text: "क्या आप सभी पीछे वाले सदस्य आज सदन में हैं?",
      words: 10,
    };

    render(
      <MemoryRouter>
        <TurnBox turn={turn} />
      </MemoryRouter>
    );

    const para = screen.getByText("क्या आप सभी पीछे वाले सदस्य आज सदन में हैं?");
    expect(para.getAttribute("lang")).toBe("hi");
  });

  it("returns null when turn prop is missing", () => {
    const { container } = render(<TurnBox />);
    expect(container.firstChild).toBeNull();
  });
});

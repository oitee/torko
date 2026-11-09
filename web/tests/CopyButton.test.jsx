import React from "react";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import CopyButton, { speechCitation } from "../components/CopyButton.jsx";

afterEach(cleanup);

describe("CopyButton", () => {
  it("copies the text and says Copied", async () => {
    const writeText = vi.fn().mockResolvedValue();
    Object.assign(navigator, { clipboard: { writeText } });
    render(<CopyButton text={() => "hello"}>Copy link</CopyButton>);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Copy link" }));
    });
    expect(writeText).toHaveBeenCalledWith("hello");
    expect(screen.getByRole("button").textContent).toBe("Copied");
  });

  it("tells the parent when the browser blocks the copy, and keeps its label", async () => {
    Object.assign(navigator, { clipboard: { writeText: vi.fn().mockRejectedValue(new Error("blocked")) } });
    const onResult = vi.fn();
    render(<CopyButton text="x" onResult={onResult}>Copy citation</CopyButton>);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Copy citation" }));
    });
    expect(onResult).toHaveBeenCalledWith(false);
    expect(screen.getByRole("button").textContent).toBe("Copy citation");
  });
});

describe("speechCitation", () => {
  it("writes one line with the member, party, seat, date and link", () => {
    expect(
      speechCitation({ quote: "Words ", member: "Mahua Moitra", party: "AITC", seat: "Krishnanagar", date: "2025-12-17", id: 178379, origin: "https://x.in" })
    ).toBe("“Words” - Mahua Moitra (AITC, Krishnanagar), Lok Sabha, 2025-12-17. https://x.in/speech/178379");
  });
  it("names an unknown speaker in the house style", () => {
    expect(speechCitation({ date: "2001-01-01", id: 5, origin: "" })).toBe("Speaker not identified, Lok Sabha, 2001-01-01. /speech/5");
  });
});

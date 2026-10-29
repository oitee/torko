import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import MethodLimits from "../pages/method/MethodLimits.jsx";
import methodAnswer from "./fixtures/method/method.json";

afterEach(cleanup);

describe("MethodLimits", () => {
  it("states each limit with its figure from the API", () => {
    const { container } = render(<MethodLimits data={methodAnswer} />);
    const text = container.textContent;
    expect(text).toContain("About 0.24% of named turns have the wrong member name.");
    expect(text).toContain("106,168 of 526,701 turns have no member name.");
    expect(text).toContain("Torko does not read about 13.6% of the source text.");
    expect(text).toContain("The share is 32.5% in the 13th Lok Sabha and about 3% in recent terms.");
    expect(text).toContain("Cite the speech, not the TLDR.");
  });

  it("hides a line when its figure is missing", () => {
    const { container } = render(<MethodLimits data={{ ...methodAnswer, unread_text: null, turns: null }} />);
    expect(container.textContent).not.toContain("source text");
    expect(container.textContent).not.toContain("no member name");
    expect(screen.getAllByRole("listitem").length).toBe(3);
  });
});

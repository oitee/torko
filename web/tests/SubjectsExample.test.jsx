import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SubjectsExample, { markMentions } from "../pages/method/SubjectsExample.jsx";

afterEach(cleanup);

// The shape of /api/method → examples.subjects.
const EXAMPLE = {
  speech_id: 5,
  member_id: 2,
  member: "Member A",
  date: "2025-02-03",
  text: "The farmers of my district wait for the sugarcane dues. The Government must pay them.",
  summary: "Asks the Government to pay the sugarcane dues of farmers.",
  items: [
    { name: "Sugarcane arrears", mention: "sugarcane dues", kept: true, tag: "Arrears", tag_slug: "arrears" },
    { name: "Farmers", mention: "farmers", kept: true, tag: "Farmers", tag_slug: "farmers" },
    { name: "Government", mention: "Government", kept: false, tag: null, tag_slug: null },
  ],
};

function renderSubjects(example) {
  return render(
    <MemoryRouter>
      <SubjectsExample example={example} />
    </MemoryRouter>
  );
}

describe("markMentions", () => {
  it("marks each mention once, ignoring case, in the order of the text", () => {
    const parts = markMentions(EXAMPLE.text, EXAMPLE.items);
    expect(parts.filter((p) => p.mark).map((p) => p.text)).toEqual(["farmers", "sugarcane dues", "Government"]);
    expect(parts.map((p) => p.text).join("")).toBe(EXAMPLE.text);
  });

  it("skips a mention that is not in the text, and a mention that overlaps another", () => {
    const parts = markMentions("wage arrears are due", [
      { mention: "wage arrears", kept: true },
      { mention: "arrears are", kept: true },
      { mention: "pension", kept: true },
    ]);
    expect(parts.filter((p) => p.mark).map((p) => p.text)).toEqual(["wage arrears"]);
  });
});

describe("SubjectsExample", () => {
  it("boxes the mentions in the speech, and dashes the box of a dropped subject", () => {
    const { container } = renderSubjects(EXAMPLE);
    expect(container.querySelectorAll("mark")).toHaveLength(3);
    expect(container.querySelectorAll("mark.subjects-example__mark--dropped")).toHaveLength(1);
  });

  it("shows the TLDR with its label, and each subject with the result of the check", () => {
    renderSubjects(EXAMPLE);
    expect(screen.getByText("TLDR")).toBeTruthy();
    expect(screen.getByText(EXAMPLE.summary)).toBeTruthy();
    expect(screen.getAllByText("kept")).toHaveLength(2);
    expect(screen.getAllByText("dropped")).toHaveLength(1);
  });

  it("shows nothing without subjects", () => {
    expect(renderSubjects({ ...EXAMPLE, items: [] }).container.innerHTML).toBe("");
  });
});

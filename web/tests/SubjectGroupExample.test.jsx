import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SubjectGroupExample from "../pages/method/SubjectGroupExample.jsx";

afterEach(cleanup);

// The shape of /api/method → examples.subject_group.
const EXAMPLE = {
  subject_id: 1,
  label: "Sugarcane farmers' arrears",
  speeches: 236,
  n_names: 12,
  names: ["Sugarcane dues", "Cane arrears", "Arrears of sugarcane farmers"],
  tag: "Arrears",
  tag_slug: "arrears",
};

function renderGroup(example) {
  return render(
    <MemoryRouter>
      <SubjectGroupExample example={example} />
    </MemoryRouter>
  );
}

describe("SubjectGroupExample", () => {
  it("shows the names, the one subject with its speeches, and the tag as a link", () => {
    renderGroup(EXAMPLE);
    for (const n of EXAMPLE.names) expect(screen.getByText(n)).toBeTruthy();
    expect(screen.getByText("Names in different speeches · 3 of 12")).toBeTruthy();
    expect(screen.getByText(/Sugarcane farmers' arrears/)).toBeTruthy();
    expect(screen.getByText("· 236 speeches")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Arrears" }).getAttribute("href")).toBe("/tag/arrears");
  });

  it("leaves out the tag box when the subject has no tag", () => {
    renderGroup({ ...EXAMPLE, tag: null, tag_slug: null });
    expect(screen.queryByText("Under the tag")).toBeNull();
  });

  it("shows nothing without names", () => {
    expect(renderGroup({ ...EXAMPLE, names: [] }).container.innerHTML).toBe("");
  });
});

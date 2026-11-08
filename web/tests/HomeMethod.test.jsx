import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import HomeMethod, { methodRows } from "../pages/home/HomeMethod.jsx";
import methodAnswer from "./fixtures/method/method.json";

afterEach(cleanup);

function renderMethod(props) {
  return render(
    <MemoryRouter>
      <HomeMethod {...props} />
    </MemoryRouter>
  );
}

describe("methodRows", () => {
  it("gives each count with its denominator, from the answer", () => {
    const rows = methodRows(methodAnswer);
    const oneSpeaker = methodAnswer.turns.total - methodAnswer.turns.chair_or_crowd;
    expect(rows.map((r) => r.key)).toEqual(["read", "who", "join", "subjects"]);
    expect(rows[0].value).toBe(methodAnswer.turns.total.toLocaleString("en-US"));
    expect(rows[1].label).toContain(`of ${oneSpeaker.toLocaleString("en-US")} turns of one speaker`);
    expect(rows[3].label).toContain(`of ${methodAnswer.speeches.eligible.toLocaleString("en-US")} speeches of 50 words or more`);
  });

  it("leaves out a row whose figures are missing", () => {
    expect(methodRows({ turns: { total: 5 } }).map((r) => r.key)).toEqual(["read"]);
    expect(methodRows(null)).toEqual([]);
  });
});

describe("HomeMethod", () => {
  it("links each row to its step on the Method page", () => {
    renderMethod({ method: methodAnswer });
    const hrefs = screen.getAllByRole("link").map((a) => a.getAttribute("href"));
    // The Method page has no section anchors, so every row opens the page itself.
    expect(hrefs).toEqual(["/method", "/method", "/method", "/method", "/method"]);
  });

  it("shows the text and the link alone when the answer is missing", () => {
    renderMethod({ method: null });
    expect(screen.getByRole("link", { name: "Read how Torko works" }).getAttribute("href")).toBe("/method");
    expect(screen.queryByRole("list")).toBeNull();
  });

  it("shows a loading state of a fixed size while the answer loads", () => {
    renderMethod({ method: null, loading: true });
    expect(screen.getByRole("status")).toBeTruthy();
  });
});

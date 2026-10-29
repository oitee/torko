import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import HomeFigures, { termRange } from "../pages/home/HomeFigures.jsx";
import homeAnswer from "./fixtures/home/home.json";

afterEach(cleanup);

describe("termRange", () => {
  it("names the first and the last term", () => {
    expect(termRange([13, 14, 15, 16, 17, 18])).toBe("13th–18th Lok Sabha");
  });

  it("names one term alone", () => {
    expect(termRange([18])).toBe("18th Lok Sabha");
  });

  it("gives an empty text for no terms", () => {
    expect(termRange([])).toBe("");
    expect(termRange(undefined)).toBe("");
  });
});

describe("HomeFigures", () => {
  it("shows each figure of the saved corpus answer with its label", () => {
    render(<HomeFigures corpus={homeAnswer.corpus} />);
    expect(screen.getByTestId("figure-debates").textContent).toContain("64,921");
    expect(screen.getByTestId("figure-members").textContent).toContain(
      "members with at least one speech, in 6 terms (13th–18th Lok Sabha)"
    );
    expect(screen.getByTestId("figure-tags").textContent).toContain("7,027");
    const err = screen.getByTestId("figure-error").textContent;
    expect(err).toContain("about 0.24%");
    expect(err).toContain("of named turns with the wrong member name");
    expect(err).toContain(homeAnswer.corpus.error_rate.source);
  });

  it("follows the API, not a number written into the page", () => {
    render(<HomeFigures corpus={{ ...homeAnswer.corpus, debates: 70000, tags: 12 }} />);
    expect(screen.getByText("70,000")).toBeTruthy();
    expect(screen.getByText("12")).toBeTruthy();
    expect(screen.queryByText("64,921")).toBeNull();
  });

  it("hides the row of a missing figure", () => {
    render(<HomeFigures corpus={{ debates: 5 }} />);
    expect(screen.getByTestId("figure-debates")).toBeTruthy();
    expect(screen.queryByTestId("figure-members")).toBeNull();
    expect(screen.queryByTestId("figure-tags")).toBeNull();
    expect(screen.queryByTestId("figure-error")).toBeNull();
  });

  it("shows nothing without a corpus", () => {
    const { container } = render(<HomeFigures corpus={null} />);
    expect(container.innerHTML).toBe("");
  });
});

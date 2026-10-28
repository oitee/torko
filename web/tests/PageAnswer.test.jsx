import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import PageAnswer from "../components/PageAnswer.jsx";
import Count from "../components/Count.jsx";

afterEach(cleanup);

describe("PageAnswer", () => {
  it("renders an h1 element with answer text", () => {
    render(
      <PageAnswer>
        Mahua Moitra spoke 41 times in the 17th Lok Sabha.
      </PageAnswer>
    );

    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toBeTruthy();
    expect(
      screen.getByText("Mahua Moitra spoke 41 times in the 17th Lok Sabha.")
    ).toBeTruthy();
  });

  it("renders with an optional Count element", () => {
    render(
      <PageAnswer count={<Count n={41} total={1318} noun="speeches" />}>
        Mahua Moitra made
      </PageAnswer>
    );

    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading.textContent).toContain("Mahua Moitra made");
    expect(heading.textContent).toContain("41 of 1,318 speeches");
  });

  it("returns null when children and count are missing", () => {
    const { container } = render(<PageAnswer />);
    expect(container.firstChild).toBeNull();
  });
});

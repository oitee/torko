import React from "react";
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import MethodCounts from "../pages/method/MethodCounts.jsx";
import methodAnswer from "./fixtures/method/method.json";
import { formatNumber } from "../assets/js/format.js";

afterEach(cleanup);

describe("MethodCounts", () => {
  it("shows the four totals from the API, with the date range of the debates", () => {
    const { container } = render(<MethodCounts data={methodAnswer} />);
    const counts = [...container.querySelectorAll(".method-counts__count")].map((c) => c.textContent);
    expect(counts).toEqual([
      `${formatNumber(64921)}debates, 20 Oct 1999 to 18 Apr 2026`,
      `${formatNumber(526701)}speaking turns`,
      `${formatNumber(173225)}speeches`,
      `${formatNumber(7027)}subject tags`,
    ]);
  });

  it("hides a total that the API does not send", () => {
    const { container } = render(<MethodCounts data={{ corpus: { tags: 5 } }} />);
    expect(container.querySelectorAll(".method-counts__count")).toHaveLength(1);
  });

  it("shows nothing without totals", () => {
    expect(render(<MethodCounts data={{}} />).container.innerHTML).toBe("");
  });
});

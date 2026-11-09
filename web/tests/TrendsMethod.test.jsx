import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import MethodBlock from "../components/MethodBlock.jsx";

afterEach(cleanup);

describe("MethodBlock", () => {
  it("opens the rule in a panel and closes it with the X button", () => {
    render(
      <MethodBlock>
        <p>Usual = the median share of the subject over all months.</p>
      </MethodBlock>
    );
    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "How this is calculated" }));
    expect(screen.getByRole("dialog", { name: "How this is calculated" }).textContent).toContain("Usual = the median share");
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("closes with Escape", () => {
    render(<MethodBlock><p>Rule</p></MethodBlock>);
    fireEvent.click(screen.getByRole("button", { name: "How this is calculated" }));
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

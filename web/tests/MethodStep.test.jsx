import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import MethodStep from "../pages/method/MethodStep.jsx";

afterEach(cleanup);

describe("MethodStep", () => {
  it("shows the number, the heading, the text and the figure", () => {
    const { container } = render(
      <ol>
        <MethodStep n={2} title="Find who spoke" figure="5 of 10 turns">
          <p>Some text.</p>
        </MethodStep>
      </ol>
    );
    expect(screen.getByRole("heading", { level: 2, name: "Find who spoke" })).toBeTruthy();
    expect(screen.getByText("Some text.")).toBeTruthy();
    expect(screen.getByText("5 of 10 turns").className).toBe("method-step__figure");
    expect(container.querySelector(".method-step__n").textContent).toBe("2");
  });

  it("leaves out the figure line when there is no figure", () => {
    const { container } = render(
      <ol>
        <MethodStep n={1} title="Read the debates" figure={false} />
      </ol>
    );
    expect(container.querySelector(".method-step__figure")).toBeNull();
  });
});

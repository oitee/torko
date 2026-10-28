import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Count from "../components/Count.jsx";

afterEach(cleanup);

describe("Count", () => {
  it("formats a single number", () => {
    render(<Count n={1318} />);

    expect(screen.getByText("1,318")).toBeTruthy();
  });

  it("shows an en dash when n is missing", () => {
    render(<Count />);

    expect(screen.getByText("–")).toBeTruthy();
  });

  it("formats count with total and noun", () => {
    render(<Count n={41} total={1318} noun="speeches" />);

    expect(screen.getByText("41 of 1,318 speeches")).toBeTruthy();
  });

  it("renders a link when href is given", () => {
    render(
      <MemoryRouter>
        <Count n={41} total={1318} noun="speeches" href="/speeches" />
      </MemoryRouter>
    );

    const link = screen.getByRole("link", { name: "41 of 1,318 speeches" });
    expect(link.getAttribute("href")).toBe("/speeches");
    expect(link.classList.contains("count--link")).toBe(true);
  });
});

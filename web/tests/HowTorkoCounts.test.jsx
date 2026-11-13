import React from "react";
import { MemoryRouter } from "react-router-dom";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import HowTorkoCounts from "../components/HowTorkoCounts.jsx";

afterEach(cleanup);

describe("HowTorkoCounts", () => {
  it("is one link to the Method page", () => {
    render(
      <MemoryRouter>
        <HowTorkoCounts />
      </MemoryRouter>
    );
    expect(screen.getByRole("link", { name: "How counts work" }).getAttribute("href")).toBe("/method");
  });
});

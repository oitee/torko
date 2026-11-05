import React from "react";
import { MemoryRouter } from "react-router-dom";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import PartyLink from "../components/PartyLink.jsx";

afterEach(cleanup);

describe("PartyLink", () => {
  it("links a code with special letters to its page", () => {
    render(<MemoryRouter><PartyLink code="J&KNC" /></MemoryRouter>);
    expect(screen.getByRole("link", { name: "J&KNC" }).getAttribute("href")).toBe("/party/J%26KNC");
  });

  it("shows nothing with no code", () => {
    const { container } = render(<MemoryRouter><PartyLink code="" /></MemoryRouter>);
    expect(container.textContent).toBe("");
  });
});

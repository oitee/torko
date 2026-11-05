import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import NotFound from "../pages/not_found.jsx";

function at(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <NotFound />
    </MemoryRouter>,
  );
}

afterEach(cleanup);

describe("NotFound", () => {
  it("names the address that the reader asked for", () => {
    const { container } = at("/party/xyz");
    expect(container.querySelector(".not-found__path").textContent).toBe("/party/xyz");
  });

  it("links to the home page", () => {
    at("/party/xyz");
    expect(screen.getByRole("link", { name: "Go to the home page" }).getAttribute("href")).toBe("/");
  });

  it("gives the search input a visible label and a quiet button", () => {
    at("/party/xyz");
    expect(screen.getByRole("combobox", { name: "Or search the debates" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Search" }).className).toContain("button--secondary");
  });

  it("marks one seat in the picture of the House", () => {
    const { container } = at("/party/xyz");
    expect(container.querySelectorAll(".house-seats__seat--marked")).toHaveLength(1);
  });
});

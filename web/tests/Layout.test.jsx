import React from "react";
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import Layout from "../components/Layout.jsx";

afterEach(cleanup);

function renderAt(path) {
  const router = createMemoryRouter(
    [{ element: <Layout />, children: [{ path: "*", element: <p>Page</p> }] }],
    { initialEntries: [path] }
  );
  return render(<RouterProvider router={router} />);
}

describe("Layout", () => {
  it("shows the footer links and the source link", () => {
    renderAt("/");
    const footer = screen.getByRole("contentinfo");
    const nav = within(footer).getByRole("navigation", { name: "Footer" });
    expect(within(nav).getByRole("link", { name: "Trends" }).getAttribute("href")).toBe("/trends");
    expect(within(nav).getByRole("link", { name: "Method" }).getAttribute("href")).toBe("/method");
    // The API is private now, so the footer has no link to it.
    expect(within(nav).queryByRole("link", { name: "API" })).toBeNull();
    expect(within(footer).getByRole("link", { name: "sansad.in" }).getAttribute("href")).toContain("sansad.in");
    expect(footer.textContent).toContain("Torko is not an official site.");
  });
});

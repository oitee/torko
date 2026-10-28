import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { routes } from "../router.jsx";

function at(path) {
  render(<RouterProvider router={createMemoryRouter(routes, { initialEntries: [path] })} />);
}

afterEach(cleanup);

describe("router", () => {
  it.each([
    ["/", "Home"],
    ["/tag/arrears", "Tag"],
    ["/member/123", "Member"],
    ["/speech/1", "Speech"],
    ["/debate/1", "Debate"],
    ["/place/latur", "Place"],
    ["/search", "Search the speeches of the Lok Sabha"],
    ["/dev/components", "Components"],
    ["/no/such/page", "Page not found"],
  ])("shows %s as the %s page", (path, heading) => {
    at(path);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(heading);
  });
});

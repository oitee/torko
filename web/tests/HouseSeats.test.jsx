import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import HouseSeats, { HOUSE_SEATS, seatLayout } from "../pages/home/HouseSeats.jsx";

afterEach(cleanup);

describe("HouseSeats", () => {
  it("places exactly one dot for each seat of the House", () => {
    expect(HOUSE_SEATS).toBe(543);
    expect(seatLayout()).toHaveLength(543);
  });

  it("marks exactly one seat", () => {
    expect(seatLayout().filter((s) => s.marked)).toHaveLength(1);
  });

  it("draws the seats with a text alternative and a caption that names no real seat", () => {
    const { container } = render(<HouseSeats />);
    expect(container.querySelectorAll("circle")).toHaveLength(543);
    expect(screen.getByRole("img").getAttribute("aria-label")).toBe("The 543 seats of the Lok Sabha. One seat is marked.");
    expect(screen.getByText(/One member speaks for your seat\./)).toBeTruthy();
  });

  it("has no link on the marked seat unless the page asks for one", () => {
    render(<HouseSeats />);
    expect(screen.queryByRole("link")).toBeNull();
  });

  it("makes the marked seat a link with a text label when the page gives an address", () => {
    render(
      <MemoryRouter>
        <HouseSeats markedHref="/my-mp" markedLabel="Find your MP: the marked seat" />
      </MemoryRouter>
    );
    const link = screen.getByRole("link", { name: "Find your MP: the marked seat" });
    expect(link.getAttribute("href")).toBe("/my-mp");
    expect(link.style.left).toMatch(/%$/);
  });
});

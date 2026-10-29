import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
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
});

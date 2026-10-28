import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { EmptyState, ErrorState, Loading } from "../components/States.jsx";

afterEach(cleanup);

describe("Loading", () => {
  it("renders grey bars with aria-busy and hidden loading text", () => {
    const { container } = render(<Loading lines={4} />);

    const wrapper = container.querySelector(".states-loading");
    expect(wrapper.getAttribute("aria-busy")).toBe("true");

    expect(screen.getByText("Loading")).toBeTruthy();

    const bars = container.querySelectorAll(".states-loading__bar");
    expect(bars.length).toBe(4);
  });

  it("defaults to 3 lines when lines prop is omitted", () => {
    const { container } = render(<Loading />);
    const bars = container.querySelectorAll(".states-loading__bar");
    expect(bars.length).toBe(3);
  });
});

describe("ErrorState", () => {
  it("shows server error message and a retry button", () => {
    const onRetry = vi.fn();
    const error = {
      status: 500,
      message: "The server could not answer. Try again.",
    };

    render(<ErrorState error={error} onRetry={onRetry} />);

    expect(
      screen.getByText("The server could not answer. Try again.")
    ).toBeTruthy();

    const button = screen.getByRole("button", { name: "Try again" });
    fireEvent.click(button);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("shows Page not found and no button for 404 status", () => {
    const onRetry = vi.fn();
    const error = { status: 404, message: "Not found" };

    render(<ErrorState error={error} onRetry={onRetry} />);

    expect(screen.getByText("Page not found")).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });
});

describe("EmptyState", () => {
  it("renders the message in meta text", () => {
    render(
      <EmptyState>This member made no speech in the 17th Lok Sabha.</EmptyState>
    );

    expect(
      screen.getByText("This member made no speech in the 17th Lok Sabha.")
    ).toBeTruthy();
  });

  it("returns null when children is missing", () => {
    const { container } = render(<EmptyState />);
    expect(container.firstChild).toBeNull();
  });
});

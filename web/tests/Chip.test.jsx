import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Chip from "../components/Chip.jsx";

afterEach(cleanup);

describe("Chip", () => {
  it("shows the label and the count", () => {
    render(<Chip label="MGNREGA" count={1318} />);

    expect(screen.getByText("MGNREGA")).toBeTruthy();
    expect(screen.getByText("1,318")).toBeTruthy();
  });

  it("shows the label without a count when count is omitted", () => {
    render(<Chip label="Rural employment" />);

    expect(screen.getByText("Rural employment")).toBeTruthy();
    expect(screen.queryByText(/0|1|2|3|4|5|6|7|8|9/)).toBeNull();
  });

  it("renders a link with the correct address when href is set", () => {
    render(
      <MemoryRouter>
        <Chip label="Arrears" href="/tag/arrears" />
      </MemoryRouter>
    );

    const link = screen.getByRole("link", { name: "Arrears" });
    expect(link.getAttribute("href")).toBe("/tag/arrears");
  });

  it("shows a check mark when selected", () => {
    const { container } = render(<Chip label="Arrears" selected />);

    expect(screen.getByText("✓")).toBeTruthy();
    expect(container.firstChild.classList.contains("chip--selected")).toBe(true);
  });

  it("calls onRemove and sets the aria-label on the remove button", () => {
    const onRemove = vi.fn();
    render(<Chip label="Arrears" onRemove={onRemove} />);

    const button = screen.getByRole("button", { name: "Remove Arrears" });
    expect(button).toBeTruthy();
    expect(button.textContent).toBe("✕");
    expect(button.getAttribute("aria-label")).toBe("Remove Arrears");

    fireEvent.click(button);
    expect(onRemove).toHaveBeenCalledTimes(1);
  });

  it("renders the remove button outside the link", () => {
    const onRemove = vi.fn();
    const { container } = render(
      <MemoryRouter>
        <Chip label="Arrears" href="/tag/arrears" onRemove={onRemove} />
      </MemoryRouter>
    );

    expect(container.querySelector("a button")).toBeNull();

    const link = screen.getByRole("link", { name: "Arrears" });
    expect(link.getAttribute("href")).toBe("/tag/arrears");

    const button = screen.getByRole("button", { name: "Remove Arrears" });
    fireEvent.click(button);
    expect(onRemove).toHaveBeenCalledTimes(1);
  });
});

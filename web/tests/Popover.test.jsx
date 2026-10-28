import React, { useRef, useState } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import Popover from "../components/Popover.jsx";

afterEach(cleanup);

function PopoverHarness({ defaultOpen = false, onClose }) {
  const [open, setOpen] = useState(defaultOpen);
  const buttonRef = useRef(null);

  const handleClose = () => {
    setOpen(false);
    onClose?.();
  };

  return (
    <div>
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setOpen((prev) => !prev)}
      >
        Toggle
      </button>
      <button type="button">Outside element</button>
      <Popover
        open={open}
        onClose={handleClose}
        triggerRef={buttonRef}
        role="dialog"
      >
        <p>Popover content</p>
      </Popover>
    </div>
  );
}

describe("Popover", () => {
  it("renders children when open is true", () => {
    render(<Popover open={true}><p>Visible content</p></Popover>);
    expect(screen.getByText("Visible content")).toBeTruthy();
  });

  it("does not render when open is false", () => {
    render(<Popover open={false}><p>Hidden content</p></Popover>);
    expect(screen.queryByText("Hidden content")).toBeNull();
  });

  it("closes when the Escape key is pressed and calls onClose", () => {
    const handleClose = vi.fn();
    render(
      <Popover open={true} onClose={handleClose}>
        <p>Modal content</p>
      </Popover>
    );

    fireEvent.keyDown(document, { key: "Escape" });
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("closes when a click occurs outside the popover", () => {
    const handleClose = vi.fn();
    render(
      <div>
        <div data-testid="outside">Outside area</div>
        <Popover open={true} onClose={handleClose}>
          <p>Inner content</p>
        </Popover>
      </div>
    );

    fireEvent.mouseDown(screen.getByTestId("outside"));
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("does not close when clicking inside the popover", () => {
    const handleClose = vi.fn();
    render(
      <Popover open={true} onClose={handleClose}>
        <p data-testid="inside">Inner content</p>
      </Popover>
    );

    fireEvent.mouseDown(screen.getByTestId("inside"));
    expect(handleClose).not.toHaveBeenCalled();
  });

  it("returns focus to trigger element when closing on Escape", () => {
    const onClose = vi.fn();
    render(<PopoverHarness defaultOpen={true} onClose={onClose} />);

    const trigger = screen.getByRole("button", { name: "Toggle" });
    fireEvent.keyDown(document, { key: "Escape" });

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(document.activeElement).toBe(trigger);
  });

  it("returns focus to trigger element when closing on outside click", () => {
    const onClose = vi.fn();
    render(<PopoverHarness defaultOpen={true} onClose={onClose} />);

    const trigger = screen.getByRole("button", { name: "Toggle" });
    const outside = screen.getByRole("button", { name: "Outside element" });

    fireEvent.mouseDown(outside);

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(document.activeElement).toBe(trigger);
  });

  it("returns focus to trigger element when open changes from true to false", () => {
    const trigger = document.createElement("button");
    document.body.appendChild(trigger);
    const triggerRef = { current: trigger };

    const { rerender } = render(
      <Popover open={true} triggerRef={triggerRef}>
        <p>Content</p>
      </Popover>
    );

    rerender(
      <Popover open={false} triggerRef={triggerRef}>
        <p>Content</p>
      </Popover>
    );

    expect(document.activeElement).toBe(trigger);
    document.body.removeChild(trigger);
  });
});

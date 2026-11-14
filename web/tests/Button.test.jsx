import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Button from "../components/Button.jsx";

afterEach(cleanup);

describe("Button", () => {
  it("renders a secondary button by default", () => {
    render(<Button>Click me</Button>);

    const button = screen.getByRole("button", { name: "Click me" });
    expect(button).toBeTruthy();
    expect(button.classList.contains("button--secondary")).toBe(true);
    expect(button.getAttribute("type")).toBe("button");
  });

  it("renders a primary button variant", () => {
    render(<Button variant="primary">Submit</Button>);

    const button = screen.getByRole("button", { name: "Submit" });
    expect(button.classList.contains("button--primary")).toBe(true);
  });

  it("renders a text button variant", () => {
    render(<Button variant="text">Read more</Button>);

    const button = screen.getByRole("button", { name: "Read more" });
    expect(button.classList.contains("button--text")).toBe(true);
  });

  it("renders a link when href is passed", () => {
    render(
      <MemoryRouter>
        <Button href="/tag/arrears" variant="secondary">
          Go to tag
        </Button>
      </MemoryRouter>
    );

    const link = screen.getByRole("link", { name: "Go to tag" });
    expect(link.getAttribute("href")).toBe("/tag/arrears");
    expect(link.classList.contains("button--secondary")).toBe(true);
  });

  it("fires onClick handler when clicked", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    const button = screen.getByRole("button", { name: "Click" });
    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("falls back to secondary when unknown variant is given", () => {
    render(<Button variant="unknown">Fallback</Button>);

    const button = screen.getByRole("button", { name: "Fallback" });
    expect(button.classList.contains("button--secondary")).toBe(true);
  });

  it("opens an address on another site in a new tab", () => {
    render(
      <MemoryRouter>
        <Button variant="text" href="https://sansad.in/ls/debates/58204">Read the original on sansad.in</Button>
      </MemoryRouter>
    );
    const link = screen.getByRole("link", { name: "Read the original on sansad.in" });
    expect(link.getAttribute("href")).toBe("https://sansad.in/ls/debates/58204");
    expect(link.getAttribute("target")).toBe("_blank");
    expect(link.getAttribute("rel")).toBe("noopener noreferrer");
  });

  it("keeps an address in Torko in the same tab", () => {
    render(
      <MemoryRouter>
        <Button href="/method">Method</Button>
      </MemoryRouter>
    );
    expect(screen.getByRole("link", { name: "Method" }).getAttribute("target")).toBeNull();
  });
});

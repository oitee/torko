import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SourceChip, { SOURCE_CONFIG } from "../pages/speech/SourceChip.jsx";

afterEach(cleanup);

describe("SourceChip", () => {
  it("renders glyph, hidden word, Chip and Why button for llm source", () => {
    const tag = {
      name: "Rural Development",
      slug: "rural-development",
      source: "llm",
    };
    const onWhy = vi.fn();

    render(
      <MemoryRouter>
        <SourceChip tag={tag} onWhyClick={onWhy} isWhyOpen={false} />
      </MemoryRouter>
    );

    const glyph = screen.getByText("◆");
    expect(glyph).toBeTruthy();
    expect(glyph.getAttribute("aria-hidden")).toBe("true");

    const hiddenWord = screen.getByText("the model named it");
    expect(hiddenWord).toBeTruthy();

    const chipLink = screen.getByRole("link", { name: "Rural Development" });
    expect(chipLink).toBeTruthy();
    expect(chipLink.getAttribute("href")).toBe("/tag/rural-development");

    const whyBtn = screen.getByRole("button", { name: "Why is tag Rural Development here" });
    expect(whyBtn).toBeTruthy();
    expect(whyBtn.getAttribute("aria-expanded")).toBe("false");

    fireEvent.click(whyBtn);
    expect(onWhy).toHaveBeenCalledTimes(1);
  });

  it("renders glyph and hidden word for dictionary source", () => {
    const tag = {
      name: "Mahatma Gandhi",
      slug: "mahatma-gandhi",
      source: "dictionary",
    };

    render(
      <MemoryRouter>
        <SourceChip tag={tag} />
      </MemoryRouter>
    );

    expect(screen.getByText("“”")).toBeTruthy();
    expect(screen.getByText("a word matched")).toBeTruthy();
  });

  it("renders glyph and hidden word for summary_tag source", () => {
    const tag = {
      name: "Employment Guarantee",
      slug: "employment-guarantee",
      source: "summary_tag",
    };

    render(
      <MemoryRouter>
        <SourceChip tag={tag} />
      </MemoryRouter>
    );

    expect(screen.getByText("≈")).toBeTruthy();
    expect(screen.getByText("near in meaning")).toBeTruthy();
  });
});

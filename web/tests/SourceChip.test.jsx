import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SourceChip from "../pages/speech/SourceChip.jsx";

afterEach(cleanup);

function renderChip(source, props = {}) {
  return render(
    <MemoryRouter>
      <SourceChip tag={{ name: "Arrears", slug: "arrears", source }} {...props} />
    </MemoryRouter>
  );
}

describe("SourceChip", () => {
  it.each([
    ["llm", "◆", "the model named it"],
    ["dictionary", "“”", "a word matched"],
    ["summary_tag", "≈", "near in meaning"],
  ])("puts the glyph and the hidden word of %s inside the chip", (source, glyph, word) => {
    renderChip(source, { onSelect: () => {} });
    const chip = screen.getByRole("button", { name: new RegExp(`${word}: Arrears`) });
    const glyphEl = chip.querySelector(".source-chip__glyph");
    expect(glyphEl.textContent).toBe(glyph);
    expect(glyphEl.getAttribute("aria-hidden")).toBe("true");
  });

  it("calls onSelect and shows the selected state", () => {
    const onSelect = vi.fn();
    renderChip("llm", { onSelect, selected: true });
    const chip = screen.getByRole("button", { name: /Arrears/ });
    expect(chip.getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(chip);
    expect(onSelect).toHaveBeenCalled();
  });
});

import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import LegacyExample from "../pages/method/LegacyExample.jsx";
import methodAnswer from "./fixtures/method/method.json";

afterEach(cleanup);

const legacy = methodAnswer.examples.legacy;

function renderLegacy(example) {
  return render(
    <MemoryRouter>
      <LegacyExample example={example} />
    </MemoryRouter>
  );
}

describe("LegacyExample", () => {
  it("shows the stored old-font text and its Hindi, marked as Hindi", () => {
    renderLegacy(legacy);
    expect(screen.getByText(legacy.source_text)).toBeTruthy();
    const hindi = screen.getByText(legacy.text);
    expect(hindi.getAttribute("lang")).toBe("hi");
    expect(legacy.text.startsWith("अध्यक्ष महोदय, गृह मंत्री जी ने कहा था")).toBe(true);
  });

  it("names the member, the date and the source page when the API knows the debate", () => {
    renderLegacy({
      ...legacy,
      debate: { date: "2005-08-11", member: "A Member", member_id: 7, source_url: "https://sansad.in/x" },
    });
    expect(screen.getByRole("link", { name: "A Member" }).getAttribute("href")).toBe("/member/7");
    expect(screen.getByText("2005-08-11")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Read the original on sansad.in" }).getAttribute("href")).toBe("https://sansad.in/x");
  });

  it("shows nothing without both texts", () => {
    expect(renderLegacy(null).container.innerHTML).toBe("");
    cleanup();
    expect(renderLegacy({ source_text: "x" }).container.innerHTML).toBe("");
  });
});

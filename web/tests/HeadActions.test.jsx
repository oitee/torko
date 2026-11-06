import React from "react";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import HeadActions, { accessedToday, pageCitation } from "../components/HeadActions.jsx";

afterEach(cleanup);

describe("HeadActions", () => {
  it("writes the citation with the source and the date of access", () => {
    expect(
      pageCitation({ title: "Mahua Moitra", detail: "66 speeches in the Lok Sabha", origin: "https://torko.in", path: "/member/1052", today: "7 Nov 2026" })
    ).toBe("Mahua Moitra, 66 speeches in the Lok Sabha. Torko, https://torko.in/member/1052. Source: sansad.in. Accessed 7 Nov 2026.");
    expect(accessedToday(new Date(2026, 10, 9))).toBe("9 Nov 2026");
  });

  it("has two actions only: Cite in a box, and Copy link as text", () => {
    render(<HeadActions citation="A citation." />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.map((b) => b.textContent)).toEqual(["Cite this page", "Copy link"]);
    expect(buttons[0].className).toContain("button--secondary");
    expect(buttons[1].className).toContain("button--text");
    expect(screen.queryByRole("link")).toBeNull();
  });

  it("opens the citation and copies it", async () => {
    const writeText = vi.fn().mockResolvedValue();
    Object.assign(navigator, { clipboard: { writeText } });
    render(<HeadActions citation="A citation." />);
    fireEvent.click(screen.getByRole("button", { name: "Cite this page" }));
    expect(screen.getByRole("dialog", { name: "Citation" }).textContent).toContain("A citation.");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Copy citation" }));
    });
    expect(writeText).toHaveBeenCalledWith("A citation.");
    expect(screen.getByRole("button", { name: "Citation copied" })).toBeTruthy();
  });
});

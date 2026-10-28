import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import DebateWho from "../pages/debate/DebateWho.jsx";

afterEach(cleanup);

describe("DebateWho", () => {
  const samplePeople = [
    {
      id: 101,
      name: "Anil Kumar",
      party: "BJP",
      seat: "Patna Sahib",
      words: 1204,
      speeches: 4,
    },
    {
      id: 102,
      name: "Sunita Meena",
      party: "BSP",
      seat: "Dausa",
      words: 520,
      speeches: 2,
    },
  ];

  const sampleSilent = [
    {
      member_id: 201,
      name: "Rajiv Pratap Rudy",
      party: "BJP",
      seat: "Saran",
    },
  ];

  it("renders who spoke list with order, member link, meta, speeches button", () => {
    const onSelect = vi.fn();
    render(
      <MemoryRouter>
        <DebateWho
          people={samplePeople}
          unidentified={{ speeches: 2, turns: 4, words: 90 }}
          silent={sampleSilent}
          selectedMemberId={101}
          onSelectMember={onSelect}
        />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: "Who spoke" })).toBeTruthy();
    expect(screen.getByText(/2 members spoke, in the order shown/)).toBeTruthy();

    const anilLink = screen.getByRole("link", { name: "Anil Kumar" });
    expect(anilLink.getAttribute("href")).toBe("/member/101");
    expect(screen.getByText(/BJP · Patna Sahib · 1,204 words/)).toBeTruthy();

    const anilBtn = screen.getByRole("button", {
      name: "Stop showing only Anil Kumar",
    });
    expect(anilBtn.getAttribute("aria-pressed")).toBe("true");

    const sunitaBtn = screen.getByRole("button", {
      name: "Show everything said by Sunita Meena",
    });
    fireEvent.click(sunitaBtn);
    expect(onSelect).toHaveBeenCalledWith(102);

    expect(
      screen.getByText(
        (_, el) =>
          el?.classList?.contains("debate-who__unidentified") &&
          el?.textContent?.includes(
            "Speaker not identified · 2 speeches. Torko could not match this name"
          )
      )
    ).toBeTruthy();

    expect(
      screen.getByRole("heading", { name: /Listed but did not speak/ })
    ).toBeTruthy();
    expect(screen.getByText("Rajiv Pratap Rudy")).toBeTruthy();
    expect(screen.getByText("BJP · Saran")).toBeTruthy();
    expect(
      screen.getByText(/Names on the official list of speakers for this debate/)
    ).toBeTruthy();
  });
});

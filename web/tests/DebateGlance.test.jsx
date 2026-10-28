import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import DebateGlance, { buildGlanceData } from "../pages/debate/DebateGlance.jsx";

afterEach(cleanup);

describe("DebateGlance", () => {
  const sampleDebate = {
    speeches: [
      { id: 1, words: 500, interruptions: 2 },
      { id: 2, words: 300, interruptions: 1 },
    ],
    people: [
      { id: 10, name: "Member One" },
      { id: 20, name: "Member Two" },
    ],
    tags: [
      { name: "Rural Development", speeches: 2 },
    ],
    turn_list: [{}, {}, {}],
  };

  it("builds sentence with speech count, top tag, and interruptions", () => {
    const data = buildGlanceData(sampleDebate);
    expect(data.sentence).toBe(
      "2 speeches by 2 members. Rural Development came up most, in 2 of 2 speeches. Members and the chair broke into a speech 3 times."
    );
    expect(data.figures).toHaveLength(4);
    expect(data.figures[0]).toEqual({ n: "2", label: "speeches" });
    expect(data.figures[1]).toEqual({ n: "2", label: "members identified" });
    expect(data.figures[2]).toEqual({ n: "800", label: "words in all speeches" });
    expect(data.figures[3]).toEqual({ n: "3", label: "interruptions inside speeches" });
  });

  it("handles a debate with no speech (64920)", () => {
    const emptyDebate = {
      speeches: [],
      people: [],
      tags: [],
      turn_list: [{}, {}],
    };
    const data = buildGlanceData(emptyDebate);
    expect(data.sentence).toBe("This debate has no speech. It has 2 turns.");
    expect(data.figures).toBeNull();

    render(<DebateGlance debate={emptyDebate} />);
    expect(screen.getByText("This debate has no speech. It has 2 turns.")).toBeTruthy();
    expect(screen.queryByText("speeches")).toBeNull();
  });

  it("renders heading, sentence, and 4 figure boxes for regular debate", () => {
    render(<DebateGlance debate={sampleDebate} />);
    expect(screen.getByRole("heading", { name: "At a glance" })).toBeTruthy();
    expect(
      screen.getByText(
        "2 speeches by 2 members. Rural Development came up most, in 2 of 2 speeches. Members and the chair broke into a speech 3 times."
      )
    ).toBeTruthy();
    expect(screen.getByText("800")).toBeTruthy();
    expect(screen.getByText("words in all speeches")).toBeTruthy();
  });
});

describe("buildGlanceData with an unidentified speaker", () => {
  it("says how many members Torko identified, not who spoke", () => {
    const data = buildGlanceData({
      speeches: [{ id: 1, words: 177, interruptions: 0 }],
      people: [],
      turn_list: [],
      tags: [],
      unidentified: { speeches: 1, turns: 1, words: 177 },
    });
    expect(data.sentence).toBe("1 speech. 0 members identified.");
    expect(data.figures[1]).toEqual({ n: "0", label: "members identified" });
  });
});

import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Debate from "../pages/debate.jsx";
import * as api from "../assets/js/api.js";

afterEach(cleanup);

const mockDebateData = {
  id: 683,
  title: "Demands for Grants 2024–25: Ministry of Rural Development",
  date: "2024-03-12",
  term: 17,
  session: 15,
  session_label: "Session 15",
  kind: "bill",
  kind_label: "Bill",
  type: "Government Bill",
  laid: false,
  source_url: "https://sansad.in/ls/debates/2024-03-12/58204",
  speeches: [
    {
      id: 101,
      start: 1,
      end: 2,
      words: 1204,
      turns: 2,
      interruptions: 0,
      member: "Anil Kumar",
      member_id: 1,
      party: "BJP",
      seat: "Patna Sahib",
      state: "Bihar",
      summary: "Speaks on rural fund releases.",
      tags: [{ name: "MGNREGA", slug: "mgnrega" }],
    },
    {
      id: 102,
      start: 3,
      end: 4,
      words: 388,
      turns: 2,
      interruptions: 1,
      member: "Sunita Meena",
      member_id: 2,
      party: "BSP",
      seat: "Dausa",
      state: "Rajasthan",
      summary: "Questions job card deletions.",
      tags: [{ name: "Job cards", slug: "job-cards" }],
    },
  ],
  turn_list: [
    {
      seq: 1,
      speech: 101,
      member: "Anil Kumar",
      member_id: 1,
      party: "BJP",
      seat: "Patna Sahib",
      attributed: true,
      kind: "member",
      role_in_debate: "speech",
      words: 1000,
      text: "Sir, I rise to support the Demands for Grants.",
    },
    {
      seq: 2,
      speech: 101,
      member: "Anil Kumar",
      member_id: 1,
      party: "BJP",
      seat: "Patna Sahib",
      attributed: true,
      kind: "member",
      role_in_debate: "speech",
      words: 204,
      text: "We need further allocation for rural roads.",
    },
    {
      seq: 3,
      speech: 102,
      member: "Sunita Meena",
      member_id: 2,
      party: "BSP",
      seat: "Dausa",
      attributed: true,
      kind: "member",
      role_in_debate: "speech",
      words: 300,
      text: "Many poor families have been left out.",
    },
    {
      seq: 4,
      speech: 102,
      member: null,
      member_id: null,
      attributed: false,
      kind: "presiding",
      role_kind: "presiding",
      role_in_debate: "interruption",
      inside_speech: 102,
      words: 88,
      text: "Please conclude your remarks now.",
    },
  ],
  people: [
    {
      id: 1,
      name: "Anil Kumar",
      party: "BJP",
      seat: "Patna Sahib",
      speeches: 1,
      turns: 2,
      words: 1204,
      first: 1,
    },
    {
      id: 2,
      name: "Sunita Meena",
      party: "BSP",
      seat: "Dausa",
      speeches: 1,
      turns: 1,
      words: 300,
      first: 3,
    },
  ],
  unidentified: { speeches: 0, turns: 0, words: 0 },
  silent: [
    {
      member_id: 3,
      name: "Rajiv Pratap Rudy",
      party: "BJP",
      seat: "Saran",
    },
  ],
  tags: [
    { name: "MGNREGA", slug: "mgnrega", speeches: 1 },
    { name: "Job cards", slug: "job-cards", speeches: 1 },
  ],
  same_day: [
    {
      id: 684,
      title: "Statement by Minister",
      kind_label: "Statement",
      speeches: 4,
    },
  ],
};

describe("Debate page", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches debate data and renders all sections", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValue(mockDebateData);

    render(
      <MemoryRouter initialEntries={["/debate/683"]}>
        <Routes>
          <Route path="/debate/:id" element={<Debate />} />
        </Routes>
      </MemoryRouter>
    );

    // Initial loading indicator
    expect(screen.getByText("Debate")).toBeTruthy();

    // Wait for data load
    await waitFor(() => {
      expect(
        screen.getByText("Demands for Grants 2024–25: Ministry of Rural Development")
      ).toBeTruthy();
    });

    // Check tab document.title: "<title cut to 60 characters> · <formatDateLong(date)> · Torko"
    // "Demands for Grants 2024–25: Ministry of Rural Development" (57 chars)
    expect(document.title).toBe(
      "Demands for Grants 2024–25: Ministry of Rural Development · 12 Mar 2024 · Torko"
    );

    // Check Glance section
    expect(screen.getByText("At a glance")).toBeTruthy();
    expect(screen.getByText("words in all speeches")).toBeTruthy();

    // Check Discussed section
    expect(screen.getByText("What was discussed")).toBeTruthy();

    // Check Who Spoke section
    expect(screen.getByText("Who spoke")).toBeTruthy();
    expect(screen.getByText("Listed but did not speak")).toBeTruthy();
    expect(screen.getByText("Rajiv Pratap Rudy")).toBeTruthy();

    // Check Transcript section
    expect(screen.getByText("The debate")).toBeTruthy();

    // Check Same day and Method/Source
    expect(screen.getByText(/Other debates on\s+12 Mar 2024/)).toBeTruthy();
    expect(screen.getByText("How Torko counts")).toBeTruthy();
    expect(screen.getByText("Source")).toBeTruthy();
  });

  it("handles 404 error state and sets document.title", async () => {
    vi.spyOn(api, "getJSON").mockRejectedValue({
      status: 404,
      message: "Debate not found",
    });

    render(
      <MemoryRouter initialEntries={["/debate/999999999"]}>
        <Routes>
          <Route path="/debate/:id" element={<Debate />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Page not found")).toBeTruthy();
    });

    expect(document.title).toBe("Page not found · Torko");
  });

  it("handles debates with 0 speeches gracefully", async () => {
    const emptyDebate = {
      ...mockDebateData,
      speeches: [],
      turn_list: [
        {
          seq: 1,
          speech: null,
          member: null,
          kind: "presiding",
          role_kind: "presiding",
          role_in_debate: "between",
          words: 10,
          text: "The House stands adjourned.",
        },
      ],
      people: [],
      tags: [],
      silent: [],
      same_day: [],
    };

    vi.spyOn(api, "getJSON").mockResolvedValue(emptyDebate);

    render(
      <MemoryRouter initialEntries={["/debate/64920"]}>
        <Routes>
          <Route path="/debate/:id" element={<Debate />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText("Demands for Grants 2024–25: Ministry of Rural Development")
      ).toBeTruthy();
    });

    // Glance states no speeches
    expect(
      screen.getAllByText("This debate has no speech. It has 1 turn.").length
    ).toBeGreaterThan(0);
    // No figures rendered
    expect(screen.queryByText("words in all speeches")).toBeNull();
    // Transcript rendered
    expect(screen.getByText("The House stands adjourned.")).toBeTruthy();
  });
});

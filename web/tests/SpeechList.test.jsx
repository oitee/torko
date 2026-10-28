import React from "react";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { clearCache } from "../assets/js/api.js";
import SpeechList from "../components/SpeechList.jsx";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

beforeEach(() => {
  clearCache();
});

describe("SpeechList", () => {
  const fakeSpeechesResponse = {
    total: 45,
    page: 1,
    per_page: 20,
    pages: 3,
    speeches: [
      {
        id: 1,
        date: "2024-03-12",
        term: 17,
        kind_label: "Bill",
        debate: "First Debate",
        member: "Om Birla",
        member_id: 225,
        party: "BJP",
        seat: "Kota",
        summary: "Speech summary.",
        excerpt: null,
        words: 500,
        tags: [{ name: "Arrears", slug: "arrears" }],
      },
    ],
  };

  it("fetches speeches and displays count header and rows", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => fakeSpeechesResponse,
    });

    render(
      <MemoryRouter initialEntries={["/"]}>
        <SpeechList filters={{ tag: "arrears" }} />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Speeches 1 to 20 of 45")).toBeTruthy();
    });

    expect(screen.getByText("First Debate")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Next →" })).toBeTruthy();
    expect(screen.queryByRole("link", { name: "← Previous" })).toBeNull();
  });

  it("capitalizes custom noun in count string", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        ...fakeSpeechesResponse,
        total: 10,
        speeches: [fakeSpeechesResponse.speeches[0]],
      }),
    });

    render(
      <MemoryRouter initialEntries={["/"]}>
        <SpeechList noun="interruptions" />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Interruptions 1 to 10 of 10")).toBeTruthy();
    });
  });

  it("shows Previous and Next links on middle page", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        ...fakeSpeechesResponse,
        page: 2,
      }),
    });

    render(
      <MemoryRouter initialEntries={["/?page=2"]}>
        <SpeechList />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Speeches 21 to 40 of 45")).toBeTruthy();
    });

    expect(screen.getByRole("link", { name: "← Previous" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Next →" })).toBeTruthy();
  });

  it("shows empty state when no speeches are returned", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        total: 0,
        page: 1,
        per_page: 20,
        pages: 0,
        speeches: [],
      }),
    });

    render(
      <MemoryRouter initialEntries={["/"]}>
        <SpeechList />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText("No speeches match. Remove a filter and try again.")
      ).toBeTruthy();
    });
  });

  it("shows error state and handles retry", async () => {
    globalThis.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    render(
      <MemoryRouter initialEntries={["/"]}>
        <SpeechList />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText("The server could not answer. Try again.")
      ).toBeTruthy();
    });

    globalThis.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => fakeSpeechesResponse,
    });

    const retryButton = screen.getByRole("button", { name: "Try again" });
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText("Speeches 1 to 20 of 45")).toBeTruthy();
    });
  });
});

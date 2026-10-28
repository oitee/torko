import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SpeakerLine from "../components/SpeakerLine.jsx";

afterEach(cleanup);

describe("SpeakerLine", () => {
  it("renders a link to the member page with seat and party", () => {
    const speech = {
      member: "Mahua Moitra",
      member_id: 1052,
      party: "AITC",
      seat: "Krishnanagar",
      printed: null,
    };

    render(
      <MemoryRouter>
        <SpeakerLine speech={speech} />
      </MemoryRouter>
    );

    const link = screen.getByRole("link", { name: "Mahua Moitra" });
    expect(link.getAttribute("href")).toBe("/member/1052");
    expect(screen.getByText("· Krishnanagar · AITC", { exact: false })).toBeTruthy();
  });

  it("leaves out null seat and its dot", () => {
    const speech = {
      member: "Mahua Moitra",
      member_id: 1052,
      party: "AITC",
      seat: null,
    };

    render(
      <MemoryRouter>
        <SpeakerLine speech={speech} />
      </MemoryRouter>
    );

    expect(screen.getByText("· AITC", { exact: false })).toBeTruthy();
    expect(screen.queryByText(/Krishnanagar/)).toBeNull();
  });

  it("leaves out null party and its dot", () => {
    const speech = {
      member: "Mahua Moitra",
      member_id: 1052,
      party: null,
      seat: "Krishnanagar",
    };

    render(
      <MemoryRouter>
        <SpeakerLine speech={speech} />
      </MemoryRouter>
    );

    expect(screen.getByText("· Krishnanagar", { exact: false })).toBeTruthy();
    expect(screen.queryByText(/AITC/)).toBeNull();
  });

  it("shows Speaker not identified when member is missing", () => {
    const speech = {
      member: null,
      member_id: null,
      party: null,
      seat: null,
      printed: "DIVISION AYES 19",
    };

    const { container } = render(<SpeakerLine speech={speech} />);

    expect(screen.getByText("Speaker not identified")).toBeTruthy();
    expect(container.firstChild.classList.contains("speaker-line--unidentified")).toBe(true);
    expect(screen.queryByRole("link")).toBeNull();
    expect(screen.queryByText("DIVISION AYES 19")).toBeNull();
    expect(screen.queryByText("Unattributed")).toBeNull();
  });

  it("handles missing speech prop gracefully", () => {
    render(<SpeakerLine />);
    expect(screen.getByText("Speaker not identified")).toBeTruthy();
  });
});

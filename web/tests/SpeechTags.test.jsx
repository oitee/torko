import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SpeechTags from "../pages/speech/SpeechTags.jsx";

afterEach(cleanup);

describe("SpeechTags", () => {
  const sampleTags = [
    {
      name: "Tag Dictionary",
      slug: "tag-dictionary",
      source: "dictionary",
      why: [
        {
          item_name: "Dictionary Item",
          marks: [{ seq: 1, start: 5, end: 15 }],
          subject: "Sample Subject",
        },
      ],
    },
    {
      name: "Tag LLM",
      slug: "tag-llm",
      source: "llm",
      why: [
        {
          item_name: "LLM Item",
          marks: [],
          subject: null,
        },
      ],
    },
    {
      name: "Tag Summary",
      slug: "tag-summary",
      source: "summary_tag",
      why: [],
    },
  ];

  it("sorts tags: llm first, then dictionary, then summary_tag", () => {
    render(
      <MemoryRouter>
        <SpeechTags tags={sampleTags} speechId={123} />
      </MemoryRouter>
    );

    const chips = screen.getAllByRole("button", { pressed: false });
    expect(chips[0].textContent).toContain("Tag LLM");
    expect(chips[1].textContent).toContain("Tag Dictionary");
    expect(chips[2].textContent).toContain("Tag Summary");
  });

  it("renders the source legend under the chips", () => {
    const { container } = render(
      <MemoryRouter>
        <SpeechTags tags={sampleTags} speechId={123} />
      </MemoryRouter>
    );

    const legend = container.querySelector(".speech-tags__legend");
    expect(legend).toBeTruthy();
    expect(legend.textContent).toContain("the model named it");
    expect(legend.textContent).toContain("a word matched");
    expect(legend.textContent).toContain("near in meaning");
  });

  it("opens the panel when a chip is selected, with the sentence, show words, the tag link and the report link", () => {
    const onToggleMarks = vi.fn();

    render(
      <MemoryRouter>
        <SpeechTags
          tags={sampleTags}
          speechId={123}
          onToggleMarks={onToggleMarks}
        />
      </MemoryRouter>
    );

    const chip = screen.getByRole("button", { name: /Tag Dictionary/ });
    fireEvent.click(chip);
    expect(chip.getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByRole("link", { name: "All speeches on Tag Dictionary" }).getAttribute("href")).toBe(
      "/tag/tag-dictionary"
    );

    expect(
      screen.getByText(/The words “Dictionary Item” appear 1 time in this speech\./)
    ).toBeTruthy();
    expect(screen.getByText("Specific subject: Sample Subject.")).toBeTruthy();

    const showWordsBtn = screen.getByRole("button", { name: "Show the words" });
    fireEvent.click(showWordsBtn);
    expect(onToggleMarks).toHaveBeenCalledWith(
      [{ seq: 1, start: 5, end: 15 }],
      "Tag Dictionary"
    );

    const reportLink = screen.getByRole("link", { name: "Report a wrong tag" });
    expect(reportLink.getAttribute("href")).toContain(
      "mailto:hello@otee.dev?subject=Wrong%20tag%3A%20Tag%20Dictionary%20(speech%20123)"
    );
  });

  it("shows Show all button when there are more than 8 tags", () => {
    const manyTags = Array.from({ length: 12 }, (_, i) => ({
      name: `Tag ${i + 1}`,
      slug: `tag-${i + 1}`,
      source: "llm",
    }));

    render(
      <MemoryRouter>
        <SpeechTags tags={manyTags} speechId={123} />
      </MemoryRouter>
    );

    expect(screen.getByRole("button", { name: "Show all 12 tags" })).toBeTruthy();
    expect(screen.getAllByRole("button", { name: /^the model named it: Tag/ }).length).toBe(8);

    fireEvent.click(screen.getByRole("button", { name: "Show all 12 tags" }));
    expect(screen.getAllByRole("button", { name: /^the model named it: Tag/ }).length).toBe(12);
  });
});

import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SpeechTags, { reportHref } from "../pages/speech/SpeechTags.jsx";

afterEach(cleanup);

const TAGS = [
  { name: "Tag Summary", slug: "tag-summary", source: "summary_tag" },
  { name: "Tag Dictionary", slug: "tag-dictionary", source: "dictionary" },
  { name: "Tag LLM", slug: "tag-llm", source: "llm" },
];

function renderTags(tags = TAGS) {
  return render(
    <MemoryRouter>
      <SpeechTags tags={tags} speechId={178379} />
    </MemoryRouter>
  );
}

describe("SpeechTags", () => {
  it("links each tag to its page, model tags first, with no source marks and no panel", () => {
    renderTags();
    const links = screen.getAllByRole("link").filter((a) => a.getAttribute("href").startsWith("/tag/"));
    expect(links.map((a) => a.getAttribute("href"))).toEqual(["/tag/tag-llm", "/tag/tag-dictionary", "/tag/tag-summary"]);
    expect(screen.queryByText(/the model named it/)).toBeNull();
    expect(screen.queryByText(/Select a tag to see why/)).toBeNull();
  });

  it("shows 8 tags, then all of them after Show all", () => {
    const many = Array.from({ length: 11 }, (_, i) => ({ name: `Tag ${i}`, slug: `tag-${i}`, source: "llm" }));
    renderTags(many);
    expect(screen.getAllByRole("link").filter((a) => a.getAttribute("href").startsWith("/tag/")).length).toBe(8);
    fireEvent.click(screen.getByRole("button", { name: "Show all 11 tags" }));
    expect(screen.getAllByRole("link").filter((a) => a.getAttribute("href").startsWith("/tag/")).length).toBe(11);
  });

  it("has one link to report a wrong tag, with the speech and all its tags in the email", () => {
    renderTags();
    const href = screen.getByRole("link", { name: "Report a wrong tag" }).getAttribute("href");
    expect(href).toBe(reportHref([TAGS[2], TAGS[1], TAGS[0]], 178379, window.location.href));
    const body = decodeURIComponent(href.split("body=")[1]);
    expect(decodeURIComponent(href.split("subject=")[1].split("&")[0])).toBe("Wrong tag on speech 178379");
    expect(body).toContain("The tags of this speech: Tag LLM, Tag Dictionary, Tag Summary");
  });

  it("shows nothing for a speech with no tags", () => {
    const { container } = renderTags([]);
    expect(container.innerHTML).toBe("");
  });
});

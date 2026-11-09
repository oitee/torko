import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import PageLayout from "../components/PageLayout.jsx";
import Breadcrumb from "../components/Breadcrumb.jsx";
import PageAnswer from "../components/PageAnswer.jsx";
import Margin from "../components/Margin.jsx";

afterEach(cleanup);

describe("PageLayout", () => {
  it("renders breadcrumb, answer, main column, and margin", () => {
    render(
      <MemoryRouter>
        <PageLayout
          breadcrumb={<Breadcrumb items={[{ label: "Section" }, { label: "Current" }]} />}
          answer={<PageAnswer>This is the plain answer.</PageAnswer>}
          margin={<div>Margin content</div>}
        >
          <div>Main content</div>
        </PageLayout>
      </MemoryRouter>
    );

    expect(screen.getByRole("navigation", { name: "Breadcrumb" })).toBeTruthy();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toContain("This is the plain answer.");
    expect(screen.getByText("Margin content")).toBeTruthy();
    expect(screen.getByText("Main content")).toBeTruthy();
  });

  it("renders correctly without breadcrumb and without margin", () => {
    render(
      <PageLayout answer={<PageAnswer>Only answer</PageAnswer>}>
        <div>Only main</div>
      </PageLayout>
    );

    expect(screen.queryByRole("navigation", { name: "Breadcrumb" })).toBeNull();
    expect(screen.queryByLabelText("Page margin")).toBeNull();
    expect(screen.getByText("Only main")).toBeTruthy();
  });

  it("wraps raw margin content in Margin component if not already wrapped", () => {
    const { container } = render(
      <PageLayout margin={<span>Raw count text</span>}>
        <div>Main body</div>
      </PageLayout>
    );

    expect(container.querySelector(".margin")).toBeTruthy();
    expect(screen.getByText("Raw count text")).toBeTruthy();
  });

  it("preserves an existing Margin element without double-wrapping", () => {
    const { container } = render(
      <PageLayout margin={<Margin label="Custom label">Custom content</Margin>}>
        <div>Main body</div>
      </PageLayout>
    );

    const marginElements = container.querySelectorAll(".margin");
    expect(marginElements.length).toBe(1);
    expect(screen.getByText("Custom content")).toBeTruthy();
  });
});

describe("PageLayout notes", () => {
  it("puts the notes of a data page in one band after the main column, with no margin", () => {
    const { container } = render(
      <PageLayout answer={<p>Answer</p>} notes={<p>How Torko counts</p>}>
        <p>Main</p>
      </PageLayout>
    );
    const notes = screen.getByRole("region", { name: "Counts, method and source" });
    expect(notes.textContent).toBe("How Torko counts");
    expect(container.querySelector(".page-layout__margin")).toBeNull();
    // The notes come after the grid of the main column.
    const grid = container.querySelector(".page-layout__grid");
    expect(grid.compareDocumentPosition(notes) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});

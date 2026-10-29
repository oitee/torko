import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import MethodLabels from "../pages/method/MethodLabels.jsx";
import methodAnswer from "./fixtures/method/method.json";

afterEach(cleanup);

function renderLabels(example) {
  return render(
    <MemoryRouter>
      <MethodLabels example={example} />
    </MemoryRouter>
  );
}

describe("MethodLabels", () => {
  it("lists each printed name with its turns, and links to the member", () => {
    renderLabels(methodAnswer.example);
    expect(screen.getAllByRole("row")).toHaveLength(1 + methodAnswer.example.labels.length);
    expect(screen.getByText("SHRI ADHIR RANJAN CHOWDHURY (BAHARAMPUR)")).toBeTruthy();
    expect(screen.getByText("981")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Adhir Ranjan Chowdhury" }).getAttribute("href")).toBe("/member/368");
    expect(screen.getByText(/The 10 most frequent printed names of one member/)).toBeTruthy();
  });

  it("marks a name in Devanagari as Hindi", () => {
    renderLabels(methodAnswer.example);
    expect(screen.getByText("श्री अधीर रंजन चौधरी").getAttribute("lang")).toBe("hi");
    expect(screen.getByText("SHRI ADHIR CHOWDHURY").getAttribute("lang")).toBeNull();
  });

  it("shows nothing without an example", () => {
    expect(renderLabels(null).container.innerHTML).toBe("");
    cleanup();
    expect(renderLabels({ member_id: 1, name: "X", labels: [] }).container.innerHTML).toBe("");
  });
});

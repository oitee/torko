import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import MethodLabels, { Stage, demoOrder, letters } from "../pages/method/MethodLabels.jsx";
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
  it("joins each printed name with its turns into the member, and links to the member", () => {
    renderLabels(methodAnswer.example);
    expect(screen.getByRole("img").getAttribute("aria-label")).toBe("10 printed names join into one member, Adhir Ranjan Chowdhury.");
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

  it("groups the names by script, Hindi first, then by form: name, with constituency, with state", () => {
    expect(demoOrder(methodAnswer.example.labels).map((r) => r.label)).toEqual([
      "श्री अधीर रंजन चौधरी",
      "श्रीअधीररंजनचौधरी",
      "श्री अधीर रंजन चौधरी ( बहरामपुर )",
      "SHRI ADHIR RANJAN CHOWDHURY",
      "SHRI ADHIR CHOWDHURY",
      "SHRI ADHIR CHOWDHARY",
      "SHRI ADHIR RANJAN CHOWDHURY (BAHARAMPUR)",
      "SHRI ADHIR CHOWDHURY (BAHARAMPUR)",
      "SHRI ADHIR CHOWDHURY (BERHAMPORE, WEST BENGAL)",
      "SHRI ADHIR CHOWDHARY (BERHAMPORE, WEST BENGAL)",
    ]);
  });

  it("cuts a Hindi name into whole letters, so no mark stands alone", () => {
    expect(letters("श्री अधीर रंजन चौधरी")).toEqual(["श्री", " ", "अ", "धी", "र", " ", "रं", "ज", "न", " ", "चौ", "ध", "री"]);
    expect(letters("( बहरामपुर )").join("")).toBe("( बहरामपुर )");
    expect(letters("SHRI A")).toEqual(["S", "H", "R", "I", " ", "A"]);
  });

  it("never starts a stage span with a Hindi mark while a name types in", () => {
    const prev = letters("श्री अधीर रंजन चौधरी");
    const target = letters("श्री अधीर रंजन चौधरी ( बहरामपुर )");
    for (let upto = 0; upto <= target.length; upto++) {
      const { container } = render(<Stage stage={{ prev, target, upto, count: 322 }} />);
      for (const span of container.querySelectorAll(".method-labels__ch")) {
        expect(span.textContent).not.toMatch(/^[\u093A-\u094F]/);
      }
      cleanup();
    }
  });

  it("shows nothing without an example", () => {
    expect(renderLabels(null).container.innerHTML).toBe("");
    cleanup();
    expect(renderLabels({ member_id: 1, name: "X", labels: [] }).container.innerHTML).toBe("");
  });
});

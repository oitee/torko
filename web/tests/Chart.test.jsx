import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Chart from "../components/Chart.jsx";

afterEach(cleanup);

describe("Chart component", () => {
  it("renders chart title and horizontal bars with correct widths", () => {
    const rows = [
      { label: "Agriculture", n: 100 },
      { label: "Finance", n: 50 },
      { label: "Defence", n: 25 },
    ];

    render(
      <MemoryRouter>
        <Chart title="Speeches by Ministry" rows={rows} />
      </MemoryRouter>
    );

    expect(
      screen.getByRole("heading", { name: "Speeches by Ministry" })
    ).toBeTruthy();

    const bar0 = screen.getByTestId("chart-bar-0");
    const bar1 = screen.getByTestId("chart-bar-1");
    const bar2 = screen.getByTestId("chart-bar-2");

    expect(bar0.style.width).toBe("100%");
    expect(bar1.style.width).toBe("50%");
    expect(bar2.style.width).toBe("25%");

    // Default bar color is var(--ink-2)
    expect(bar0.style.backgroundColor).toBe("var(--ink-2)");
  });

  it("formats values with shareOf when total is provided, and formatNumber without", () => {
    const rows = [{ label: "Topic A", n: 20 }];

    const { unmount } = render(
      <MemoryRouter>
        <Chart title="Topics" rows={rows} total={100} />
      </MemoryRouter>
    );

    // With total=100: 20.0% (20 of 100)
    expect(screen.getAllByText("20.0% (20 of 100)").length).toBeGreaterThan(0);
    unmount();

    render(
      <MemoryRouter>
        <Chart title="Topics" rows={rows} />
      </MemoryRouter>
    );

    // Without total: 20
    expect(screen.getAllByText("20").length).toBeGreaterThan(0);
  });

  it("renders links for rows with href", () => {
    const rows = [{ label: "Wages", n: 42, href: "/tag/wages" }];

    render(
      <MemoryRouter>
        <Chart title="Tags" rows={rows} />
      </MemoryRouter>
    );

    const links = screen.getAllByRole("link", { name: "Wages" });
    expect(links.length).toBeGreaterThan(0);
    expect(links[0].getAttribute("href")).toBe("/tag/wages");
  });

  it("aggregates parties beyond the top 6 into 'Others'", () => {
    const rows = [
      { label: "BJP", n: 240 },
      { label: "INC", n: 99 },
      { label: "SP", n: 37 },
      { label: "AITC", n: 29 },
      { label: "DMK", n: 22 },
      { label: "TDP", n: 16 },
      { label: "JDU", n: 12 },
      { label: "AAP", n: 3 },
    ];

    render(
      <MemoryRouter>
        <Chart title="Parties" rows={rows} party />
      </MemoryRouter>
    );

    // 6 largest keep their own rows: BJP, INC, SP, AITC, DMK, TDP
    expect(screen.getAllByText("BJP").length).toBeGreaterThan(0);
    expect(screen.getAllByText("INC").length).toBeGreaterThan(0);
    expect(screen.getAllByText("SP").length).toBeGreaterThan(0);
    expect(screen.getAllByText("AITC").length).toBeGreaterThan(0);
    expect(screen.getAllByText("DMK").length).toBeGreaterThan(0);
    expect(screen.getAllByText("TDP").length).toBeGreaterThan(0);

    // JDU (12) + AAP (3) = 15 in "Others"
    expect(screen.getAllByText("Others").length).toBeGreaterThan(0);
    expect(screen.getAllByText("15").length).toBeGreaterThan(0);

    // Total rows displayed: 6 + 1 = 7 rows
    const othersBar = screen.getByTestId("chart-bar-6");
    expect(othersBar.style.backgroundColor).toBe("var(--control)");
  });

  it("uses token for known party, derived shades for party with colour, and var(--control) for party with no colour", () => {
    const rows = [
      { label: "BJP", n: 100 }, // known token: bjp
      { label: "AAP", n: 80, colour: "#0066A4" }, // unknown token, valid colour
      { label: "IND", n: 60 }, // unknown token, no colour
    ];

    render(
      <MemoryRouter>
        <Chart title="Parties" rows={rows} party />
      </MemoryRouter>
    );

    const bjpBar = screen.getByTestId("chart-bar-0");
    const aapBar = screen.getByTestId("chart-bar-1");
    const indBar = screen.getByTestId("chart-bar-2");

    // BJP uses var(--party-bjp)
    expect(bjpBar.style.backgroundColor).toBe("var(--party-bjp)");

    // AAP has class chart__bar--derived and CSS variables --bar-light and --bar-dark
    expect(aapBar.classList.contains("chart__bar--derived")).toBe(true);
    expect(aapBar.style.getPropertyValue("--bar-light")).toBeTruthy();
    expect(aapBar.style.getPropertyValue("--bar-dark")).toBeTruthy();

    // IND has no token and no colour -> var(--control)
    expect(indBar.style.backgroundColor).toBe("var(--control)");
  });

  it("handles table accessibility, caption, and toggling between chart and table", () => {
    const rows = [
      { label: "Lok Sabha 17", n: 500 },
      { label: "Lok Sabha 18", n: 250 },
    ];

    render(
      <MemoryRouter>
        <Chart title="Terms Comparison" rows={rows} />
      </MemoryRouter>
    );

    const table = screen.getByRole("table");
    expect(table).toBeTruthy();

    // Caption contains title
    const caption = table.querySelector("caption");
    expect(caption).toBeTruthy();
    expect(caption.textContent).toBe("Terms Comparison");

    // Initially table is visually hidden via sr-only class
    expect(table.classList.contains("sr-only")).toBe(true);

    const toggleButton = screen.getByRole("button", { name: "Show as table" });
    expect(toggleButton).toBeTruthy();

    // Click toggle button to show table
    fireEvent.click(toggleButton);

    expect(table.classList.contains("sr-only")).toBe(false);
    expect(toggleButton.textContent).toBe("Show as chart");

    // Click again to toggle back to chart
    fireEvent.click(toggleButton);

    expect(table.classList.contains("sr-only")).toBe(true);
    expect(toggleButton.textContent).toBe("Show as table");
  });

  it("handles empty or missing rows gracefully without crashing", () => {
    const { container } = render(
      <MemoryRouter>
        <Chart title="Empty Chart" rows={[]} />
      </MemoryRouter>
    );

    expect(container).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: "Empty Chart" })
    ).toBeTruthy();
  });
});

import React, { useState } from "react";
import { Link } from "react-router-dom";
import Button from "./Button.jsx";
import { formatNumber, shareOf } from "../assets/js/format.js";
import { partyShades } from "../assets/js/colour.js";
import "./Chart.css";

// Five party codes with handcrafted tokens in tokens.css.
const KNOWN_PARTY_TOKENS = new Set(["bjp", "inc", "aitc", "tdp", "bsp"]);

// The Chart component displays a horizontal bar chart with accessible table toggle.
export default function Chart({ title, rows = [], total, party = false }) {
  const [showTable, setShowTable] = useState(false);

  const safeRows = Array.isArray(rows) ? rows : [];

  // When party is true, sort and pick the top 6 rows. Aggregate the rest into "Others".
  let displayRows = [];
  if (party) {
    const sorted = [...safeRows].sort(
      (a, b) => (Number(b.n) || 0) - (Number(a.n) || 0)
    );
    if (sorted.length > 6) {
      const top6 = sorted.slice(0, 6);
      const others = sorted.slice(6);
      const othersSum = others.reduce(
        (sum, r) => sum + (Number(r.n) || 0),
        0
      );
      displayRows = [
        ...top6,
        {
          label: "Others",
          n: othersSum,
          isOthers: true,
        },
      ];
    } else {
      displayRows = sorted;
    }
  } else {
    displayRows = safeRows;
  }

  // Calculate the maximum value so the longest bar fills 100% width.
  const maxN = Math.max(0, ...displayRows.map((r) => Number(r.n) || 0));

  // Format a row value either as a share percentage or as a formatted count.
  function formatRowValue(n) {
    if (total !== undefined && total !== null) {
      return shareOf(n, total);
    }
    return formatNumber(n);
  }

  return (
    <div className="chart">
      {title && <h3 className="chart__title">{title}</h3>}

      {/* Accessible data table: visually hidden by default, accessible to screen readers */}
      <table
        className={`chart__table ${showTable ? "" : "sr-only"}`}
        aria-hidden={!showTable ? undefined : undefined}
      >
        <caption>{title || "Chart data"}</caption>
        <thead>
          <tr>
            <th scope="col">Label</th>
            <th scope="col">
              {total !== undefined && total !== null ? "Share" : "Count"}
            </th>
          </tr>
        </thead>
        <tbody>
          {displayRows.map((row, idx) => {
            const formatted = formatRowValue(row.n);
            const key = row.key || `${row.label || ""}-${idx}`;
            return (
              <tr key={key}>
                <td>
                  {row.href ? (
                    <Link to={row.href}>{row.label}</Link>
                  ) : (
                    row.label
                  )}
                </td>
                <td>{formatted}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Visual horizontal bars */}
      <div
        className={`chart__bars ${showTable ? "sr-only" : ""}`}
        aria-hidden={showTable ? "true" : undefined}
      >
        <ul className="chart__list" role="list">
          {displayRows.map((row, idx) => {
            const nVal = Number(row.n) || 0;
            const widthPercent = maxN > 0 ? (nVal / maxN) * 100 : 0;
            const formatted = formatRowValue(row.n);
            const key = row.key || `${row.label || ""}-${idx}`;

            let barStyle = {
              width: `${widthPercent}%`,
            };
            let barClass = "chart__bar";

            if (row.isOthers) {
              barStyle.backgroundColor = "var(--control)";
              barClass += " chart__bar--control";
            } else if (party) {
              const code = String(row.label || "").trim().toLowerCase();
              if (KNOWN_PARTY_TOKENS.has(code)) {
                barStyle.backgroundColor = `var(--party-${code})`;
                barClass += " chart__bar--token";
              } else if (row.colour) {
                const shades = partyShades(row.colour);
                if (shades) {
                  barStyle["--bar-light"] = shades.light;
                  barStyle["--bar-dark"] = shades.dark;
                  barClass += " chart__bar--derived";
                } else {
                  barStyle.backgroundColor = "var(--control)";
                  barClass += " chart__bar--control";
                }
              } else {
                barStyle.backgroundColor = "var(--control)";
                barClass += " chart__bar--control";
              }
            } else {
              barStyle.backgroundColor = "var(--ink-2)";
            }

            return (
              <li key={key} className="chart__row">
                <span className="chart__label">
                  {row.href ? (
                    <Link to={row.href} className="chart__link">
                      {row.label}
                    </Link>
                  ) : (
                    row.label
                  )}
                </span>
                <div className="chart__track">
                  <div
                    className={barClass}
                    style={barStyle}
                    data-testid={`chart-bar-${idx}`}
                  />
                </div>
                <span className="chart__value">{formatted}</span>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Toggle between chart and table view */}
      <div className="chart__toggle">
        <Button
          variant="text"
          onClick={() => setShowTable((prev) => !prev)}
        >
          {showTable ? "Show as chart" : "Show as table"}
        </Button>
      </div>
    </div>
  );
}

export { Chart };

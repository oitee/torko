import React from "react";
import { countOf, termLong } from "../../assets/js/format.js";
import "./TagTermBar.css";

export const TERM_LABELS = {
  13: "13th · 1999–2004",
  14: "14th · 2004–09",
  15: "15th · 2009–14",
  16: "16th · 2014–19",
  17: "17th · 2019–24",
  18: "18th · 2024–",
};

// TagTermBar displays Lok Sabha term filter buttons and the count meta line.
export default function TagTermBar({ tag, selectedTerm = "", onTermChange }) {
  if (!tag) return null;

  const sessions = Array.isArray(tag.sessions) ? tag.sessions : [];

  const availableTerms = Array.from(
    new Set(
      sessions
        .map((s) => Number(s.term))
        .filter((t) => !Number.isNaN(t) && t >= 13 && t <= 18)
    )
  ).sort((a, b) => a - b);

  const isAll = !selectedTerm || selectedTerm === "all";

  // Total speeches for the selected term from sessions
  const termSpeeches = !isAll
    ? sessions
        .filter((s) => String(s.term) === String(selectedTerm))
        .reduce((sum, s) => sum + (Number(s.n) || 0), 0)
    : null;

  return (
    <div className="tag-term-bar">
      <div className="tag-term-bar__row">
        <span className="tag-term-bar__label">Lok Sabha term</span>
        <div className="tag-term-bar__buttons" role="group" aria-label="Lok Sabha terms">
          <button
            type="button"
            className={`tag-term-button ${isAll ? "tag-term-button--selected" : ""}`}
            aria-pressed={isAll}
            onClick={() => onTermChange("")}
          >
            All terms
          </button>
          {availableTerms.map((termNum) => {
            const isSelected = String(selectedTerm) === String(termNum);
            const label = TERM_LABELS[termNum] || `${termNum}th`;
            return (
              <button
                key={termNum}
                type="button"
                className={`tag-term-button ${
                  isSelected ? "tag-term-button--selected" : ""
                }`}
                aria-pressed={isSelected}
                onClick={() => onTermChange(String(termNum))}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {!isAll && termSpeeches !== null && (
        <p className="tag-term-bar__meta meta">
          {countOf(termSpeeches, tag.total, "speeches")} in the{" "}
          {termLong(selectedTerm)}
        </p>
      )}
    </div>
  );
}

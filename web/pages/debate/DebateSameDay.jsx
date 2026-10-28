import React from "react";
import { Link } from "react-router-dom";
import { formatDateLong, formatNumber } from "../../assets/js/format.js";
import "./DebateSameDay.css";

export default function DebateSameDay({ sameDay = [], date }) {
  if (!sameDay || sameDay.length === 0) {
    return null;
  }

  const headingDate = date ? formatDateLong(date) : "";

  return (
    <section className="debate-same-day" aria-labelledby="same-day-heading">
      <div className="debate-same-day__header">
        <h2 id="same-day-heading" className="debate-same-day__title">
          Other debates on {headingDate}
        </h2>
      </div>

      <ul className="debate-same-day__list">
        {sameDay.map((d) => {
          const count = d.speeches || 0;
          const spText =
            count === 0
              ? "no speeches"
              : count === 1
              ? "1 speech"
              : `${formatNumber(count)} speeches`;

          return (
            <li key={d.id} className="debate-same-day__item">
              <Link to={`/debate/${d.id}`} className="debate-same-day__link">
                {d.title}
              </Link>
              <div className="debate-same-day__meta meta">
                {d.kind_label ? `${d.kind_label} · ` : ""}
                <span className="mono">{spText}</span>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

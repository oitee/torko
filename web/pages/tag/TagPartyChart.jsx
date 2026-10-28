import React from "react";
import Chart from "../../components/Chart.jsx";
import { formatNumber, termLong } from "../../assets/js/format.js";
import "./TagPartyChart.css";

// TagPartyChart displays the party breakdown of speeches for the tag.
export default function TagPartyChart({ parties = [], selectedTerm = "" }) {
  const safeParties = Array.isArray(parties) ? parties : [];
  const termTotal = safeParties.reduce((sum, p) => sum + (Number(p.n) || 0), 0);
  const termLabel = selectedTerm ? termLong(selectedTerm) : "all terms";

  const rows = safeParties.map((p) => ({
    label: p.party,
    n: p.n,
    colour: p.colour,
  }));

  return (
    <section className="tag-party-chart" aria-labelledby="party-heading">
      <div className="tag-party-chart__header">
        <h2 id="party-heading" className="tag-party-chart__title">
          From which party
        </h2>
        <span className="tag-party-chart__meta mono">
          {formatNumber(termTotal)} speeches · {termLabel}
        </span>
      </div>

      <Chart party={true} total={termTotal} rows={rows} />

      <p className="tag-party-chart__note meta">
        Party is the member's party on the day of the speech. Parties after the
        largest 6 are counted in Others, in grey.
      </p>
    </section>
  );
}

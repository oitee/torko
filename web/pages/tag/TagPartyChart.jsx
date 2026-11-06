import React from "react";
import Chart from "../../components/Chart.jsx";
import { formatNumber, termLong } from "../../assets/js/format.js";
import "./TagPartyChart.css";

// total is the number of speeches with the tag in the chosen terms. Some of them have no party.
export default function TagPartyChart({ parties = [], selectedTerm = "", total = null }) {
  const safeParties = Array.isArray(parties) ? parties : [];
  const termTotal = safeParties.reduce((sum, p) => sum + (Number(p.n) || 0), 0);
  const termLabel = selectedTerm ? termLong(selectedTerm) : "all terms";
  const noParty = total != null ? Math.max(0, total - termTotal) : 0;

  const rows = safeParties.map((p) => ({
    label: p.party,
    n: p.n,
    colour: p.colour,
    href: p.party ? `/party/${encodeURIComponent(p.party)}` : undefined,
  }));

  return (
    <section className="tag-party-chart" aria-labelledby="party-heading">
      <div className="tag-party-chart__header">
        <h2 id="party-heading" className="tag-party-chart__title">
          From which party
        </h2>
        <span className="tag-party-chart__meta mono">
          {total != null ? `${formatNumber(termTotal)} of ${formatNumber(total)} speeches have a party` : `${formatNumber(termTotal)} speeches`} · {termLabel}
        </span>
      </div>

      <Chart party={true} total={termTotal} rows={rows} />

      <p className="tag-party-chart__note meta">
        {"Each value is the share of the speeches that have a party. "}
        {noParty > 0 ? `${formatNumber(noParty)} speeches have no party and are not shown. ` : ""}
        {"Party is the member's party on the day of the speech. Parties after the largest 6 are counted in Others, in grey."}
      </p>
    </section>
  );
}

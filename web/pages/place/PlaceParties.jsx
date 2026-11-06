import React from "react";
import { formatNumber } from "../../assets/js/format.js";
import PartyLink from "../../components/PartyLink.jsx";

const KNOWN_PARTY_TOKENS = new Set(["bjp", "inc", "aitc", "tdp", "bsp"]);

export default function PlaceParties({ parties = [] }) {
  const safeParties = Array.isArray(parties) ? parties : [];
  if (safeParties.length === 0) {
    return null;
  }

  const maxN = Math.max(1, ...safeParties.map((p) => Number(p.n) || 0));

  return (
    <section
      className="place-section place-parties"
      aria-labelledby="parties-heading"
    >
      <div className="section-header">
        <h2 id="parties-heading" className="place-section__title">
          Which parties spoke about it
        </h2>
        <span className="place-section__meta mono">Across all terms</span>
      </div>

      <div className="place-parties__grid-table">
        <div className="place-parties__table-head mono" aria-hidden="true">
          <span className="place-parties__th-party"></span>
          <span className="place-parties__th-bar"></span>
          <span className="place-parties__th-speeches">speeches</span>
          <span className="place-parties__th-per100">per 100</span>
        </div>

        <div className="place-parties__table-rows">
          {safeParties.map((p, idx) => {
            const widthPercent = (p.n / maxN) * 100;
            const code = String(p.party || "").trim().toLowerCase();

            let barStyle = {
              width: `${widthPercent}%`,
            };

            // Only the parties with a colour token in tokens.css get a colour. Every other party is control grey.
            barStyle.backgroundColor = KNOWN_PARTY_TOKENS.has(code) ? `var(--party-${code})` : "var(--control)";

            const per100Text =
              typeof p.per100 === "number"
                ? p.per100.toFixed(2)
                : p.per100 || "0.00";

            return (
              <div key={p.party || idx} className="place-parties__row">
                <span className="place-parties__party-name"><PartyLink code={p.party} /></span>

                <div className="place-parties__track">
                  <div
                    className="place-parties__bar"
                    style={barStyle}
                    data-testid={`party-bar-${idx}`}
                  />
                </div>

                <span className="place-parties__speeches-count mono">
                  {formatNumber(p.n)}
                </span>

                <span className="place-parties__per100-val mono">
                  {per100Text}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <p className="place-parties__note">
        Per 100 stops a large party from looking important only because it is large. Five parties have their own colour. All
        other parties are grey.{" "}
        <a href="#method" className="place-parties__method-link">
          Method
        </a>
      </p>
    </section>
  );
}

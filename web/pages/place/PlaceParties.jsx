import React from "react";
import { formatNumber } from "../../assets/js/format.js";
import { partyShades } from "../../assets/js/colour.js";

const KNOWN_PARTY_TOKENS = new Set(["bjp", "inc", "aitc", "tdp", "bsp"]);

const WIKIPEDIA_PARTY_HEX = {
  BJP: "#CD7407",
  INC: "#0395C8",
  SHS: "#D95A0B",
  SS: "#D95A0B",
  SHSUBT: "#D95A0B",
  NCP: "#009797",
  DMK: "#FF0D0D",
  AIADMK: "#138808",
  AITC: "#03A132",
  "CPI(M)": "#CC0000",
  CPI: "#D90000",
  PMK: "#998100",
  VCK: "#0F52BA",
  BJD: "#006400",
  "JD(U)": "#003366",
  AAP: "#0072B0",
  SP: "#E40000",
};

export default function PlaceParties({ parties = [], placeName = "" }) {
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
      <div className="place-section__header">
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
            const upperCode = String(p.party || "").trim().toUpperCase();

            let barStyle = {
              width: `${widthPercent}%`,
            };

            if (idx < 6) {
              if (KNOWN_PARTY_TOKENS.has(code)) {
                barStyle.backgroundColor = `var(--party-${code})`;
              } else if (WIKIPEDIA_PARTY_HEX[upperCode]) {
                const shades = partyShades(WIKIPEDIA_PARTY_HEX[upperCode]);
                if (shades) {
                  barStyle.backgroundColor = shades.light;
                } else {
                  barStyle.backgroundColor = "var(--control)";
                }
              } else {
                barStyle.backgroundColor = "var(--control)";
              }
            } else {
              barStyle.backgroundColor = "var(--control)";
            }

            const per100Text =
              typeof p.per100 === "number"
                ? p.per100.toFixed(2)
                : p.per100 || "0.00";

            return (
              <div key={p.party || idx} className="place-parties__row">
                <span className="place-parties__party-name">{p.party}</span>

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
        Per 100: of every 100 speeches the party made in the house, how many were
        about {placeName}. This keeps a large party from looking important only
        because it is large. Party colours follow Wikipedia. Parties after the
        largest 6 are grey.{" "}
        <a href="#method" className="place-parties__method-link">
          Method
        </a>
      </p>
    </section>
  );
}

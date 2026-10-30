import React, { useState } from "react";
import Button from "../../components/Button.jsx";
import { formatNumber, termLong, termShort } from "../../assets/js/format.js";
import { percent } from "./partyData.js";

// The top of the scale: the next round step above the highest share, so the bars do not touch the top.
// The step grows with the share, so a small party gets bars that a reader can see.
export function scaleTop(shares) {
  const max = Math.max(0, ...shares.map((s) => Number(s) || 0));
  if (max === 0) return 0.01;
  const step = max < 0.02 ? 0.005 : max < 0.05 ? 0.01 : max < 0.2 ? 0.05 : 0.1;
  return Math.min(1, Math.round(Math.ceil((max + 1e-9) / step + 1e-9) * step * 1000) / 1000);
}

// One sentence for a term.
export function termSentence(t, code) {
  const head = `${termLong(t.term)}, ${t.years}`;
  if (!t.tagged) return `${head}: no tagged ${code} speeches.`;
  const members = t.members_speaking === 1 ? "1 member spoke" : `${formatNumber(t.members_speaking)} members spoke`;
  return `${head}: ${percent(t.share_of_tagged)} of tagged speeches (${formatNumber(t.tagged)} of ${formatNumber(
    t.all_tagged
  )}). ${members}.`;
}

// PartyShareChart shows two charts on one row of terms.
// The first: the share of all tagged speeches of the House that came from the party, in each term.
// The second: the number of members who spoke for the party in each term.
// The two charts have their own scales. They share only the terms, so they are two charts, not one chart with two axes.
export default function PartyShareChart({ terms = [], code }) {
  const [active, setActive] = useState(null);
  const [showTable, setShowTable] = useState(false);
  const list = Array.isArray(terms) ? terms : [];
  if (list.length === 0) return null;

  const top = scaleTop(list.map((t) => t.share_of_tagged));
  const maxMembers = Math.max(1, ...list.map((t) => Number(t.members_speaking) || 0));
  const grid = { gridTemplateColumns: `repeat(${list.length}, minmax(0, 1fr))` };

  const handlers = (t) => ({
    onMouseEnter: () => setActive(t),
    onFocus: () => setActive(t),
    onBlur: () => setActive(null),
  });

  return (
    <section className="party-section" aria-labelledby="party-share-heading">
      <div className="party-section__header">
        <h2 id="party-share-heading" className="party-section__title">
          Share of the House, by term
        </h2>
        <span className="party-section__meta mono">of all tagged speeches</span>
      </div>

      <div className="party-box">
        <p className="party-box__readout mono" aria-live="polite">
          {active ? termSentence(active, code) : "Point at a term"}
        </p>

        <div className={showTable ? "sr-only" : "party-share"} aria-hidden={showTable ? "true" : undefined}>
          <div className="party-share__chart" onMouseLeave={() => setActive(null)}>
            <div className="party-share__scale mono" aria-hidden="true">
              <span>{percent(top)}</span>
              <span>0%</span>
            </div>
            <div className="party-share__plot" style={grid}>
              {list.map((t) => {
                const h = top > 0 ? ((Number(t.share_of_tagged) || 0) / top) * 100 : 0;
                return (
                  <div
                    key={t.term}
                    className={`party-share__col${active?.term === t.term ? " party-share__col--active" : ""}`}
                    tabIndex={0}
                    role="img"
                    aria-label={termSentence(t, code)}
                    data-testid={`party-share-${t.term}`}
                    {...handlers(t)}
                  >
                    {t.tagged > 0 && <span className="party-share__value mono">{percent(t.share_of_tagged)}</span>}
                    <div className="party-share__bar" style={{ height: `${h}%` }} />
                  </div>
                );
              })}
            </div>
          </div>

          <div className="party-share__members">
            <span className="party-share__members-title">Members who spoke</span>
            <div className="party-share__plot party-share__plot--members" style={grid}>
              {list.map((t) => {
                const h = ((Number(t.members_speaking) || 0) / maxMembers) * 100;
                return (
                  <div
                    key={t.term}
                    className={`party-share__col${active?.term === t.term ? " party-share__col--active" : ""}`}
                    aria-hidden="true"
                    onMouseEnter={() => setActive(t)}
                    data-testid={`party-members-${t.term}`}
                  >
                    {t.members_speaking > 0 && (
                      <span className="party-share__value mono">{formatNumber(t.members_speaking)}</span>
                    )}
                    <div className="party-share__bar party-share__bar--members" style={{ height: `${h}%` }} />
                  </div>
                );
              })}
            </div>
          </div>

          <div className="party-share__axis mono" style={grid} aria-hidden="true">
            {list.map((t) => (
              <span key={t.term} className="party-share__tick">
                <span className="party-share__tick-term">{termShort(t.term)}</span>
                <span className="party-share__tick-years">{t.years}</span>
              </span>
            ))}
          </div>
        </div>

        <div className={showTable ? "party-table-wrap" : "sr-only"}>
          <table className="party-table">
            <caption>{code}: share of all tagged speeches, and members who spoke, by term</caption>
            <thead>
              <tr>
                <th scope="col">Term</th>
                <th scope="col" className="party-table__num">Tagged {code} speeches</th>
                <th scope="col" className="party-table__num">All tagged speeches</th>
                <th scope="col" className="party-table__num">Share</th>
                <th scope="col" className="party-table__num">Members who spoke</th>
              </tr>
            </thead>
            <tbody>
              {list.map((t) => (
                <tr key={t.term}>
                  <td>
                    {termShort(t.term)} · {t.years}
                  </td>
                  <td className="party-table__num">{formatNumber(t.tagged)}</td>
                  <td className="party-table__num">{formatNumber(t.all_tagged)}</td>
                  <td className="party-table__num">{percent(t.share_of_tagged)}</td>
                  <td className="party-table__num">{formatNumber(t.members_speaking)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="party-box__note">
          A tagged speech is a speech with at least one tag of any kind. The party of a speech is the party of the member
          on the date of the debate. The two charts have their own scales.
        </p>

        <div className="party-box__toggle">
          <Button variant="text" onClick={() => setShowTable((v) => !v)}>
            {showTable ? "Show as chart" : "Show as table"}
          </Button>
        </div>
      </div>
    </section>
  );
}

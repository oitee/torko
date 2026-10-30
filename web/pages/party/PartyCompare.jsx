import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";
import { perThousand, subjectSentence, timesText } from "./partyData.js";

// PartyCompare draws one row for each subject: a dot for the party and a ring for all parties, on one scale.
// The scale is speeches with the subject in every 1,000 tagged speeches. The line between the two marks is the gap.
// rows: { tag, slug, n, share, base, lift }. hrefBase is "/tag/" or "/place/".
export default function PartyCompare({ id, title, meta, rows = [], code, hrefBase, empty, controls }) {
  const [active, setActive] = useState(null);
  const list = Array.isArray(rows) ? rows : [];
  const max = Math.max(0, ...list.flatMap((r) => [Number(r.share) || 0, Number(r.base) || 0]));
  const pos = (v) => (max > 0 ? ((Number(v) || 0) / max) * 100 : 0);

  return (
    <section className="party-section" aria-labelledby={id}>
      <div className="party-section__header">
        <h2 id={id} className="party-section__title">
          {title}
        </h2>
        {meta && <span className="party-section__meta mono">{meta}</span>}
      </div>

      {controls}

      <div className="party-box">
        {list.length === 0 ? (
          <p className="party-box__empty">{empty}</p>
        ) : (
          <>
            <div className="party-compare__top">
              <ul className="party-legend" aria-label="Legend">
                <li className="party-legend__item">
                  <span className="party-mark party-mark--party" aria-hidden="true" />
                  {code}
                </li>
                <li className="party-legend__item">
                  <span className="party-mark party-mark--house" aria-hidden="true" />
                  All parties
                </li>
              </ul>
              <p className="party-box__readout mono" aria-live="polite">
                {active ? subjectSentence(active, code) : "Point at a row"}
              </p>
            </div>

            <div className="party-compare__head mono" aria-hidden="true">
              <span />
              <span className="party-compare__scale">
                <span>0</span>
                <span>{perThousand(max)} per 1,000</span>
              </span>
              <span className="party-compare__num">times</span>
              <span className="party-compare__num">speeches</span>
            </div>

            <ul className="party-compare" onMouseLeave={() => setActive(null)}>
              {list.map((r) => {
                const a = pos(r.share);
                const b = pos(r.base);
                return (
                  <li
                    key={r.slug}
                    className={`party-compare__row${active?.slug === r.slug ? " party-compare__row--active" : ""}`}
                    onMouseEnter={() => setActive(r)}
                  >
                    <Link
                      to={`${hrefBase}${r.slug}`}
                      className="party-compare__label"
                      onFocus={() => setActive(r)}
                      onBlur={() => setActive(null)}
                      aria-label={subjectSentence(r, code)}
                    >
                      {r.tag}
                    </Link>
                    <span className="party-compare__track" aria-hidden="true">
                      <span
                        className="party-compare__gap"
                        style={{ left: `${Math.min(a, b)}%`, width: `${Math.abs(a - b)}%` }}
                      />
                      <span className="party-mark party-mark--house party-compare__dot" style={{ left: `${b}%` }} />
                      <span
                        className="party-mark party-mark--party party-compare__dot"
                        style={{ left: `${a}%` }}
                        data-testid={`party-dot-${r.slug}`}
                      />
                    </span>
                    <span className="party-compare__num mono">{timesText(r.lift).replace(" times", "×")}</span>
                    <span className="party-compare__num mono">{formatNumber(r.n)}</span>
                  </li>
                );
              })}
            </ul>
          </>
        )}
      </div>
    </section>
  );
}

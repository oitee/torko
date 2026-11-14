import React from "react";
import { Link } from "react-router-dom";
import { formatNumber, termShort } from "../../assets/js/format.js";
import { partyColourVars } from "../party/partyData.js";

// The charts of a term show this many parties by name. The other parties of the term make one group, "Others".
export const NAMED_PARTIES = 8;
// A cell of the grid at or above LIFT_MORE is "more than the House". At or above LIFT_MUCH it has the strong colour.
export const LIFT_MORE = 1.2;
export const LIFT_MUCH = 1.5;

// The terms of a party as a short range when they follow each other: "13th–18th LS", else a list.
export function termsText(terms) {
  if (!terms?.length) return "";
  const run = terms.every((t, i) => i === 0 || t === terms[i - 1] + 1);
  if (terms.length === 1) return termShort(terms[0]);
  return run ? `${termShort(terms[0]).replace(" LS", "")}–${termShort(terms[terms.length - 1])}` : terms.map((t) => termShort(t).replace(" LS", "")).join(", ") + " LS";
}

const partyHref = (code) => `/party/${encodeURIComponent(code)}`;

// A share as a percent with no decimal, or with one decimal below 10%. For example "55%" and "9.8%".
export function sharePercent(share) {
  if (share === null || share === undefined) return "–";
  const p = share * 100;
  return p >= 10 ? `${Math.round(p)}%` : `${p.toFixed(1)}%`;
}

// The parties of a term with the most members, then one row for all other parties. The API gives the order.
export function namedAndOthers(parties, limit = NAMED_PARTIES) {
  const named = parties.slice(0, limit);
  const rest = parties.slice(limit);
  if (!rest.length) return named;
  const sum = (key) => rest.reduce((a, p) => a + (p[key] || 0), 0);
  return [
    ...named,
    { code: "Others", others: true, count: rest.length, members: sum("members"), speeches: sum("speeches"),
      member_share: sum("member_share"), speech_share: sum("speech_share") },
  ];
}

// The named party with the largest difference between its share of the members and its share of the speeches.
export function largestGap(rows) {
  let best = null;
  for (const r of rows) {
    if (r.others || r.member_share === null || r.speech_share === null) continue;
    const gap = Math.abs(r.speech_share - r.member_share);
    if (!best || gap > best.gap) best = { ...r, gap };
  }
  return best;
}

// The short name of a subject area: the words before the first comma or the first "and".
export function areaShort(name) {
  return String(name || "").split(/,| and /)[0].trim();
}

// Place one dot for each member on ROWS half circles. An outer row is longer, so it gets more dots.
// The dots come back in order from the left side of the House to the right side, row after row along each angle.
const ROWS = 12;
export function houseLayout(total) {
  const radii = Array.from({ length: ROWS }, (_, i) => 58 + i * 8.6);
  const sum = radii.reduce((a, b) => a + b, 0);
  const counts = radii.map((r) => Math.round((total * r) / sum));
  counts[ROWS - 1] += total - counts.reduce((a, b) => a + b, 0);
  const dots = [];
  radii.forEach((r, row) => {
    for (let i = 0; i < counts[row]; i++) {
      const a = (Math.PI * (i + 0.5)) / counts[row];
      dots.push({ a, x: +(160 - r * Math.cos(a)).toFixed(1), y: +(170 - r * Math.sin(a)).toFixed(1) });
    }
  });
  dots.sort((p, q) => p.a - q.a);
  return dots;
}

// The House of one term: one dot for each member, in the colour of the party. The dots of a party are one link.
export function PartyHouse({ rows, total, colours }) {
  const dots = houseLayout(total);
  let from = 0;
  const groups = rows.map((r) => {
    const group = { row: r, dots: dots.slice(from, from + r.members) };
    from += r.members;
    return group;
  });
  return (
    <svg viewBox="0 12 320 164" className="parties-house" role="img" aria-label={`The ${formatNumber(total)} members of the term, as dots in the colour of each party.`}>
      {groups.map(({ row, dots: own }) => {
        const circles = own.map((d, i) => <circle key={i} cx={d.x} cy={d.y} r="2.6" />);
        const title = `${row.code}: ${formatNumber(row.members)} members`;
        return row.others ? (
          <g key={row.code} className="parties-pc parties-house__group">
            <title>{title}</title>
            {circles}
          </g>
        ) : (
          <Link key={row.code} to={partyHref(row.code)} className="parties-pc parties-house__group" style={partyColourVars(row.code, colours[row.code])}>
            <title>{title}</title>
            {circles}
          </Link>
        );
      })}
    </svg>
  );
}

// Two bars for each party: the share of the members above, the share of the speeches below.
export function PartyShares({ rows, colours }) {
  const top = Math.max(...rows.flatMap((r) => [r.member_share || 0, r.speech_share || 0]), 0.01);
  const width = (share) => `${Math.max(((share || 0) / top) * 100, 0.5).toFixed(1)}%`;
  return (
    <ul className="parties-shares">
      {rows.map((r) => (
        <li key={r.code} className="parties-pc parties-shares__row" style={r.others ? undefined : partyColourVars(r.code, colours[r.code])}>
          {r.others ? <span className="parties-shares__name">Others</span> : <Link to={partyHref(r.code)} className="parties-shares__name">{r.code}</Link>}
          <span className="parties-shares__bars" aria-hidden="true">
            <span className="parties-shares__bar" style={{ width: width(r.member_share) }} />
            <span className="parties-shares__bar parties-shares__bar--speeches" style={{ width: width(r.speech_share) }} />
          </span>
          <span className="parties-shares__num mono">
            <span className="visually-hidden">members </span>{sharePercent(r.member_share)} · <span className="visually-hidden">speeches </span>{sharePercent(r.speech_share)}
          </span>
        </li>
      ))}
    </ul>
  );
}

// The grid of a term: one row for each party, one column for each subject area. A cell compares the party with the House.
export function PartyGrid({ grid }) {
  return (
    <div className="parties-grid-frame">
      <table className="parties-grid">
        <thead>
          <tr>
            <th scope="col"><span className="visually-hidden">Party</span></th>
            {grid.areas.map((a) => (
              <th key={a.name} scope="col" title={a.name}>
                <span aria-hidden="true">{areaShort(a.name)}</span>
                <span className="visually-hidden">{a.name}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {grid.rows.map((r) => (
            <tr key={r.code}>
              <th scope="row"><Link to={partyHref(r.code)}>{r.code}</Link></th>
              {r.cells.map((c, i) => {
                if (c.lift === null) {
                  return <td key={i} className="parties-grid__cell parties-grid__cell--empty"><span className="visually-hidden">Too few speeches</span></td>;
                }
                const level = c.lift >= LIFT_MUCH ? " parties-grid__cell--much" : c.lift >= LIFT_MORE ? " parties-grid__cell--more" : "";
                return (
                  <td key={i} className={`parties-grid__cell mono${level}`} title={`${formatNumber(c.n)} speeches`}>
                    {c.lift.toFixed(1)}×
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// One card for each party: its name, its speeches in all terms, the members who spoke for it, and its terms.
// A row is a party of the API list `parties`, so the card does not change with the term.
export function PartyCards({ rows }) {
  return (
    <ul className="parties-cards">
      {rows.map((p) => (
        <li key={p.code} className="parties-pc parties-card" style={partyColourVars(p.code, p.colour)}>
          <Link to={partyHref(p.code)} className="parties-card__name">{p.name || p.code}</Link>
          <p className="parties-card__meta">
            {formatNumber(p.speeches)} {p.speeches === 1 ? "speech" : "speeches"} · {formatNumber(p.members)} {p.members === 1 ? "member" : "members"} who spoke
          </p>
          <p className="parties-card__meta">{termsText(p.terms)}</p>
        </li>
      ))}
    </ul>
  );
}

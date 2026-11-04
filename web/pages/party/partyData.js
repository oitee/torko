import { partyShades } from "../../assets/js/colour.js";
import { formatNumber, termLong } from "../../assets/js/format.js";

// Five party codes with fixed tokens in tokens.css. Each token already changes with the theme.
const TOKEN_CODES = new Set(["bjp", "inc", "aitc", "tdp", "bsp"]);

// The CSS variables of the party colour for the light and the dark theme.
// A party with a token uses it. Any other party gets shades derived from its colour by the fixed rule.
// A party with no colour gets no variables, so the charts use the control grey.
export function partyColourVars(code, colour) {
  const key = String(code || "").trim().toLowerCase();
  if (TOKEN_CODES.has(key)) {
    return { "--pc-light": `var(--party-${key})`, "--pc-dark": `var(--party-${key})` };
  }
  const shades = colour ? partyShades(colour) : null;
  if (!shades || !shades.light || !shades.dark) return {};
  return { "--pc-light": shades.light, "--pc-dark": shades.dark };
}

// A share as a percent with one decimal, for example "40.5%". A missing share gives an en dash.
export function percent(share) {
  if (share === null || share === undefined || Number.isNaN(Number(share))) return "–";
  return `${(Number(share) * 100).toFixed(1)}%`;
}

// A share as speeches in every 1,000, for example 0.0021 gives "2.1".
export function perThousand(share) {
  if (share === null || share === undefined || Number.isNaN(Number(share))) return "–";
  const v = Number(share) * 1000;
  return v >= 10 ? v.toFixed(0) : v.toFixed(1);
}

// A lift as "3.5 times". Lift is the share of the party divided by the share of all parties.
export function timesText(lift) {
  if (lift === null || lift === undefined || Number.isNaN(Number(lift))) return "–";
  const v = Number(lift);
  return `${v >= 10 ? v.toFixed(0) : v.toFixed(1)} times`;
}

// The terms in which the party had at least one tagged speech.
export function activeTerms(terms) {
  return (Array.isArray(terms) ? terms : []).filter((t) => (Number(t.tagged) || 0) > 0);
}

// The big numbers at the top of the page.
export function headNumbers(party) {
  const active = activeTerms(party.terms);
  const share = party.all_tagged ? party.total_tagged / party.all_tagged : null;
  const most = active.reduce((best, t) => (!best || t.members_speaking > best.members_speaking ? t : best), null);
  return [
    { label: "tagged speeches, all terms", value: formatNumber(party.total_tagged) },
    { label: "of all tagged speeches in the House", value: percent(share), lead: true },
    { label: active.length === 1 ? "term with speeches" : "terms with speeches", value: String(active.length) },
    most
      ? { label: `members spoke in the ${termLong(most.term)}, the most in one term`, value: formatNumber(most.members_speaking) }
      : null,
  ].filter(Boolean);
}

// One sentence for a subject row, for example
// "Malaria: 2.1 in every 1,000 tagged BJP speeches, 0.6 for all parties. 10 speeches."
export function subjectSentence(row, code) {
  const count = row.n === 1 ? "1 speech" : `${formatNumber(row.n)} speeches`;
  const by = row.members ? ` by ${row.members === 1 ? "1 member" : `${formatNumber(row.members)} members`}` : "";
  return `${row.tag}: ${perThousand(row.share)} in every 1,000 tagged ${code} speeches, ${perThousand(
    row.base
  )} for all parties. ${count}${by}, ${formatNumber(Math.round(row.extra))} above the rate of all parties.`;
}

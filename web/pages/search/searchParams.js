// The pure rules of the Search page: what the address means, and how a result reads.

// The scope keys choose which speeches the search covers. The filter keys narrow them.
export const SCOPE_KEYS = ["q", "tag", "member", "place"];
export const FILTER_KEYS = ["term", "session", "party", "party_not", "kind", "subject"];
export const SORTS = [
  { value: "latest", label: "Latest first" },
  { value: "oldest", label: "Oldest first" },
  { value: "longest", label: "Longest first" },
];

// Read the address into one object. Unknown values fall back to the defaults.
export function readSearch(searchParams) {
  const get = (k) => (searchParams.get(k) || "").trim();
  const scope = {};
  for (const k of SCOPE_KEYS) {
    if (get(k)) scope[k] = get(k);
  }
  const filters = {};
  for (const k of FILTER_KEYS) {
    if (get(k)) filters[k] = get(k);
  }
  const view = get("view") === "members" ? "members" : "speeches";
  const sort = SORTS.some((s) => s.value === get("sort")) ? get("sort") : "latest";
  const pageNum = parseInt(get("page") || "1", 10);
  const page = Number.isInteger(pageNum) && pageNum > 0 ? pageNum : 1;
  return { scope, filters, view, sort, page };
}

// The terms that the address selects, as numbers.
export function selectedTerms(filters) {
  return (filters.term || "").split(",").map((s) => parseInt(s, 10)).filter(Number.isInteger);
}

// "the word" for one word, "the words" for more than one.
function wordsPhrase(q) {
  return q.split(/\s+/).filter(Boolean).length > 1 ? "the words" : "the word";
}

// The heading of the page, in parts, so that the page can set the count in mono.
// count is null while the speeches load. names holds the names of the tag, place and member.
export function headingParts({ scope, count, names = {} }) {
  const q = scope.q || "";
  let on = "";
  if (scope.tag) on += ` on ${names.tag || scope.tag}`;
  if (scope.place) on += ` about ${names.place || scope.place}`;
  if (scope.member) on += ` by ${names.member || "this member"}`;

  if (!q && !on) {
    return { lead: null, rest: "Search the speeches of the Lok Sabha" };
  }
  if (count === null || count === undefined) {
    const words = q ? ` with ${wordsPhrase(q)} “${q}”` : "";
    return { lead: null, rest: `Speeches${on}${words}` };
  }
  if (count === 0) {
    return { lead: null, rest: q ? `No speech${on} uses ${wordsPhrase(q)} “${q}”` : `No speech${on} matches the filters` };
  }
  const noun = count === 1 ? "speech" : "speeches";
  if (!q) return { lead: count, rest: ` ${noun}${on}` };
  const verb = count === 1 ? "uses" : "use";
  return { lead: count, rest: ` ${noun}${on} ${verb} ${wordsPhrase(q)} “${q}”` };
}

// Cut the excerpt to a short window around the first marked word.
// Returns { parts: [{ text, mark }], cutStart, cutEnd }. Runs of white space become one space.
export function excerptParts(excerpt, marks, width = 240) {
  if (!excerpt) return { parts: [], cutStart: false, cutEnd: false };
  const text = String(excerpt);
  const spans = (Array.isArray(marks) ? marks : [])
    .filter((m) => Array.isArray(m) && m[1] > m[0] && m[0] >= 0 && m[1] <= text.length)
    .sort((a, b) => a[0] - b[0]);

  let start = 0;
  if (spans.length && spans[0][0] > width / 3) {
    start = spans[0][0] - Math.round(width / 3);
    const space = text.indexOf(" ", start);
    if (space !== -1 && space < spans[0][0]) start = space + 1;
  }
  let end = Math.min(text.length, start + width);
  if (end < text.length) {
    const space = text.lastIndexOf(" ", end);
    if (space > start) end = space;
  }
  // A marked word is never cut in two.
  for (const [a, b] of spans) {
    if (a < end && b > end) end = b;
  }

  const parts = [];
  let pos = start;
  for (const [a, b] of spans) {
    if (b <= start || a >= end) continue;
    const from = Math.max(a, start);
    if (from > pos) parts.push({ text: text.slice(pos, from), mark: false });
    parts.push({ text: text.slice(from, Math.min(b, end)), mark: true });
    pos = Math.min(b, end);
  }
  if (pos < end) parts.push({ text: text.slice(pos, end), mark: false });

  const clean = parts.map((p) => ({ ...p, text: p.text.replace(/\s+/g, " ") }));
  if (clean.length) {
    clean[0].text = clean[0].text.replace(/^\s+/, "");
    const last = clean[clean.length - 1];
    last.text = last.text.replace(/\s+$/, "");
  }
  return {
    parts: clean.filter((p) => p.text),
    cutStart: start > 0,
    cutEnd: end < text.length,
  };
}

// A year span: "2019" or "2004–2024".
export function yearSpan(first, last) {
  const a = first ? String(first).slice(0, 4) : "";
  const b = last ? String(last).slice(0, 4) : "";
  if (a && b) return a === b ? a : `${a}–${b}`;
  return a || b || "";
}

// The page numbers to show: the first, the last, and two on each side of the current page.
// A null is a gap.
export function pageWindow(page, pages) {
  const out = [];
  for (let p = 1; p <= pages; p += 1) {
    if (p === 1 || p === pages || Math.abs(p - page) <= 2) {
      out.push(p);
    } else if (out[out.length - 1] !== null) {
      out.push(null);
    }
  }
  return out;
}

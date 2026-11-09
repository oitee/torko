export const MAX_COMPARE = 4;

export function readSlugs(value) {
  return [...new Set(String(value || "").split(",").map((s) => s.trim()).filter(Boolean))].slice(0, MAX_COMPARE);
}

export function addSlug(slugs, slug) {
  return slugs.includes(slug) || slugs.length >= MAX_COMPARE ? slugs : [...slugs, slug];
}

export function removeSlug(slugs, slug) {
  return slugs.filter((s) => s !== slug);
}

// The percent of the tagged speeches of each year that carry the subject. A year with no tagged speech gives null.
export function yearRates(years) {
  return (years || []).map((y) => ({ year: y.year, n: y.n, tagged: y.tagged, rate: y.tagged ? (100 * y.n) / y.tagged : null }));
}

// Round the top of the chart up to a simple number.
export function niceMax(value) {
  if (value <= 0) return 1;
  const size = 10 ** Math.floor(Math.log10(value));
  const step = [1, 2, 5, 10].find((s) => s * size >= value);
  return step * size;
}

// The sentence at the top of the page: the year and subject with the largest share of any year.
// A share of 5% or more reads as "one in N". A smaller share reads as a percent.
// A year with fewer than minTagged tagged speeches cannot give the sentence, because one debate can move its shares a lot.
export const HEADLINE_MIN_TAGGED = 2000;

export function headline(years, minTagged = HEADLINE_MIN_TAGGED) {
  let best = null;
  for (const y of (years || []).filter((x) => x.tagged === undefined || x.tagged >= minTagged)) {
    for (const s of y.subjects || []) {
      if (!best || s.share > best.share) best = { year: y.year, name: s.name, slug: s.slug, share: s.share, n: s.n, tagged: y.tagged };
    }
  }
  if (!best) return null;
  const phrase = best.share >= 5 ? `one in ${Math.round(100 / best.share)}` : `${best.share}%`;
  return { ...best, phrase };
}

// The share of a subject, with one decimal. Example: 3.4%.
export function fmtShare(value) {
  return `${Number(value).toFixed(1)}%`;
}

// The usual share of a subject. Below 0.05 the API rounds to 0, so the text says "under 0.05%".
// Below 1 it has two decimals. From 1 up it has one decimal.
export function fmtUsual(value) {
  const v = Number(value);
  if (v < 0.05) return "under 0.05%";
  return v < 1 ? `${v.toFixed(2)}%` : `${v.toFixed(1)}%`;
}

const SMALL_WORDS = new Set(["of", "and", "the", "for", "in", "on", "to", "a", "an", "or"]);

// The name of a subject as the page shows it. The data stays as it is.
// A name cut by the source loses its closing bracket, so the bracket closes.
// A stray space before a number, as in "COVID -19", goes.
// A name in capitals only gets normal capitals. A word of one to three letters stays in capitals, except small words.
export function displayName(name) {
  if (!name) return "";
  let out = String(name).trim().replace(/\s{2,}/g, " ").replace(/([A-Za-z]) -(\d)/g, "$1-$2");
  const open = (out.match(/\(/g) || []).length;
  const close = (out.match(/\)/g) || []).length;
  if (open > close) out = `${out.replace(/\s+$/, "")})`;
  if (out.includes(" ") && out === out.toUpperCase() && /[A-Z]/.test(out)) {
    out = out
      .split(" ")
      .map((w, i) => {
        const lower = w.toLowerCase();
        if (i > 0 && SMALL_WORDS.has(lower)) return lower;
        if (w.length <= 3 && !["ACT", "THE", "AND", "FOR"].includes(w)) return w;
        return lower.charAt(0).toUpperCase() + lower.slice(1);
      })
      .join(" ");
  }
  return out;
}

// The comparison that the chart shows before the reader chooses.
// Rule: the leading subject of the newest complete year, and the leading subject of the year before it.
// A complete year has at least minTagged tagged speeches. When both years lead with the same subject,
// the year before gives its next subject. It returns the slugs and the two years that they come from.
export function defaultCompare(years, minTagged = HEADLINE_MIN_TAGGED) {
  const full = (years || [])
    .filter((y) => (y.tagged === undefined || y.tagged >= minTagged) && (y.subjects || []).length)
    .sort((a, b) => b.year - a.year);
  if (!full.length) return { slugs: [], years: [] };
  const slugs = [full[0].subjects[0].slug];
  const used = [full[0].year];
  const before = full.find((y) => y.year === full[0].year - 1);
  if (before) {
    const pick = before.subjects.find((s) => !slugs.includes(s.slug));
    if (pick) {
      slugs.push(pick.slug);
      used.push(before.year);
    }
  }
  return { slugs, years: used };
}

// A short form of a tag name for a sentence. Rule: a name that ends in an abbreviation in brackets
// (2 to 12 characters with at least two capital letters together) shows only that abbreviation.
// "Novel Coronavirus (COVID-19)" becomes "COVID-19". "Seat (Bihar)" and "Scheme (Ayushman Bharat)" stay whole.
export function shortName(name) {
  const full = displayName(name);
  const m = full.match(/^.{8,}\s\(([^()]{2,12})\)$/);
  return m && /[A-Z]{2,}/.test(m[1]) ? m[1] : full;
}

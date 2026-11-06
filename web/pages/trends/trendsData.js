// The pure rules of the Trends page.
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
      if (!best || s.share > best.share) best = { year: y.year, name: s.name, share: s.share };
    }
  }
  if (!best) return null;
  const phrase = best.share >= 5 ? `one in ${Math.round(100 / best.share)}` : `${best.share}%`;
  return { ...best, phrase };
}

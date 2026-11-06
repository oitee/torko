// The rows of a chart by year, in year order: { year, n, tagged, rate }. rate is n / tagged, or 0 for a year with no tagged speech.
export function yearSeries(years) {
  return (Array.isArray(years) ? years : [])
    .map((y) => {
      const n = Number(y.n) || 0;
      const tagged = Number(y.tagged) || 0;
      return { year: Number(y.year), n, tagged, rate: tagged > 0 ? n / tagged : 0 };
    })
    .filter((y) => !Number.isNaN(y.year))
    .sort((a, b) => a.year - b.year);
}

// The row with the largest value. A tie goes to the earlier year. With no value above 0, it returns null.
export function peakYear(rows, value = (d) => d.n) {
  const best = rows.reduce((top, d) => (top === null || value(d) > value(top) ? d : top), null);
  return best && value(best) > 0 ? best : null;
}

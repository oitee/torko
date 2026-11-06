// The pure rules of the race of subjects on the Trends page.
// The API gives, for each subject, its speeches in each 12-month window. A frame is one window.
// t is a frame position. It can be between two frames while the race plays.

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

// "2001-06" gives "June 2001".
export function monthName(label) {
  const [y, m] = String(label).split("-").map(Number);
  return `${MONTHS[m - 1]} ${y}`;
}

// The percent of the tagged speeches of frame i that carry the subject. A frame with no tagged speech gives 0.
export function shareAt(subject, tagged, i) {
  return tagged[i] ? (100 * subject.n[i]) / tagged[i] : 0;
}

// The distance of the subject above its typical share, in percentage points, at frame position t.
// Between two frames, the value moves in a straight line from one frame to the next.
export function aboveAt(subject, tagged, t) {
  const last = tagged.length - 1;
  const lo = Math.max(0, Math.min(last, Math.floor(t)));
  const hi = Math.min(last, lo + 1);
  const f = Math.min(1, Math.max(0, t - lo));
  const a = shareAt(subject, tagged, lo) - subject.typical;
  const b = shareAt(subject, tagged, hi) - subject.typical;
  return a + (b - a) * f;
}

// The top subjects at frame position t, largest distance above typical first. A tie goes by name.
// A subject qualifies only when its nearest frame has at least minWindow speeches. This is the rule of the API.
export function rankAt(subjects, tagged, t, top, minWindow) {
  const near = Math.max(0, Math.min(tagged.length - 1, Math.round(t)));
  return subjects
    .filter((s) => s.n[near] >= minWindow)
    .map((s) => ({ subject: s, value: aboveAt(s, tagged, t), share: shareAt(s, tagged, near), n: s.n[near] }))
    .sort((a, b) => b.value - a.value || a.subject.name.localeCompare(b.subject.name))
    .slice(0, top);
}

// Move label positions apart so that two labels are never closer than gap. ys must be in the order of the labels.
// The labels stay in their order from top to bottom and stay between min and max when there is room.
export function spreadLabels(ys, gap, min, max) {
  const order = ys.map((y, i) => [y, i]).sort((a, b) => a[0] - b[0]);
  const out = order.map(([y]) => Math.max(min, y));
  for (let k = 1; k < out.length; k++) out[k] = Math.max(out[k], out[k - 1] + gap);
  const over = out.length ? out[out.length - 1] - max : 0;
  if (over > 0) {
    out[out.length - 1] -= over;
    for (let k = out.length - 2; k >= 0; k--) out[k] = Math.min(out[k], out[k + 1] - gap);
  }
  const result = new Array(ys.length);
  order.forEach(([, i], k) => { result[i] = out[k]; });
  return result;
}

// The first month of the window that ends at frame i. A window has windowMonths calendar months.
// Example: with 12 months, the window that ends in "2026-04" starts in "2025-05".
export function windowStart(label, windowMonths = 12) {
  const [y, m] = String(label).split("-").map(Number);
  const index = y * 12 + (m - 1) - (windowMonths - 1);
  return `${Math.floor(index / 12)}-${String((index % 12) + 1).padStart(2, "0")}`;
}

// The one scale of the bars for every frame of the race.
// max is the largest distance above typical of any subject in any frame that it qualifies in.
// The scale is a whole number of steps, so the gridlines fall on simple numbers. It returns the top and the step.
export function raceScale(subjects, tagged, minWindow) {
  let max = 0.1;
  for (const s of subjects) {
    for (let i = 0; i < tagged.length; i++) {
      if (s.n[i] >= minWindow) max = Math.max(max, shareAt(s, tagged, i) - s.typical);
    }
  }
  const raw = max / 3;
  const size = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((k) => k * size).find((v) => v >= raw);
  return { top: step * Math.ceil(max / step - 1e-9), step };
}

// The rows of the CSV file of the race: the top subjects of every month.
export function raceCsvRows(data) {
  const { rules } = data;
  const rows = [["month", "window_start", "rank", "subject", "speeches_with_subject", "tagged_speeches", "share_percent", "usual_share_percent", "points_above_usual"]];
  for (let f = 0; f < data.months.length; f++) {
    rankAt(data.subjects, data.tagged, f, rules.top, rules.min_window_speeches).forEach((r, i) => {
      rows.push([data.months[f], windowStart(data.months[f], rules.window_months), i + 1, r.subject.name, r.n, data.tagged[f],
        r.share.toFixed(2), r.subject.typical, r.value.toFixed(2)]);
    });
  }
  return rows;
}

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

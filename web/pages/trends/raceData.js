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

// The one scale of the bars for every frame of the race.
// max is the largest distance above typical of any subject in any frame that it qualifies in.
// The scale is a whole number of steps, so the gridlines fall on simple numbers. It returns the top and the step.
export function raceScale(subjects, tagged, minWindow, quantile = 0.9) {
  const leads = [];
  for (let i = 0; i < tagged.length; i++) {
    let lead = 0;
    for (const s of subjects) {
      if (s.n[i] >= minWindow) lead = Math.max(lead, shareAt(s, tagged, i) - s.typical);
    }
    if (lead > 0) leads.push(lead);
  }
  // The scale stops at the 90th percentile of those leads, so one peak, such as the year of COVID, does not shrink every other month.
  // A bar above the top is drawn to the end of the track and marked as cut.
  leads.sort((a, b) => a - b);
  const max = Math.max(0.1, leads.length ? leads[Math.min(leads.length - 1, Math.floor(quantile * (leads.length - 1)))] : 0.1);
  const raw = max / 3;
  const size = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((k) => k * size).find((v) => v >= raw);
  return { top: step * Math.ceil(max / step - 1e-9), step };
}

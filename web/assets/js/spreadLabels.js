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

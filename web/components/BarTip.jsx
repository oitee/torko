import React, { useLayoutEffect, useRef, useState } from "react";
import "./BarTip.css";

// Where the pop-up sits along the chart. Near an edge it lines up with that edge, so it stays inside the chart.
export function tipSide(index, count) {
  if (count <= 1) return "middle";
  if (index < count * 0.2) return "start";
  if (index > count * 0.8) return "end";
  return "middle";
}

// The parent of BarTip must have position: relative and be the box of the bars. heightPct is from 0 to 100.
export default function BarTip({ index, count, heightPct = 0, children, wrap = false }) {
  const ref = useRef(null);
  const [shift, setShift] = useState(0);
  const show = index != null && index >= 0 && Boolean(count);

  // On a narrow screen the box can cross an edge of the chart. Then it moves back inside by that amount.
  // The small mark under the box moves the other way, so it still points at the bar.
  useLayoutEffect(() => {
    const el = ref.current;
    const host = el?.parentElement;
    if (!el || !host) return;
    el.style.translate = "0 0";
    const box = el.getBoundingClientRect();
    const room = host.getBoundingClientRect();
    let next = 0;
    if (box.right > room.right) next = room.right - box.right;
    if (box.left + next < room.left) next = room.left - box.left;
    el.style.translate = "";
    setShift(Math.round(next));
  }, [index, count, children]);

  if (!show) return null;
  const at = ((index + 0.5) / count) * 100;
  return (
    <div
      ref={ref}
      className={`bar-tip bar-tip--${tipSide(index, count)}${wrap ? " bar-tip--wrap" : ""}`}
      style={{ "--at": `${at}%`, "--h": `${Math.max(0, Math.min(100, heightPct))}%`, "--shift": `${shift}px` }}
      role="status"
      aria-live="polite"
    >
      {children}
    </div>
  );
}

export { BarTip };

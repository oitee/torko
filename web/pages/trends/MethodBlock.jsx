import React, { useId, useLayoutEffect, useRef, useState } from "react";
import Popover from "../../components/Popover.jsx";

// MethodBlock is a short text link that opens a small panel with the rule of a chart.
// It works like "Add filter" on the Search page: the panel floats under the link, and it closes with its X button,
// with Escape, or with a click outside it.
export default function MethodBlock({ label = "How this is calculated", children }) {
  const [open, setOpen] = useState(false);
  const trigger = useRef(null);
  const titleId = useId();
  const box = useRef(null);
  const [shift, setShift] = useState(0);

  // The panel starts under the link. On a narrow screen it can run past the right edge. Then it moves left by that amount.
  useLayoutEffect(() => {
    if (!open) {
      setShift(0);
      return;
    }
    const pop = box.current?.querySelector(".trends-method__pop");
    if (!pop) return;
    const rect = pop.getBoundingClientRect();
    const room = document.documentElement.clientWidth - 16;
    if (rect.right > room) setShift(Math.min(rect.left - 16, rect.right - room));
  }, [open]);
  return (
    <div className="trends-method" ref={box}>
      <button
        type="button"
        ref={trigger}
        className="trends-method__link"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {label}
      </button>
      <Popover open={open} onClose={() => setOpen(false)} triggerRef={trigger} className="trends-method__pop" role="dialog" aria-labelledby={titleId} style={shift ? { transform: `translateX(-${shift}px)` } : undefined}>
        <div className="trends-method__head">
          <p id={titleId} className="trends-method__title">{label}</p>
          <button type="button" className="trends-method__close" aria-label="Close" onClick={() => setOpen(false)}>
            ✕
          </button>
        </div>
        <div className="trends-method__body">{children}</div>
      </Popover>
    </div>
  );
}

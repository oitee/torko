import React, { useId, useLayoutEffect, useRef, useState } from "react";
import Popover from "./Popover.jsx";
import "./MethodBlock.css";

// A text link that opens a small panel with the rule of a chart. The panel closes with its X button, Escape or a click outside.
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
    const pop = box.current?.querySelector(".method-block__pop");
    if (!pop) return;
    const rect = pop.getBoundingClientRect();
    const room = document.documentElement.clientWidth - 16;
    if (rect.right > room) setShift(Math.min(rect.left - 16, rect.right - room));
  }, [open]);
  return (
    <div className="method-block" ref={box}>
      <button
        type="button"
        ref={trigger}
        className="method-block__link"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {label}
      </button>
      <Popover open={open} onClose={() => setOpen(false)} triggerRef={trigger} className="method-block__pop" role="dialog" aria-labelledby={titleId} style={shift ? { transform: `translateX(-${shift}px)` } : undefined}>
        <div className="method-block__head">
          <p id={titleId} className="method-block__title">{label}</p>
          <button type="button" className="method-block__close" aria-label="Close" onClick={() => setOpen(false)}>
            ✕
          </button>
        </div>
        <div className="method-block__body">{children}</div>
      </Popover>
    </div>
  );
}

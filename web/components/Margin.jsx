import React, { useState } from "react";
import "./Margin.css";

// The Margin component renders side content like counts and method notes.
// On desktop screens it is always open.
// On mobile screens it collapses into an expandable toggle button.
export default function Margin({ children, label = "Counts and method" }) {
  const [open, setOpen] = useState(false);

  if (!children) {
    return null;
  }

  const toggleSign = open ? "−" : "+";

  return (
    <aside aria-label={label} className="margin">
      <button
        type="button"
        className="margin__toggle"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        <span>{label}</span>
        <span className="margin__sign">{toggleSign}</span>
      </button>

      <div
        className={`margin__content ${
          open ? "margin__content--open" : ""
        }`}
      >
        {children}
      </div>
    </aside>
  );
}

export { Margin };

import React, { useId } from "react";

// InfoTip is a small question mark button. Its text shows on hover, on keyboard focus, and on a tap.
// A tap works because a tap gives the button focus. The text is also the description of the button for screen readers.
export default function InfoTip({ label, children }) {
  const id = useId();
  return (
    <span className="info-tip">
      <button type="button" className="info-tip__button" aria-label={label} aria-describedby={id}>?</button>
      <span role="tooltip" id={id} className="info-tip__text">{children}</span>
    </span>
  );
}

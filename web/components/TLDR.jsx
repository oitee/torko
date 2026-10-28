import React from "react";
import "./TLDR.css";

// The TLDR component displays a brief summary.
// It renders the label TLDR above the body text.
// It returns null when text is missing or empty.
export default function TLDR({ text }) {
  if (!text || !text.trim()) {
    return null;
  }

  return (
    <div className="tldr">
      <div className="tldr__label">TLDR</div>
      <p className="tldr__text">{text}</p>
    </div>
  );
}

export { TLDR };

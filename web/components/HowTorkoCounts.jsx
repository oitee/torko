import React from "react";
import "./HowTorkoCounts.css";

// The HowTorkoCounts component renders a method explanation next to figures.
// It includes a label heading and meta text above a hairline divider.
export default function HowTorkoCounts({ children }) {
  if (!children) {
    return null;
  }

  return (
    <div className="how-torko-counts">
      <h3 className="how-torko-counts__heading">How Torko counts</h3>
      <div className="how-torko-counts__note">{children}</div>
    </div>
  );
}

export { HowTorkoCounts };

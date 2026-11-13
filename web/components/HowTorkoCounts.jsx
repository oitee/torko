import React from "react";
import { Link } from "react-router-dom";
import "./HowTorkoCounts.css";

// One link to the Method page, which explains how Torko counts.
export default function HowTorkoCounts() {
  return (
    <p className="how-torko-counts">
      <Link to="/method" className="how-torko-counts__link">How counts work</Link>
    </p>
  );
}

export { HowTorkoCounts };

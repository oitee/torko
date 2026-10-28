import React from "react";
import { Link } from "react-router-dom";
import "./Logo.css";

// Seat layout coordinates for the Lok Sabha mark.
const SEATS = [
  { cx: 38.43, cy: 67.79, isMarked: false },
  { cx: 32.03, cy: 55.05, isMarked: false },
  { cx: 36.91, cy: 41.65, isMarked: false },
  { cx: 50.0, cy: 36.0, isMarked: false },
  { cx: 63.09, cy: 41.65, isMarked: false },
  { cx: 67.97, cy: 55.05, isMarked: false },
  { cx: 61.57, cy: 67.79, isMarked: false },
  { cx: 31.36, cy: 76.22, isMarked: false },
  { cx: 23.11, cy: 64.86, isMarked: false },
  { cx: 21.16, cy: 50.97, isMarked: false },
  { cx: 25.96, cy: 37.78, isMarked: false },
  { cx: 36.39, cy: 28.39, isMarked: false },
  { cx: 50.0, cy: 25.0, isMarked: false },
  { cx: 63.61, cy: 28.39, isMarked: true },
  { cx: 74.04, cy: 37.78, isMarked: false },
  { cx: 78.84, cy: 50.97, isMarked: false },
  { cx: 76.89, cy: 64.86, isMarked: false },
  { cx: 68.64, cy: 76.22, isMarked: false },
  { cx: 24.29, cy: 84.64, isMarked: false },
  { cx: 15.36, cy: 74.0, isMarked: false },
  { cx: 10.61, cy: 60.95, isMarked: false },
  { cx: 10.61, cy: 47.05, isMarked: false },
  { cx: 15.36, cy: 34.0, isMarked: false },
  { cx: 24.29, cy: 23.36, isMarked: false },
  { cx: 36.32, cy: 16.41, isMarked: false },
  { cx: 50.0, cy: 14.0, isMarked: false },
  { cx: 63.68, cy: 16.41, isMarked: false },
  { cx: 75.71, cy: 23.36, isMarked: false },
  { cx: 84.64, cy: 34.0, isMarked: false },
  { cx: 89.39, cy: 47.05, isMarked: false },
  { cx: 89.39, cy: 60.95, isMarked: false },
  { cx: 84.64, cy: 74.0, isMarked: false },
  { cx: 75.71, cy: 84.64, isMarked: false },
];

// The Logo component renders the Lok Sabha seat-row mark and the word torko.
// It links to the home page with the accessible name Torko home.
export default function Logo() {
  return (
    <Link to="/" className="logo" aria-label="Torko home">
      <svg
        viewBox="0 0 100 100"
        width="28"
        height="28"
        aria-hidden="true"
        style={{ display: "block", flex: "none" }}
      >
        {SEATS.map((seat, index) => (
          <circle
            key={index}
            cx={seat.cx}
            cy={seat.cy}
            r="4.5"
            fill={seat.isMarked ? "var(--header-action)" : "currentColor"}
          />
        ))}
      </svg>
      <span className="logo__word">torko</span>
    </Link>
  );
}

export { Logo };

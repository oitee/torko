import React from "react";
import "./HouseSeats.css";

// The size of the House: the Lok Sabha has 543 elected seats. This is a fixed fact, not a figure from the data.
export const HOUSE_SEATS = 543;

// The seats sit in ROWS arcs, from radius INNER to radius OUTER. Each arc runs from START to END degrees,
// so the House is open at the front, as in the mark of the site.
const ROWS = 11;
const INNER = 34;
const OUTER = 94;
const START = 130;
const END = 410;
// The one marked seat: a seat in the middle row, at about 72% of its arc.
const MARKED_ROW = 6;
const MARKED_AT = 0.72;

// Place HOUSE_SEATS seats on the arcs. An outer arc is longer, so it gets more seats, in proportion to its radius.
export function seatLayout(total = HOUSE_SEATS) {
  const radii = Array.from({ length: ROWS }, (_, i) => INNER + ((OUTER - INNER) * i) / (ROWS - 1));
  const sum = radii.reduce((a, b) => a + b, 0);
  const counts = radii.map((r) => Math.round((total * r) / sum));
  // Rounding can miss the total by a few seats. The outer arc takes the difference.
  counts[ROWS - 1] += total - counts.reduce((a, b) => a + b, 0);

  const seats = [];
  radii.forEach((r, row) => {
    const n = counts[row];
    const marked = Math.round(n * MARKED_AT);
    for (let i = 0; i < n; i++) {
      const a = ((START + ((END - START) * i) / (n - 1)) * Math.PI) / 180;
      seats.push({
        x: +(100 + r * Math.cos(a)).toFixed(2),
        y: +(100 + r * Math.sin(a)).toFixed(2),
        marked: row === MARKED_ROW && i === marked,
      });
    }
  });
  return seats;
}

const SEATS = seatLayout();

// HouseSeats draws the seats of the Lok Sabha from above, with one seat marked.
// The marked seat is a picture of "your seat". It does not stand for a real constituency.
export default function HouseSeats() {
  return (
    <figure className="house-seats">
      <svg
        viewBox="0 0 200 196"
        role="img"
        aria-label={`The ${HOUSE_SEATS} seats of the Lok Sabha. One seat is marked.`}
        className="house-seats__svg"
      >
        {SEATS.map((s, i) => (
          <circle
            key={i}
            cx={s.x}
            cy={s.y}
            r={s.marked ? 3.6 : 2.2}
            className={s.marked ? "house-seats__seat house-seats__seat--marked" : "house-seats__seat"}
          />
        ))}
      </svg>
      <figcaption className="house-seats__caption">
        <span className="house-seats__key" aria-hidden="true" />
        <span>
          <span className="house-seats__num">{HOUSE_SEATS}</span> seats. One member speaks for your seat.
        </span>
      </figcaption>
    </figure>
  );
}

export { HouseSeats };

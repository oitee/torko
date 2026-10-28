import React from "react";
import { Link } from "react-router-dom";
import { countOf, formatNumber } from "../assets/js/format.js";
import "./Count.css";

// The Count component renders mono numbers and counts.
// It formats counts with formatNumber or countOf.
// It renders a link when href is given.
export default function Count({ n, total, noun, href }) {
  let text = "";
  if (total !== undefined && total !== null) {
    text = countOf(n, total, noun);
  } else if (noun) {
    const formatted = formatNumber(n);
    text = formatted === "–" ? "–" : `${formatted} ${noun}`;
  } else {
    text = formatNumber(n);
  }

  if (href) {
    return (
      <Link to={href} className="count count--link">
        {text}
      </Link>
    );
  }

  return <span className="count">{text}</span>;
}

export { Count };

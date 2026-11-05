import React from "react";
import { Link } from "react-router-dom";
import "./PartyLink.css";

// PartyLink shows a party code as a link to the page of the party. With no code, it shows nothing.
// A click stays on the link, because some rows that hold a party have their own click.
export default function PartyLink({ code }) {
  const clean = String(code || "").trim();
  if (!clean) return null;
  return (
    <Link to={`/party/${encodeURIComponent(clean)}`} className="party-link" onClick={(e) => e.stopPropagation()}>
      {clean}
    </Link>
  );
}

export { PartyLink };

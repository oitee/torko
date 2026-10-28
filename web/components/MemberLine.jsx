import React from "react";
import { formatNumber, termShort } from "../assets/js/format.js";
import "./MemberLine.css";

// The MemberLine component displays a member identity and their parliamentary terms.
// Note: The API does not yet provide a photo or Devanagari name.
export default function MemberLine({ member }) {
  if (!member) {
    return null;
  }

  const { name, terms } = member;
  const safeTerms = Array.isArray(terms) ? terms : [];

  return (
    <div className="member-line">
      {name && <h2 className="member-line__name">{name}</h2>}

      {safeTerms.length > 0 && (
        <ul className="member-line__terms" role="list">
          {safeTerms.map((t, idx) => {
            const parts = [];

            // 1. Term in short form (e.g. 17th LS)
            if (t.term !== null && t.term !== undefined && t.term !== "") {
              parts.push(termShort(t.term));
            }

            // 2. Seat
            if (t.seat && typeof t.seat === "string" && t.seat.trim()) {
              parts.push(t.seat.trim());
            }

            // 3. Parties joined with ", "
            if (Array.isArray(t.parties) && t.parties.length > 0) {
              const partyList = t.parties
                .filter((p) => typeof p === "string" && p.trim())
                .map((p) => p.trim());
              if (partyList.length > 0) {
                parts.push(partyList.join(", "));
              }
            } else if (typeof t.parties === "string" && t.parties.trim()) {
              parts.push(t.parties.trim());
            }

            // 4. Speeches formatted with formatNumber
            if (
              t.speeches !== null &&
              t.speeches !== undefined &&
              t.speeches !== ""
            ) {
              const num = formatNumber(t.speeches);
              if (num !== "–") {
                parts.push(`${num} speeches`);
              }
            }

            const termText = parts.join(" · ");
            const key = t.term ?? idx;

            return (
              <li key={key} className="member-line__term">
                {termText}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export { MemberLine };

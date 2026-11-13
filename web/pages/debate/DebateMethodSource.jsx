import React from "react";
import { termLong } from "../../assets/js/format.js";
import HowTorkoCounts from "../../components/HowTorkoCounts.jsx";
import "./DebateMethodSource.css";

// Strip https:// or http:// from source URL for display
function cleanUrl(url) {
  if (!url) return "";
  return url.replace(/^https?:\/\//, "");
}

export default function DebateMethodSource({ term, session_label, date, source_url }) {
  const recordParts = ["Lok Sabha Debates"];
  if (term) recordParts.push(termLong(term));
  if (session_label) recordParts.push(session_label);
  const recordText = recordParts.join(", ");

  return (
    <div className="debate-method-source">
      <section id="counts" className="debate-method-source__counts">
        <HowTorkoCounts />
      </section>

      <section className="debate-source" aria-labelledby="debate-source-heading">
        <h3 id="debate-source-heading" className="debate-source__heading">
          Source
        </h3>
        <dl className="debate-source__dl">
          <dt>Record</dt>
          <dd>{recordText}</dd>
          <dt>Date</dt>
          <dd className="mono">{date || "Not given"}</dd>
          <dt>Debate</dt>
          <dd>
            {source_url ? (
              <a
                href={source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="debate-source__link mono"
              >
                {cleanUrl(source_url)}
              </a>
            ) : (
              "Not given"
            )}
          </dd>
          <dt>TLDR</dt>
          <dd>Cite the speech, not the TLDR.</dd>
        </dl>
      </section>
    </div>
  );
}

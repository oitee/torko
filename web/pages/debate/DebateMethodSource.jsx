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
        <HowTorkoCounts>
          <div className="debate-method-source__entries">
            <p>
              <strong>Speech.</strong> A range of the record that belongs to one member,
              from their first words to their last. A bracket in the left margin marks it.
            </p>
            <p>
              <strong>Interruption.</strong> A short remark by another member or by the chair
              inside a speech. It stays in its place, indented. It is not part of the speech.
            </p>
            <p>
              <strong>TLDR.</strong> One or two sentences for each speech of 99 words or more.
              Shorter speeches have no TLDR. The record is the source.
            </p>
            <p>
              <strong>Filters.</strong> A tag belongs to a speech, so a tag shows whole speeches.
              A member filter shows every remark by that member, also inside other speeches.
              Everything else folds into a bar you can open.
            </p>
            <p>
              <strong>No member.</strong> Every remark that is not matched to a member shows
              “Speaker not identified. Torko could not match this name to one member.”
            </p>
          </div>
        </HowTorkoCounts>
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

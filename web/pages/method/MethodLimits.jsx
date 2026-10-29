import React from "react";
import { countOf, ordinal } from "../../assets/js/format.js";
import "./MethodLimits.css";

// The first letter in capitals, for a figure that starts a sentence (e.g. "about 0.24%").
function capital(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

// MethodLimits lists what Torko gets wrong or leaves out. Each figure comes from /api/method.
// A missing figure hides its line.
export default function MethodLimits({ data }) {
  const err = data?.corpus?.error_rate;
  const turns = data?.turns;
  const unread = data?.unread_text;

  return (
    <section className="method-limits" aria-labelledby="method-limits-title">
      <h2 id="method-limits-title" className="method-limits__title">
        What Torko gets wrong
      </h2>
      <ul className="method-limits__list">
        {err?.text && (
          <li>
            <span className="method-limits__num">{capital(err.text)}</span> of named turns have the wrong member name.
          </li>
        )}
        {turns?.no_name != null && turns?.total != null && (
          <li>
            <span className="method-limits__num">{countOf(turns.no_name, turns.total)}</span> turns have no member
            name. Torko could not match the printed name to one member.
          </li>
        )}
        {unread?.text && (
          <li>
            Torko does not read <span className="method-limits__num">{unread.text}</span> {unread.counts}.
            {unread.first_term && (
              <>
                {" "}
                The share is <span className="method-limits__num">{unread.first_term.text}</span> in the{" "}
                {ordinal(unread.first_term.term)} Lok Sabha
                {unread.recent_terms && (
                  <>
                    {" "}
                    and <span className="method-limits__num">{unread.recent_terms}</span> in recent terms
                  </>
                )}
                . So the charts show too little activity in the early years.
              </>
            )}
          </li>
        )}
        <li>The TLDR and the tags are machine text. Cite the speech, not the TLDR.</li>
        <li>
          The party of a member changes on a date only after a formal event, for example a by-election, a split that
          the House recognises, or an expulsion.
        </li>
      </ul>
    </section>
  );
}

export { MethodLimits };

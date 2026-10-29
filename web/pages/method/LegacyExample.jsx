import React from "react";
import { Link } from "react-router-dom";
import { formatDateISO } from "../../assets/js/format.js";
import "./MethodExample.css";
import "./LegacyExample.css";

// LegacyExample shows one sentence of old-font Hindi as the source page stores it, and the Hindi that Torko reads.
// The example comes from /api/method → examples.legacy. The API decodes it with the code of the reader.
export default function LegacyExample({ example }) {
  if (!example?.source_text || !example?.text) return null;
  const d = example.debate;

  return (
    <div className="legacy-example">
      <div className="method-box">
        <p className="method-box__label">In the source page</p>
        <p className="legacy-example__garbled">{example.source_text}</p>
      </div>
      <div className="method-arrow" aria-hidden="true">
        ↓
      </div>
      <div className="method-box method-after">
        <p className="method-box__label">After Torko reads it</p>
        <p className="legacy-example__hindi" lang="hi">
          {example.text}
        </p>
      </div>
      {d && (
        <p className="method-source">
          {d.member && (
            <>
              {d.member_id ? <Link to={`/member/${d.member_id}`}>{d.member}</Link> : d.member} ·{" "}
            </>
          )}
          {d.date && <span className="method-source__date">{formatDateISO(d.date)}</span>}
          {d.source_url && (
            <>
              {" "}
              · <a href={d.source_url}>Read the original on sansad.in</a>
            </>
          )}
        </p>
      )}
    </div>
  );
}

export { LegacyExample };

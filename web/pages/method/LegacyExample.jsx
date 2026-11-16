import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatDateISO } from "../../assets/js/format.js";
import useDemo from "./useDemo.js";
import "./MethodExample.css";
import "./LegacyExample.css";

// LegacyExample shows one sentence of old-font Hindi as the source page stores it, and the Hindi that Torko reads.
// While the example is on screen, the Hindi types itself out, glyph by glyph, again and again.
// The example comes from /api/method → examples.legacy. The API decodes it with the code of the reader.
export default function LegacyExample({ example }) {
  const text = example?.text || "";
  const [shown, setShown] = useState(null);
  const [ref, isStatic] = useDemo(async (sleep) => {
    const glyphs = Array.from(text);
    setShown("");
    await sleep(600);
    for (let i = 1; i <= glyphs.length; i++) {
      setShown(glyphs.slice(0, i).join("") + (i < glyphs.length ? "▌" : ""));
      await sleep(28);
    }
    await sleep(2500);
  }, 1500);

  if (!example?.source_text || !text) return null;
  const d = example.debate;
  const typed = isStatic || shown == null ? text : shown;

  return (
    <div ref={ref} className="method-demo legacy-example">
      <p className="method-box__label">In the source page</p>
      <p className="legacy-example__garbled">{example.source_text}</p>
      <div className="method-arrow" aria-hidden="true">
        ↓
      </div>
      <p className="method-box__label">After Torko reads it</p>
      {typed === text ? (
        <p className="legacy-example__hindi" lang="hi">
          {text}
        </p>
      ) : (
        <p className="legacy-example__hindi" lang="hi" aria-label={text}>
          {typed || " "}
        </p>
      )}
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
              · <a href={d.source_url} target="_blank" rel="noopener noreferrer">Read the original on sansad.in</a>
            </>
          )}
        </p>
      )}
    </div>
  );
}

export { LegacyExample };

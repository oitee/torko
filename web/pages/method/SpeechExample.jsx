import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatDateISO, formatNumber } from "../../assets/js/format.js";
import useDemo from "./useDemo.js";
import "./MethodExample.css";
import "./SpeechExample.css";

// SpeechExample shows the turns inside one speech: the turns of the member, and the short interruptions
// between them. While the example is on screen, it moves through four phases, again and again:
// 0 the turns as plain text, 1 a box round each turn, 2 the interruptions dotted and set in,
// 3 one outer box round the whole speech, with the result.
// The example comes from /api/method → examples.speech. Each turn holds only its first words.
export default function SpeechExample({ example }) {
  const turns = Array.isArray(example?.turns) ? example.turns : [];
  const [phase, setPhase] = useState(0);
  const [ref, isStatic] = useDemo(async (sleep) => {
    for (const p of [0, 1, 2]) {
      setPhase(p);
      await sleep(1800);
    }
    setPhase(3);
    await sleep(3500);
  }, 1200);

  if (turns.length === 0) return null;

  const own = turns.filter((t) => t.own).length;
  const other = turns.length - own;
  const shown = isStatic ? 3 : phase;

  return (
    <div ref={ref} className="method-demo speech-example">
      <p className="method-box__label">
        Turns in the source ·{" "}
        {example.member_id ? <Link to={`/member/${example.member_id}`}>{example.member}</Link> : example.member}
        {example.date && (
          <>
            {" "}
            · <span className="method-source__date">{formatDateISO(example.date)}</span>
          </>
        )}
      </p>
      <div className={`speech-example__stitch is-p${shown}`}>
        <ol className="speech-example__turns">
          {turns.map((t) => (
            <li key={t.seq} className={t.own ? "speech-example__turn" : "speech-example__turn speech-example__turn--other"}>
              <b>{t.speaker}:</b> {t.text}
            </li>
          ))}
        </ol>
        <p className="speech-example__result">
          {own} turns of {example.member} and {other} {other === 1 ? "interruption" : "interruptions"} become{" "}
          <Link to={`/speech/${example.speech_id}`}>
            <b>one speech of {formatNumber(example.words)} words</b>
          </Link>
          .
        </p>
      </div>
    </div>
  );
}

export { SpeechExample };

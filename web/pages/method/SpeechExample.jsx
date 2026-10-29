import React from "react";
import { Link } from "react-router-dom";
import { formatDateISO, formatNumber } from "../../assets/js/format.js";
import "./MethodExample.css";
import "./SpeechExample.css";

// SpeechExample shows the turns inside one speech: the turns of the member, and the short interruptions
// between them. A bracket on the left marks the range of the speech, and the interruptions sit inside it.
// The example comes from /api/method → examples.speech. Each turn holds only its first words.
export default function SpeechExample({ example }) {
  const turns = Array.isArray(example?.turns) ? example.turns : [];
  if (turns.length === 0) return null;

  const own = turns.filter((t) => t.own).length;
  const other = turns.length - own;

  return (
    <div className="speech-example">
      <div className="method-box">
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
        <ol className="speech-example__turns">
          {turns.map((t) => (
            <li key={t.seq} className={t.own ? "speech-example__turn" : "speech-example__turn speech-example__turn--other"}>
              <p className="speech-example__who">
                {t.speaker} <span className="speech-example__words">· {formatNumber(t.words)} words</span>
              </p>
              <p className="speech-example__text">{t.text}</p>
            </li>
          ))}
        </ol>
      </div>
      <div className="method-arrow" aria-hidden="true">
        ↓
      </div>
      <div className="method-box method-after">
        <p className="speech-example__result">
          {own} turns of {example.member} and {other} {other === 1 ? "interruption" : "interruptions"} become{" "}
          <Link to={`/speech/${example.speech_id}`}>one speech of {formatNumber(example.words)} words</Link>.
        </p>
      </div>
    </div>
  );
}

export { SpeechExample };

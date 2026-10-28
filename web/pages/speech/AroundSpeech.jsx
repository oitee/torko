import React from "react";
import { Link } from "react-router-dom";
import { SPEAKER_NOT_IDENTIFIED, scriptLang } from "../../assets/js/format.js";
import "./AroundSpeech.css";

// Helper to render speaker name or role for an around-turn.
function renderTurnSpeaker(turn) {
  if (turn.attributed && turn.member_id) {
    return (
      <Link to={`/member/${turn.member_id}`} className="around-speech__speaker-link">
        {turn.member}
      </Link>
    );
  }
  if (turn.attributed && turn.member) {
    return <span className="around-speech__speaker-name">{turn.member}</span>;
  }
  if (turn.role_kind === "presiding") {
    return <span className="around-speech__speaker-name">The Chair</span>;
  }
  return <span className="around-speech__speaker-name">{SPEAKER_NOT_IDENTIFIED}</span>;
}

// Helper to truncate text to 120 characters.
function formatPreview(text) {
  if (!text) return "";
  const cleaned = text.replace(/\s+/g, " ").trim();
  if (cleaned.length > 120) {
    return cleaned.slice(0, 120) + "…";
  }
  return cleaned;
}

// AroundSpeech renders the turns directly before and after the speech in its debate.
export default function AroundSpeech({ before = [], after = [], debateId }) {
  const hasAround = (before && before.length > 0) || (after && after.length > 0);
  if (!hasAround && !debateId) {
    return null;
  }

  return (
    <section className="around-speech" aria-labelledby="around-speech-heading">
      <h3 id="around-speech-heading" className="around-speech__heading">
        Around this speech
      </h3>

      <div className="around-speech__list">
        {before.map((turn) => (
          <div key={turn.seq} className="around-speech__turn">
            <div className="around-speech__speaker">{renderTurnSpeaker(turn)}</div>
            <p className="around-speech__text" lang={scriptLang(turn.text)}>
              {formatPreview(turn.text)}
            </p>
          </div>
        ))}

        <div className="around-speech__current-marker" aria-current="true">
          <span className="around-speech__current-label">This speech</span>
        </div>

        {after.map((turn) => (
          <div key={turn.seq} className="around-speech__turn">
            <div className="around-speech__speaker">{renderTurnSpeaker(turn)}</div>
            <p className="around-speech__text" lang={scriptLang(turn.text)}>
              {formatPreview(turn.text)}
            </p>
          </div>
        ))}
      </div>

      {debateId && (
        <div className="around-speech__footer">
          <Link to={`/debate/${debateId}`} className="around-speech__debate-link">
            Read the whole debate
          </Link>
        </div>
      )}
    </section>
  );
}

export { AroundSpeech };

import React from "react";
import { Link } from "react-router-dom";
import { SPEAKER_NOT_IDENTIFIED, scriptLang } from "../../assets/js/format.js";
import Button from "../../components/Button.jsx";
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

// One row: the turn number in the debate, the speaker, and the start of the text.
function TurnRow({ turn, current = false, label }) {
  return (
    <li className={`around-speech__row ${current ? "around-speech__row--current" : ""}`} aria-current={current || undefined}>
      <span className="around-speech__seq">{turn.seq}</span>
      <div className="around-speech__body">
        <div className="around-speech__speaker">
          {renderTurnSpeaker(turn)}
          {label && <span className="around-speech__label"> · {label}</span>}
        </div>
        <p className="around-speech__text" lang={scriptLang(turn.text)}>
          {formatPreview(turn.text)}
        </p>
      </div>
    </li>
  );
}

// AroundSpeech renders the turns just before and just after the speech in its debate, with the speech in its place.
export default function AroundSpeech({ before = [], after = [], debateId, current = null }) {
  const hasAround = (before && before.length > 0) || (after && after.length > 0);
  if (!hasAround && !debateId) {
    return null;
  }

  return (
    <section className="around-speech" aria-labelledby="around-speech-heading">
      <h2 id="around-speech-heading" className="around-speech__heading">
        Around this speech
      </h2>

      <ol className="around-speech__list">
        {before.map((turn) => (
          <TurnRow key={turn.seq} turn={turn} />
        ))}
        {current && <TurnRow turn={current} current label="this speech" />}
        {after.map((turn) => (
          <TurnRow key={turn.seq} turn={turn} />
        ))}
      </ol>

      {debateId && (
        <div className="around-speech__footer">
          <Button variant="secondary" href={`/debate/${debateId}`}>
            Read the whole debate
          </Button>
        </div>
      )}
    </section>
  );
}

export { AroundSpeech };

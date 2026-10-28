import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  SPEAKER_NOT_IDENTIFIED,
  SPEAKER_NOT_IDENTIFIED_LINE,
  formatNumber,
  scriptLang,
} from "../assets/js/format.js";
import Button from "./Button.jsx";
import TLDR from "./TLDR.jsx";
import "./TurnBox.css";

// The TurnBox component renders a single debate turn.
// It formats speakers, optional speech TLDR, and speech paragraphs.
export default function TurnBox({ turn, meta, summary }) {
  const [expanded, setExpanded] = useState(false);

  if (!turn) {
    return null;
  }

  const { kind, member, member_id, text, words } = turn;

  const metaParts = [];
  if (meta) {
    metaParts.push(meta);
  }
  if (words !== undefined && words !== null) {
    metaParts.push(`${formatNumber(words)} words`);
  }
  const metaText = metaParts.join(" · ");

  let speakerContent = null;
  if (kind === "member") {
    speakerContent = member_id ? (
      <Link to={`/member/${member_id}`} className="turn-box__speaker-link">
        {member}
      </Link>
    ) : (
      <span className="turn-box__speaker-name">{member}</span>
    );
  } else if (kind === "presiding") {
    speakerContent = (
      <span className="turn-box__speaker-name">The Chair</span>
    );
  } else if (kind === "crowd") {
    speakerContent = (
      <span className="turn-box__speaker-name">Several members</span>
    );
  } else {
    speakerContent = (
      <span className="turn-box__speaker-unidentified">
        {SPEAKER_NOT_IDENTIFIED}
      </span>
    );
  }

  const paragraphs = text
    ? text
        .split(/\n\s*\n/)
        .map((p) => p.trim())
        .filter(Boolean)
    : [];

  const hasMore = paragraphs.length > 2;
  const visibleParagraphs = expanded || !hasMore ? paragraphs : paragraphs.slice(0, 2);

  return (
    <div className="turn-box">
      <div className="turn-box__header">
        <div className="turn-box__speaker">{speakerContent}</div>
        {metaText && <div className="turn-box__meta">{metaText}</div>}
      </div>

      {kind === "unattributed" && (
        <p className="turn-box__unidentified-line">
          {SPEAKER_NOT_IDENTIFIED_LINE}
        </p>
      )}

      {summary && <TLDR text={summary} />}

      <div className="turn-box__content">
        {visibleParagraphs.map((para, index) => (
          <p
            key={index}
            className="turn-box__para"
            lang={scriptLang(para)}
          >
            {para}
          </p>
        ))}
      </div>

      {!expanded && hasMore && (
        <div className="turn-box__action">
          <Button variant="text" onClick={() => setExpanded(true)}>
            Read more
          </Button>
        </div>
      )}
    </div>
  );
}

export { TurnBox };

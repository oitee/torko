import React from "react";
import { Link } from "react-router-dom";
import { SPEAKER_NOT_IDENTIFIED } from "../assets/js/format.js";
import "./SpeakerLine.css";

// The SpeakerLine component displays who spoke.
// It links to the member page when the member is known.
// Otherwise it shows Speaker not identified.
export default function SpeakerLine({ speech }) {
  if (!speech || !speech.member) {
    return (
      <span className="speaker-line speaker-line--unidentified">
        {SPEAKER_NOT_IDENTIFIED}
      </span>
    );
  }

  const { member, member_id, seat, party } = speech;
  const metaParts = [];
  if (seat) {
    metaParts.push(seat);
  }
  if (party) {
    metaParts.push(party);
  }

  const metaText = metaParts.length > 0 ? ` · ${metaParts.join(" · ")}` : "";

  return (
    <span className="speaker-line">
      {member_id ? (
        <Link to={`/member/${member_id}`} className="speaker-line__link">
          {member}
        </Link>
      ) : (
        <span className="speaker-line__name">{member}</span>
      )}
      {metaText && <span className="speaker-line__meta">{metaText}</span>}
    </span>
  );
}

export { SpeakerLine };

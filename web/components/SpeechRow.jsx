import React from "react";
import { Link } from "react-router-dom";
import {
  formatDateISO,
  formatNumber,
  scriptLang,
  termShort,
} from "../assets/js/format.js";
import SpeakerLine from "./SpeakerLine.jsx";
import ChipRow from "./ChipRow.jsx";
import "./SpeechRow.css";

// The SpeechRow component displays a single speech in a list.
// The left column holds the date and the type of debate. The right column holds the debate,
// the TLDR, the speaker, the excerpt, the counts and the tags.
export default function SpeechRow({ speech }) {
  if (!speech) {
    return null;
  }

  const {
    id,
    date,
    term,
    kind_label,
    debate,
    summary,
    excerpt,
    words,
    position,
    of,
    tags,
  } = speech;

  const countParts = [];
  if (term !== undefined && term !== null) {
    countParts.push(termShort(term));
  }
  if (position && of) {
    countParts.push(`speech ${formatNumber(position)} of ${formatNumber(of)} in the debate`);
  }
  if (words !== undefined && words !== null) {
    countParts.push(`${formatNumber(words)} words`);
  }

  const excerptLang = excerpt ? scriptLang(excerpt) : undefined;

  return (
    <article className="speech-row">
      <div className="speech-row__when">
        {date && <span className="speech-row__date">{formatDateISO(date)}</span>}
        {kind_label && <span className="speech-row__kind">{kind_label}</span>}
      </div>

      <div className="speech-row__body">
        {debate && (
          <Link to={`/speech/${id}`} className="speech-row__debate">
            {debate}
          </Link>
        )}
        {summary && summary.trim() && (
          <p className="speech-row__tldr">
            <span className="speech-row__tldr-label">TLDR</span> {summary}
          </p>
        )}
        {excerpt && (
          <p className="speech-row__excerpt" lang={excerptLang}>
            “{excerpt}”
          </p>
        )}
        <div className="speech-row__byline">
          <SpeakerLine speech={speech} />
          {countParts.length > 0 && (
            <span className="speech-row__counts">{countParts.join(" · ")}</span>
          )}
        </div>
        {tags && tags.length > 0 && <ChipRow tags={tags} max={6} />}
      </div>
    </article>
  );
}

export { SpeechRow };

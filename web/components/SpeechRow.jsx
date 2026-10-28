import React from "react";
import { Link } from "react-router-dom";
import {
  formatDateISO,
  formatNumber,
  scriptLang,
  termShort,
} from "../assets/js/format.js";
import TLDR from "./TLDR.jsx";
import SpeakerLine from "./SpeakerLine.jsx";
import ChipRow from "./ChipRow.jsx";
import "./SpeechRow.css";

// The SpeechRow component displays a single speech in a list.
// It shows metadata, debate link, TLDR, speaker, excerpt, and tags.
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
    tags,
  } = speech;

  const metaParts = [];
  if (date) {
    metaParts.push(formatDateISO(date));
  }
  if (term !== undefined && term !== null) {
    metaParts.push(termShort(term));
  }
  if (kind_label) {
    metaParts.push(kind_label);
  }
  if (words !== undefined && words !== null) {
    metaParts.push(`${formatNumber(words)} words`);
  }

  const metaLine = metaParts.join(" · ");
  const excerptLang = excerpt ? scriptLang(excerpt) : undefined;

  return (
    <article className="speech-row">
      {metaLine && <div className="speech-row__meta">{metaLine}</div>}
      {debate && (
        <Link to={`/speech/${id}`} className="speech-row__debate">
          {debate}
        </Link>
      )}
      {summary && <TLDR text={summary} />}
      <SpeakerLine speech={speech} />
      {excerpt && (
        <p className="speech-row__excerpt" lang={excerptLang}>
          “{excerpt}”
        </p>
      )}
      {tags && tags.length > 0 && <ChipRow tags={tags} />}
    </article>
  );
}

export { SpeechRow };

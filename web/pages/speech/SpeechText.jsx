import React, { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import {
  SPEAKER_NOT_IDENTIFIED,
  SPEAKER_NOT_IDENTIFIED_LINE,
  scriptLang,
} from "../../assets/js/format.js";
import "./SpeechText.css";

// Split text into paragraphs separated by blank lines, keeping character offsets.
export function splitParagraphs(fullText) {
  if (!fullText) return [];
  const regex = /\n\s*\n/;
  let remaining = fullText;
  let offset = 0;
  const paras = [];

  while (remaining.length > 0) {
    const match = remaining.match(regex);
    if (!match) {
      if (remaining.trim()) {
        paras.push({
          text: remaining,
          start: offset,
          end: offset + remaining.length,
        });
      }
      break;
    }
    const matchIndex = match.index;
    const matchLen = match[0].length;
    const paraText = remaining.slice(0, matchIndex);
    if (paraText.trim()) {
      paras.push({
        text: paraText,
        start: offset,
        end: offset + matchIndex,
      });
    }
    offset += matchIndex + matchLen;
    remaining = remaining.slice(matchIndex + matchLen);
  }
  return paras;
}

// Render paragraph text with <mark> elements for any active marks falling within it.
function renderParagraphContent(para, turnSeq, marks, markIdRef) {
  if (!marks || marks.length === 0) {
    return para.text;
  }

  // Filter and clip marks that fall within this paragraph.
  const relevantMarks = [];
  for (const m of marks) {
    if (m.seq !== turnSeq) continue;
    const clipStart = Math.max(m.start, para.start);
    const clipEnd = Math.min(m.end, para.end);
    if (clipStart < clipEnd) {
      relevantMarks.push({
        start: clipStart - para.start,
        end: clipEnd - para.start,
        orig: m,
      });
    }
  }

  if (relevantMarks.length === 0) {
    return para.text;
  }

  // Sort by start offset
  relevantMarks.sort((a, b) => a.start - b.start);

  const elements = [];
  let lastIdx = 0;

  relevantMarks.forEach((m, i) => {
    if (m.start > lastIdx) {
      elements.push(para.text.slice(lastIdx, m.start));
    }
    const isFirstMarkOverall = !markIdRef.current;
    if (isFirstMarkOverall) {
      markIdRef.current = true;
    }

    elements.push(
      <mark
        key={`m-${i}`}
        id={isFirstMarkOverall ? "first-speech-mark" : undefined}
        className="speech-text__mark"
      >
        {para.text.slice(m.start, m.end)}
      </mark>
    );
    lastIdx = m.end;
  });

  if (lastIdx < para.text.length) {
    elements.push(para.text.slice(lastIdx));
  }

  return elements;
}

// SpeechText renders the whole speech as one continuous reading text.
// Paragraphs of own turns carry ¶1, ¶2 numbers. Interruptions are indented.
export default function SpeechText({
  turns = [],
  hasMember = true,
  activeMarks = null,
  speaker = null,
}) {
  const markIdRef = useRef(false);
  markIdRef.current = false;

  // Scroll to the first mark when activeMarks is updated
  useEffect(() => {
    if (activeMarks && activeMarks.length > 0) {
      const el = document.getElementById("first-speech-mark");
      if (el && typeof el.scrollIntoView === "function") {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [activeMarks]);

  let globalParaCount = 0;
  let afterInterruption = false;

  // The line above an own turn: the member, seat and party. After an interruption it also says "continues".
  const speakerLine = (continues) =>
    speaker?.member ? (
      <div className="speech-text__speaker">
        {speaker.member_id ? (
          <Link to={`/member/${speaker.member_id}`} className="speech-text__speaker-name">
            {speaker.member}
          </Link>
        ) : (
          <span className="speech-text__speaker-name">{speaker.member}</span>
        )}
        <span className="speech-text__speaker-meta">
          {[speaker.seat, speaker.party, continues ? "continues" : null].filter(Boolean).join(" · ")}
        </span>
      </div>
    ) : null;

  return (
    <section className="speech-text" aria-labelledby="speech-text-heading">
      <h2 id="speech-text-heading" className="speech-text__heading">
        The speech
      </h2>

      <div className="speech-text__body">
        {!hasMember && (
          <div className="speech-text__unidentified">
            <div className="speech-text__unidentified-name">
              {SPEAKER_NOT_IDENTIFIED}
            </div>
            <p className="speech-text__unidentified-line meta">
              {SPEAKER_NOT_IDENTIFIED_LINE}
            </p>
          </div>
        )}

        {turns.map((turn) => {
          const isOwn = !hasMember || turn.own;

          if (isOwn) {
            const paragraphs = splitParagraphs(turn.text);
            const isFirst = globalParaCount === 0;
            const continues = afterInterruption;
            afterInterruption = false;
            return (
              <div key={turn.seq} className="speech-text__turn speech-text__turn--own">
                {hasMember && (isFirst || continues) && speakerLine(continues)}
                {paragraphs.map((p, pIdx) => {
                  globalParaCount++;
                  const paraNum = globalParaCount;
                  return (
                    <p
                      key={pIdx}
                      className="speech-text__paragraph"
                      lang={scriptLang(p.text)}
                    >
                      <span
                        className="speech-text__para-num mono meta"
                        aria-label={`Paragraph ${paraNum}`}
                      >
                        ¶{paraNum}
                      </span>
                      <span className="speech-text__para-body">
                        {renderParagraphContent(
                          p,
                          turn.seq,
                          activeMarks,
                          markIdRef
                        )}
                      </span>
                    </p>
                  );
                })}
              </div>
            );
          }

          // Interruption turn
          afterInterruption = true;
          let speakerHeader = null;
          if (turn.attributed && turn.member_id) {
            speakerHeader = (
              <Link
                to={`/member/${turn.member_id}`}
                className="speech-text__interruption-speaker"
              >
                {turn.member}
              </Link>
            );
          } else if (turn.attributed && turn.member) {
            speakerHeader = (
              <span className="speech-text__interruption-speaker">
                {turn.member}
              </span>
            );
          } else if (turn.role_kind === "presiding") {
            speakerHeader = (
              <span className="speech-text__interruption-speaker">
                The Chair
              </span>
            );
          } else {
            speakerHeader = (
              <span className="speech-text__interruption-speaker">
                {SPEAKER_NOT_IDENTIFIED}
              </span>
            );
          }

          return (
            <div
              key={turn.seq}
              className="speech-text__turn speech-text__turn--interruption"
            >
              <div className="speech-text__interruption-header">
                {speakerHeader}
                <span className="meta"> · interruption</span>
              </div>
              <p
                className="speech-text__interruption-text"
                lang={scriptLang(turn.text)}
              >
                {turn.text}
              </p>
            </div>
          );
        })}
      </div>

      <p className="speech-text__footer meta">
        Text from the Lok Sabha debates on sansad.in. Interruptions are kept as
        printed.
      </p>
    </section>
  );
}

export { SpeechText };

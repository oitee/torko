import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  SPEAKER_NOT_IDENTIFIED,
  SPEAKER_NOT_IDENTIFIED_LINE,
  formatDateLong,
  scriptLang,
} from "../../assets/js/format.js";
import { prefersReducedMotion } from "../../assets/js/motion.js";
import CopyButton, { speechCitation } from "../../components/CopyButton.jsx";
import "./SpeechText.css";

// The paragraph id that a hash names, for example "#p7" gives "p7". Other hashes give null.
export function paragraphIdFromHash(hash) {
  const m = /^#?(p\d+)$/.exec(hash || "");
  return m ? m[1] : null;
}

// The text that the reader selected inside the speech, and the paragraph id where the selection starts.
function readSelection(root) {
  const sel = typeof window !== "undefined" ? window.getSelection?.() : null;
  if (!sel || sel.isCollapsed || !root || !sel.anchorNode || !root.contains(sel.anchorNode)) return null;
  const quote = sel.toString().replace(/\s+/g, " ").trim();
  if (!quote) return null;
  const node = sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentElement;
  const para = node?.closest?.("[id^='p']");
  return { quote, paragraph: para && paragraphIdFromHash(para.id) ? para.id : null };
}

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
  const bodyRef = useRef(null);
  const [selected, setSelected] = useState(null);
  const [targetId, setTargetId] = useState(() => paragraphIdFromHash(typeof window !== "undefined" ? window.location.hash : ""));
  const [linkCopied, setLinkCopied] = useState(null);

  // A hash such as #p7 marks that paragraph and brings it into view, also when the data came after the page.
  useEffect(() => {
    const read = () => setTargetId(paragraphIdFromHash(window.location.hash));
    window.addEventListener("hashchange", read);
    return () => window.removeEventListener("hashchange", read);
  }, []);
  useEffect(() => {
    if (!targetId) return;
    const el = document.getElementById(targetId);
    if (el && typeof el.scrollIntoView === "function") {
      el.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth", block: "start" });
    }
    // Only the first load and a new hash move the page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetId, turns.length]);

  useEffect(() => {
    const read = () => setSelected(readSelection(bodyRef.current));
    document.addEventListener("selectionchange", read);
    return () => document.removeEventListener("selectionchange", read);
  }, []);

  // The paragraph sign puts the paragraph in the address and copies the link.
  const copyParagraphLink = async (event, id) => {
    event.preventDefault();
    window.history.replaceState(null, "", `#${id}`);
    setTargetId(id);
    let ok = false;
    try {
      await navigator.clipboard.writeText(`${window.location.origin}${window.location.pathname}#${id}`);
      ok = true;
    } catch {
      // The browser blocks the clipboard. The address bar holds the link.
    }
    setLinkCopied(ok ? id : null);
  };

  const quoteCitation = () =>
    `${speechCitation({
      quote: selected?.quote,
      member: speaker?.member,
      party: speaker?.party,
      seat: speaker?.seat,
      date: speaker?.date ? formatDateLong(speaker.date) : "",
      id: speaker?.id,
    })}${selected?.paragraph ? `#${selected.paragraph}` : ""}`;

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

      <div className="speech-text__select-bar meta" aria-live="polite">
        {selected ? (
          <CopyButton text={quoteCitation} copiedLabel="Copied with source">
            Copy the selected words with the source
          </CopyButton>
        ) : (
          <span>Select words in the speech to copy them with the source. Select the ¶ sign to copy a link to a paragraph.</span>
        )}
      </div>

      <div className="speech-text__body" ref={bodyRef}>
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
                      id={`p${paraNum}`}
                      className={`speech-text__paragraph${targetId === `p${paraNum}` ? " speech-text__paragraph--target" : ""}`}
                      lang={scriptLang(p.text)}
                    >
                      <a
                        href={`#p${paraNum}`}
                        className="speech-text__para-num mono"
                        title={`Copy the link to paragraph ${paraNum}`}
                        aria-label={`Paragraph ${paraNum}. Copy the link.`}
                        onClick={(e) => copyParagraphLink(e, `p${paraNum}`)}
                      >
                        ¶{paraNum}
                      </a>
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
      {linkCopied && (
        <p className="speech-text__footer meta" role="status">
          The link to paragraph {linkCopied.slice(1)} is copied.
        </p>
      )}
    </section>
  );
}

export { SpeechText };

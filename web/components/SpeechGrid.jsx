import React from "react";
import { Link } from "react-router-dom";
import Button from "./Button.jsx";
import {
  SPEAKER_NOT_IDENTIFIED,
  formatDateLong,
  formatNumber,
} from "../assets/js/format.js";
import "./SpeechGrid.css";

// SpeechGrid shows some speeches as boxes in a grid, with one button to the full list on the Search page.
// showSpeaker is false on the page of one member, where each box has the same speaker.
export default function SpeechGrid({ speeches = [], meta, href, action = "See all speeches", empty = "No speeches yet.", showSpeaker = true, id }) {
  const safeSpeeches = Array.isArray(speeches) ? speeches : [];
  const headingId = `${id || "speech-grid"}-heading`;

  return (
    <section className="speech-grid" id={id} aria-labelledby={headingId}>
      <div className="speech-grid__header">
        <h2 id={headingId} className="speech-grid__title">
          Speeches
        </h2>
        {meta && <span className="speech-grid__meta mono">{meta}</span>}
      </div>

      {safeSpeeches.length > 0 ? (
        <div className="speech-grid__grid">
          {safeSpeeches.map((s, idx) => {
            const metaParts = [s.party, s.seat].filter(Boolean).join(" · ");

            return (
              <Link
                key={s.id || idx}
                to={`/speech/${s.id}`}
                className="speech-card"
              >
                <div className="speech-card__top">
                  {showSpeaker && <span className="speech-card__speaker">
                    {s.member ? (
                      <>
                        <span className="speech-card__speaker-name">
                          {s.member}
                        </span>
                        {metaParts && (
                          <span className="speech-card__speaker-meta">
                            {" "}
                            · {metaParts}
                          </span>
                        )}
                      </>
                    ) : (
                      <span className="speech-card__speaker-unknown">
                        {SPEAKER_NOT_IDENTIFIED}
                      </span>
                    )}
                  </span>}
                  <span className="speech-card__date mono">
                    {formatDateLong(s.date)}
                    {s.kind_label ? ` · ${s.kind_label}` : ""}
                  </span>
                </div>

                {s.debate && (
                  <span className="speech-card__debate">{s.debate}</span>
                )}

                {s.summary && (
                  <div className="speech-card__tldr">
                    <span className="speech-card__tldr-label mono">
                      TLDR
                    </span>
                    <span className="speech-card__tldr-text">
                      {s.summary}
                    </span>
                  </div>
                )}

                {s.quote && (
                  <p
                    className="speech-card__quote"
                    lang={s.quote_lang === "hi" ? "hi" : undefined}
                  >
                    “{s.quote}”
                  </p>
                )}

                <div className="speech-card__footer">
                  {s.subject ? (
                    <span className="speech-card__subject">
                      {s.subject}
                    </span>
                  ) : (
                    <span />
                  )}
                  {s.words != null && (
                    <span className="speech-card__words mono">
                      {formatNumber(s.words)} words
                    </span>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      ) : (
        <p className="speech-grid__empty meta">
          {empty}
        </p>
      )}

      <div className="speech-grid__action">
        <Button variant="primary" href={href}>
          {action}
        </Button>
      </div>
    </section>
  );
}

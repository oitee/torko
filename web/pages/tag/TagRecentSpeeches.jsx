import React from "react";
import { Link } from "react-router-dom";
import Button from "../../components/Button.jsx";
import {
  SPEAKER_NOT_IDENTIFIED,
  formatDateLong,
  formatNumber,
  termLong,
} from "../../assets/js/format.js";
import "./TagRecentSpeeches.css";

// TagRecentSpeeches displays recent speeches for this tag in responsive card tiles.
export default function TagRecentSpeeches({
  speeches = [],
  slug = "",
  selectedTerm = "",
}) {
  const safeSpeeches = Array.isArray(speeches) ? speeches : [];
  const termLabel = selectedTerm ? termLong(selectedTerm) : "all terms";

  return (
    <section className="tag-speeches" aria-labelledby="speeches-heading">
      <div className="tag-speeches__header">
        <h2 id="speeches-heading" className="tag-speeches__title">
          Speeches
        </h2>
        <span className="tag-speeches__meta mono">latest · {termLabel}</span>
      </div>

      {safeSpeeches.length > 0 ? (
        <div className="tag-speeches__grid">
          {safeSpeeches.map((s, idx) => {
            const metaParts = [s.party, s.seat].filter(Boolean).join(" · ");

            return (
              <Link
                key={s.id || idx}
                to={`/speech/${s.id}`}
                className="tag-speech-card"
              >
                <div className="tag-speech-card__top">
                  <span className="tag-speech-card__speaker">
                    {s.member ? (
                      <>
                        <span className="tag-speech-card__speaker-name">
                          {s.member}
                        </span>
                        {metaParts && (
                          <span className="tag-speech-card__speaker-meta">
                            {" "}
                            · {metaParts}
                          </span>
                        )}
                      </>
                    ) : (
                      <span className="tag-speech-card__speaker-unknown">
                        {SPEAKER_NOT_IDENTIFIED}
                      </span>
                    )}
                  </span>
                  <span className="tag-speech-card__date mono">
                    {formatDateLong(s.date)}
                  </span>
                </div>

                {s.debate && (
                  <span className="tag-speech-card__debate">{s.debate}</span>
                )}

                {s.summary && (
                  <div className="tag-speech-card__tldr">
                    <span className="tag-speech-card__tldr-label mono">
                      TLDR
                    </span>
                    <span className="tag-speech-card__tldr-text">
                      {s.summary}
                    </span>
                  </div>
                )}

                {s.quote && (
                  <p
                    className="tag-speech-card__quote"
                    lang={s.quote_lang === "hi" ? "hi" : undefined}
                  >
                    “{s.quote}”
                  </p>
                )}

                <div className="tag-speech-card__footer">
                  {s.subject ? (
                    <span className="tag-speech-card__subject">
                      {s.subject}
                    </span>
                  ) : (
                    <span />
                  )}
                  {s.words != null && (
                    <span className="tag-speech-card__words mono">
                      {formatNumber(s.words)} words
                    </span>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      ) : (
        <p className="tag-speeches__empty meta">
          No sample speeches for this term yet.
        </p>
      )}

      <div className="tag-speeches__action">
        <Button variant="primary" href={`/search?tag=${slug}`}>
          See all speeches
        </Button>
      </div>
    </section>
  );
}

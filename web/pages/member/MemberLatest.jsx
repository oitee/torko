import React from "react";
import { Link } from "react-router-dom";
import { formatDateLong, formatNumber } from "../../assets/js/format.js";

export default function MemberLatest({ speeches = [], totalSpeeches = 0 }) {
  const items = (speeches || []).slice(0, 3);
  if (items.length === 0) return null;

  return (
    <section className="member-latest" id="latest" aria-labelledby="member-latest-heading">
      <div className="member-section-head">
        <h2 id="member-latest-heading" className="member-section-title">
          Latest speeches
        </h2>
        <a href="#speeches" className="member-latest__all-link">
          All {formatNumber(totalSpeeches)} speeches
        </a>
      </div>

      <div className="member-latest__grid">
        {items.map((speech) => (
          <article key={speech.id} className="member-latest__card">
            <span className="member-latest__card-meta mono">
              {formatDateLong(speech.date)} · {speech.kind_label || speech.kind}
            </span>
            <h3 className="member-latest__card-title">
              <Link to={`/speech/${speech.id}`} className="member-latest__card-link">
                {speech.debate}
              </Link>
            </h3>
            {speech.summary && (
              <p className="member-latest__card-tldr">{speech.summary}</p>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

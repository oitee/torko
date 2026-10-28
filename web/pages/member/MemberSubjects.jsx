import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";
import Button from "../../components/Button.jsx";

export default function MemberSubjects({ typical = [], totalSpeeches = 0 }) {
  const [expandedKeys, setExpandedKeys] = useState({});
  const [showAll, setShowAll] = useState(false);

  if (!Array.isArray(typical) || typical.length === 0) {
    return null;
  }

  // Sentence above table
  const top = typical[0];
  const topMemberPct = ((top?.member_share || 0) * 100).toFixed(1);
  const topHousePct = ((top?.house_share || 0) * 100).toFixed(1);

  // Find most frequent specific subject
  let topSpec = null;
  typical.forEach((t) => {
    (t.subjects || []).forEach((spec) => {
      if (!topSpec || spec.n > topSpec.n) {
        topSpec = spec;
      }
    });
  });

  let sentence = `${top.name} is the most typical subject: ${topMemberPct}% of this member's speeches and ${topHousePct}% of the house's.`;
  if (topSpec) {
    sentence += ` The specific subject that comes back most is ${topSpec.label.toLowerCase()}, in ${topSpec.n} speeches.`;
  }

  // Max scale for member share / house share bars
  const maxShare = Math.max(
    0.01,
    ...typical.map((s) => Math.max(s.member_share || 0, s.house_share || 0))
  );

  const toggleRow = (slug) => {
    setExpandedKeys((prev) => ({
      ...prev,
      [slug]: !prev[slug],
    }));
  };

  // Rule 37: lists of more than 10 rows show 10, then "Show all N ..."
  const displayItems = showAll ? typical : typical.slice(0, 10);
  const hasMore = typical.length > 10;

  return (
    <section className="member-subjects" id="subjects" aria-labelledby="member-subjects-heading">
      <div className="member-section-head">
        <div className="member-section-head__text">
          <h2 id="member-subjects-heading" className="member-section-title">
            Subjects
          </h2>
          <p className="member-section-subtitle">{sentence}</p>
        </div>
      </div>

      <div className="member-subjects__container">
        <div className="member-subjects__table-head mono">
          <span className="member-subjects__th-caret" aria-hidden="true" />
          <span className="member-subjects__th-subject">Subject</span>
          <span className="member-subjects__th-bar">Member share</span>
          <span className="member-subjects__th-n text-right">Speeches</span>
          <span className="member-subjects__th-ratio text-right">Compared with the house</span>
        </div>

        <div className="member-subjects__list">
          {displayItems.map((s) => {
            const isOpen = Boolean(expandedKeys[s.slug]);
            const specs = s.subjects || [];
            const hasSpecs = specs.length > 0;
            const memberPct = ((s.member_share || 0) * 100).toFixed(0);
            const barW = Math.min(100, ((s.member_share || 0) / maxShare) * 100);
            const houseTick = Math.min(100, ((s.house_share || 0) / maxShare) * 100);
            const ratioText =
              s.lift_terms != null
                ? `${Number(s.lift_terms).toFixed(1)}× the house`
                : "—";

            return (
              <div key={s.slug} className="member-subjects__row-group">
                <div className="member-subjects__row">
                  <div className="member-subjects__caret-cell">
                    {hasSpecs ? (
                      <button
                        type="button"
                        onClick={() => toggleRow(s.slug)}
                        aria-expanded={isOpen}
                        aria-label={`${isOpen ? "Hide" : "Show"} specific subjects for ${s.name}`}
                        className="member-subjects__caret-btn"
                      >
                        <span aria-hidden="true">{isOpen ? "▾" : "▸"}</span>
                      </button>
                    ) : (
                      <span className="member-subjects__caret-empty" aria-hidden="true" />
                    )}
                  </div>

                  <div className="member-subjects__subject-cell">
                    <Link to={`/tag/${s.slug}`} className="member-subjects__link">
                      {s.name}
                    </Link>
                    {hasSpecs && (
                      <span className="member-subjects__spec-count meta">
                        {" "}· {specs.length} specific
                      </span>
                    )}
                  </div>

                  <div className="member-subjects__bar-cell">
                    <div className="member-subjects__bar-track" aria-hidden="true">
                      <span
                        className="member-subjects__bar-fill"
                        style={{ width: `${barW}%` }}
                      />
                      <span
                        className="member-subjects__house-tick"
                        style={{ left: `calc(${houseTick}% - 1px)` }}
                      />
                    </div>
                  </div>

                  <div className="member-subjects__n-cell mono text-right">
                    <span>{formatNumber(s.n)}</span>
                    <span className="member-subjects__pct meta"> {memberPct}%</span>
                  </div>

                  <div className="member-subjects__ratio-cell mono text-right">
                    <span
                      className={
                        s.lift_terms != null && s.lift_terms >= 2
                          ? "member-subjects__ratio--high"
                          : ""
                      }
                    >
                      {ratioText}
                    </span>
                  </div>
                </div>

                {isOpen && hasSpecs && (
                  <div className="member-subjects__specs-list">
                    {specs.map((sub, subIdx) => {
                      const subShare = (sub.n / (s.n || 1)) * barW;
                      return (
                        <div key={subIdx} className="member-subjects__spec-row">
                          <span className="member-subjects__caret-cell" aria-hidden="true" />
                          <div className="member-subjects__spec-label">
                            <span className="meta" aria-hidden="true">› </span>
                            <span>{sub.label}</span>
                          </div>
                          <div className="member-subjects__bar-cell">
                            <div className="member-subjects__bar-track member-subjects__bar-track--sub" aria-hidden="true">
                              <span
                                className="member-subjects__bar-fill member-subjects__bar-fill--sub"
                                style={{ width: `${subShare}%` }}
                              />
                            </div>
                          </div>
                          <div className="member-subjects__n-cell mono text-right">
                            {formatNumber(sub.n)}
                          </div>
                          <div className="member-subjects__ratio-cell" aria-hidden="true" />
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {hasMore && (
          <div className="member-subjects__more-wrap">
            <Button variant="text" onClick={() => setShowAll((prev) => !prev)}>
              {showAll ? "Show fewer" : `Show all ${typical.length} subjects`}
            </Button>
          </div>
        )}

        <div className="member-subjects__legend mono">
          <span className="member-subjects__legend-item">
            <span className="member-subjects__legend-swatch" aria-hidden="true" />
            Member share
          </span>
          <span className="member-subjects__legend-item">
            <span className="member-subjects__legend-tick" aria-hidden="true" />
            House share
          </span>
        </div>
      </div>

      <p className="member-subjects__note meta">
        Share of the member's {formatNumber(totalSpeeches)} speeches. House: share of all speeches by all members in the same terms. Open a subject to see its specific subjects.
      </p>
    </section>
  );
}

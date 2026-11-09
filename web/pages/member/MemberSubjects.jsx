import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";
import Button from "../../components/Button.jsx";
import { formatPct, topSubjectByCount } from "./MemberHead.jsx";

// A ratio to the house leads a row only from this many speeches. Below it, the counts speak alone.
export const MIN_SPEECHES_FOR_RATIO = 10;

export const SUBJECT_SORTS = {
  most: {
    label: "Most speeches",
    compare: (a, b) => (b.n || 0) - (a.n || 0) || (b.lift_terms || 0) - (a.lift_terms || 0),
  },
  unusual: {
    label: "Most unusual",
    compare: (a, b) => (b.lift_terms || 0) - (a.lift_terms || 0) || (b.n || 0) - (a.n || 0),
  },
};

// The text under the name of a subject, for example "4 of 63 tagged (6%) · house 0.2%".
export function subjectCounts(s, tagged) {
  let text = `${formatNumber(s.n)} of ${formatNumber(tagged)} tagged (${formatPct(s.member_share)}) · house ${formatPct(s.house_share)}`;
  if (s.lift_terms != null && s.n >= MIN_SPEECHES_FOR_RATIO) {
    text += ` · ${Number(s.lift_terms).toFixed(1)}× the house`;
  }
  return text;
}

export default function MemberSubjects({ typical = [], tagged = 0, memberId }) {
  const [expandedKeys, setExpandedKeys] = useState({});
  const [showAll, setShowAll] = useState(false);
  const [sort, setSort] = useState("most");

  if (!Array.isArray(typical) || typical.length === 0) {
    return null;
  }

  const top = topSubjectByCount(typical);
  const sentence = `${top.name} has the most speeches: ${formatNumber(top.n)} of ${formatNumber(tagged)} tagged speeches (${formatPct(top.member_share)}). The house share is ${formatPct(top.house_share)}.`;

  const maxShare = Math.max(0.01, ...typical.map((s) => s.member_share || 0));
  const sorted = [...typical].sort(SUBJECT_SORTS[sort].compare);

  const toggleRow = (slug) => setExpandedKeys((prev) => ({ ...prev, [slug]: !prev[slug] }));

  const displayItems = showAll ? sorted : sorted.slice(0, 10);
  const hasMore = typical.length > 10;
  const searchBase = memberId ? `/search?member=${memberId}` : "/search";

  return (
    <section className="member-subjects" id="subjects" aria-labelledby="member-subjects-heading">
      <div className="member-subjects__head">
        <div className="member-subjects__title-row">
          <h2 id="member-subjects-heading" className="member-section-title">
            Subjects
          </h2>
          <div className="member-sort" role="group" aria-label="Order of subjects">
            <span className="member-sort__label" aria-hidden="true">
              Sort
            </span>
            {Object.entries(SUBJECT_SORTS).map(([key, def]) => (
              <button
                key={key}
                type="button"
                className={`member-sort__option${sort === key ? " member-sort__option--on" : ""}`}
                aria-pressed={sort === key}
                onClick={() => setSort(key)}
              >
                {def.label}
              </button>
            ))}
          </div>
        </div>
        <p className="member-section-subtitle">{sentence}</p>
      </div>

      <div className="member-subjects__container">
        <div className="member-subjects__list">
          {displayItems.map((s) => {
            const isOpen = Boolean(expandedKeys[s.slug]);
            const specs = s.subjects || [];
            const hasSpecs = specs.length > 0;
            const barW = Math.min(100, ((s.member_share || 0) / maxShare) * 100);

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
                    <div className="member-subjects__name">
                      <Link to={`/tag/${s.slug}`} className="member-subjects__link">
                        {s.name}
                      </Link>
                      {hasSpecs && (
                        <span className="member-subjects__spec-count meta"> · {specs.length} specific</span>
                      )}
                    </div>
                    <Link to={`${searchBase}&tag=${s.slug}`} className="member-subjects__counts mono">
                      {subjectCounts(s, tagged)}
                    </Link>
                  </div>

                  <div className="member-subjects__bar-cell" aria-hidden="true">
                    <div className="member-subjects__bar-track">
                      <span className="member-subjects__bar-fill" style={{ width: `${barW}%` }} />
                    </div>
                  </div>
                </div>

                {isOpen && hasSpecs && (
                  <div className="member-subjects__specs-list">
                    {specs.map((sub) => (
                      <div key={sub.id ?? sub.label} className="member-subjects__spec-row">
                        <span className="member-subjects__caret-cell" aria-hidden="true" />
                        <div className="member-subjects__spec-label">
                          <span>{sub.label}</span>{" "}
                          <Link to={`${searchBase}&subject=${sub.id}`} className="member-subjects__counts mono">
                            {formatNumber(sub.n)} of {formatNumber(s.n)} speeches
                          </Link>
                        </div>
                      </div>
                    ))}
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
      </div>

    </section>
  );
}

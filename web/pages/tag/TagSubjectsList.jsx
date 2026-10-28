import React from "react";
import { formatNumber } from "../../assets/js/format.js";
import "./TagSubjectsList.css";

// TagSubjectsList renders specific subjects raised under this tag.
export default function TagSubjectsList({ subjects = [] }) {
  const safeSubjects = Array.isArray(subjects) ? subjects : [];

  if (safeSubjects.length === 0) {
    return null;
  }

  const maxN = Math.max(
    1,
    ...safeSubjects.map((s) => Number(s.speeches ?? s.n ?? 0))
  );

  return (
    <section className="tag-subjects" aria-labelledby="subjects-heading">
      <div className="tag-subjects__header">
        <h2 id="subjects-heading" className="tag-subjects__title">
          Subjects under this tag
        </h2>
        <p className="tag-subjects__subtitle">
          The specific things members raised. Across all terms.
        </p>
      </div>

      <div className="tag-subjects__grid">
        {safeSubjects.map((s, idx) => {
          const count = Number(s.speeches ?? s.n ?? 0);
          const widthPercent = maxN > 0 ? (count / maxN) * 100 : 0;
          const label = s.label || s.name || "Subject";

          return (
            <div key={s.id || idx} className="tag-subject-card">
              <span className="tag-subject-card__label">{label}</span>
              <div className="tag-subject-card__track">
                <div
                  className="tag-subject-card__bar"
                  style={{ width: `${widthPercent}%` }}
                />
              </div>
              <div className="tag-subject-card__meta mono">
                <span className="tag-subject-card__count">
                  {formatNumber(count)} speeches
                </span>
                {s.peak != null && (
                  <span className="tag-subject-card__peak">peak {s.peak}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

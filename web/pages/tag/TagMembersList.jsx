import React from "react";
import { Link } from "react-router-dom";
import { formatNumber, termLong } from "../../assets/js/format.js";
import { formatSpan } from "./TagHead.jsx";
import "./TagMembersList.css";

// TagMembersList renders the top members who spoke on this tag.
export default function TagMembersList({ members = [], selectedTerm = "" }) {
  const safeMembers = Array.isArray(members) ? members : [];
  const termLabel = selectedTerm ? termLong(selectedTerm) : "all terms";

  return (
    <section className="tag-members-list" aria-labelledby="members-heading">
      <div className="tag-members-list__header">
        <h2 id="members-heading" className="tag-members-list__title">
          Who spoke
        </h2>
        <span className="tag-members-list__meta mono">
          most speeches · {termLabel}
        </span>
      </div>

      <div className="tag-members-list__items">
        {safeMembers.length > 0 ? (
          safeMembers.map((m, idx) => {
            const span = formatSpan(m.first, m.last);
            const metaParts = [m.party, m.seat, span].filter(Boolean).join(" · ");

            return (
              <Link
                key={m.id || idx}
                to={`/member/${m.id}`}
                className="tag-member-row"
              >
                <span className="tag-member-row__rank mono">{idx + 1}</span>
                <div className="tag-member-row__info">
                  <span className="tag-member-row__name">{m.name}</span>
                  {metaParts && (
                    <span className="tag-member-row__meta">{metaParts}</span>
                  )}
                </div>
                <span className="tag-member-row__count mono">
                  {formatNumber(m.n)}
                </span>
              </Link>
            );
          })
        ) : (
          <p className="tag-members-list__empty meta">
            No sample members for this term yet.
          </p>
        )}
      </div>

      <p className="tag-members-list__note meta">
        Members with 3 or more speeches on this tag.
      </p>
    </section>
  );
}

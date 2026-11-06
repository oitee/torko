import React from "react";
import { Link } from "react-router-dom";
import { formatNumber, termLong } from "../../assets/js/format.js";
import { formatSpan } from "./TagHead.jsx";
import "./TagMembersList.css";

// Each count links to the Search page, with the speeches of that member on this tag.
export default function TagMembersList({ members = [], selectedTerm = "", slug = "", total = null, nMembers = null }) {
  const safeMembers = Array.isArray(members) ? members : [];
  const termLabel = selectedTerm ? termLong(selectedTerm) : "all terms";
  const termParam = selectedTerm ? `&term=${selectedTerm}` : "";
  const searchHref = (memberId) => `/search?tag=${slug}&member=${memberId}${termParam}`;

  return (
    <section className="tag-members-list" aria-labelledby="members-heading">
      <div className="tag-members-list__header">
        <h2 id="members-heading" className="tag-members-list__title">
          Who spoke
        </h2>
        <span className="tag-members-list__meta mono">
          most speeches on this tag · {termLabel}
        </span>
      </div>

      <div className="tag-members-list__items">
        {safeMembers.length > 0 ? (
          safeMembers.map((m, idx) => {
            const span = formatSpan(m.first, m.last);
            const metaParts = [m.party, m.seat, span].filter(Boolean).join(" · ");

            return (
              <div key={m.id || idx} className="tag-member-row">
                <span className="tag-member-row__rank mono">{idx + 1}</span>
                <Link to={`/member/${m.id}`} className="tag-member-row__info">
                  <span className="tag-member-row__name">{m.name}</span>
                  {metaParts && <span className="tag-member-row__meta">{metaParts}</span>}
                </Link>
                <Link
                  to={searchHref(m.id)}
                  className="tag-member-row__count mono"
                  aria-label={`Read ${m.n} speeches of this member on this tag`}
                >
                  {formatNumber(m.n)}
                  {total != null ? ` of ${formatNumber(total)}` : ""}
                </Link>
              </div>
            );
          })
        ) : (
          <p className="tag-members-list__empty meta">
            No member has 3 or more speeches on this tag{selectedTerm ? ` in the ${termLong(selectedTerm)}` : ""}.
          </p>
        )}
      </div>

      <p className="tag-members-list__note meta">
        This list shows members with at least 3 speeches on this tag.
        {nMembers != null && ` In all, ${formatNumber(nMembers)} members spoke on it.`}
        {slug && (
          <>
            {" "}
            <Link to={`/search?tag=${slug}&view=members${termParam}`}>Show all members in Search</Link>
          </>
        )}
      </p>
    </section>
  );
}

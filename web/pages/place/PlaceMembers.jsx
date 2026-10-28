import React, { useState } from "react";
import { Link } from "react-router-dom";
import Button from "../../components/Button.jsx";
import { formatNumber } from "../../assets/js/format.js";
import { formatMonthYear } from "./PlaceHead.jsx";

export default function PlaceMembers({
  members = [],
  totalSpeeches = 0,
}) {
  const [showAll, setShowAll] = useState(false);

  const safeMembers = Array.isArray(members) ? members : [];
  if (safeMembers.length === 0) {
    return null;
  }

  const visibleMembers = showAll ? safeMembers : safeMembers.slice(0, 10);
  const hasMore = safeMembers.length > 10;

  return (
    <section
      className="place-section place-members"
      aria-labelledby="members-heading"
    >
      <div className="place-section__header">
        <h2 id="members-heading" className="place-section__title">
          Who spoke about it
        </h2>
        <span className="place-section__meta mono">
          Across all terms · of {formatNumber(totalSpeeches)} speeches
        </span>
      </div>

      <div className="place-members__list">
        {visibleMembers.map((m, idx) => {
          const rank = idx + 1;
          const metaText = [m.party, m.seat, m.state]
            .filter(Boolean)
            .join(" · ");
          const lastDate = formatMonthYear(m.last);

          return (
            <Link
              key={m.id || idx}
              to={`/member/${m.id}`}
              className="place-members__row"
            >
              <span className="place-members__rank mono">{rank}</span>

              <div className="place-members__main">
                <div className="place-members__title-line">
                  <span className="place-members__name">{m.name}</span>
                  {m.own_seat && (
                    <span className="place-members__own-badge mono">
                      own seat
                    </span>
                  )}
                </div>
                {metaText && (
                  <span className="place-members__meta">{metaText}</span>
                )}
              </div>

              <div className="place-members__stats">
                <span className="place-members__count mono">
                  {formatNumber(m.n)}
                </span>
                {lastDate && (
                  <span className="place-members__last mono">
                    last {lastDate}
                  </span>
                )}
              </div>
            </Link>
          );
        })}
      </div>

      {hasMore && (
        <div className="place-members__toggle">
          <Button
            variant="secondary"
            onClick={() => setShowAll((prev) => !prev)}
          >
            {showAll ? "Show fewer" : `Show all ${safeMembers.length} members`}
          </Button>
        </div>
      )}
    </section>
  );
}

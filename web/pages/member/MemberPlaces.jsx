import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";
import Button from "../../components/Button.jsx";

export default function MemberPlaces({ places = [], totalSpeeches = 0, seat = "" }) {
  const [showAll, setShowAll] = useState(false);

  if (!Array.isArray(places) || places.length === 0) {
    return null;
  }

  const top = places[0];
  const maxN = Math.max(1, ...places.map((p) => p.n || 0));

  let sentence = "";
  if (top) {
    const topPct = totalSpeeches > 0 ? ((top.n / totalSpeeches) * 100).toFixed(1) : 0;
    sentence = `${top.name} is the place named most often, in ${formatNumber(top.n)} speeches (${topPct}% of speeches).`;
    if (seat) {
      const ownPlace = places.find((p) => p.own_seat);
      if (ownPlace) {
        sentence += ` ${seat} is the member's own seat.`;
      }
    }
  }

  // Rule 37: more than 10 items shows 10, then "Show all N ..."
  const displayItems = showAll ? places : places.slice(0, 10);
  const hasMore = places.length > 10;

  return (
    <section className="member-places" id="places" aria-labelledby="member-places-heading">
      <div className="member-section-head">
        <div className="member-section-head__text">
          <h2 id="member-places-heading" className="member-section-title">
            Places
          </h2>
          {sentence && <p className="member-section-subtitle">{sentence}</p>}
        </div>
      </div>

      <div className="member-places__grid">
        {displayItems.map((p) => {
          const pct = totalSpeeches > 0 ? ((p.n / totalSpeeches) * 100).toFixed(1) : "0.0";
          const barW = Math.min(100, Math.max(2, (p.n / maxN) * 100));

          return (
            <div key={p.slug || p.name} className="member-places__card">
              <div className="member-places__card-header">
                <div className="member-places__name-wrap">
                  <Link to={`/place/${p.slug}`} className="member-places__name-link">
                    {p.name}
                  </Link>
                  {p.own_seat && (
                    <span className="member-places__own-seat mono">own seat</span>
                  )}
                </div>
                <span className="member-places__count mono">{formatNumber(p.n)}</span>
              </div>

              <div className="member-places__meta mono">
                {pct}% of speeches
              </div>

              <div className="member-places__bar-track" aria-hidden="true">
                <span className="member-places__bar-fill" style={{ width: `${barW}%` }} />
              </div>
            </div>
          );
        })}
      </div>

      {hasMore && (
        <div className="member-places__more-wrap">
          <Button variant="text" onClick={() => setShowAll((prev) => !prev)}>
            {showAll ? "Show fewer" : `Show all ${places.length} places`}
          </Button>
        </div>
      )}
    </section>
  );
}

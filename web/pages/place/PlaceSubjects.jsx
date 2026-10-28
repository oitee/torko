import React from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";

export default function PlaceSubjects({
  associated = [],
  related = [],
  placeName = "",
}) {
  const safeAssociated = Array.isArray(associated) ? associated : [];
  const safeRelated = Array.isArray(related) ? related : [];

  if (safeAssociated.length === 0 && safeRelated.length === 0) {
    return null;
  }

  return (
    <section
      className="place-section place-subjects"
      aria-labelledby="subjects-heading"
    >
      <div className="place-section__header">
        <h2 id="subjects-heading" className="place-section__title">
          What comes up here
        </h2>
        <span className="place-section__meta mono">Across all terms</span>
      </div>

      <div className="place-subjects__grid">
        {/* Left Column: Often raised here */}
        <div className="place-subjects__col">
          <div className="place-subjects__subhead">
            <h3 className="place-subjects__subtitle">Often raised here</h3>
            <p className="place-subjects__subdesc">
              Subjects far more common for {placeName} than for the house as a
              whole.
            </p>
          </div>

          <div className="place-associated__list">
            {safeAssociated.map((o, idx) => {
              const here = formatNumber(o.n);
              const house = formatNumber(o.all);
              const barPercent =
                o.all > 0 ? Math.min(100, (o.n / o.all) * 100) : 0;

              return (
                <Link
                  key={o.slug || idx}
                  to={`/tag/${o.slug}`}
                  className="place-associated__card"
                >
                  <div className="place-associated__card-top">
                    <span className="place-associated__name">{o.name}</span>
                    <span className="place-associated__ratio mono">
                      {here} of {house}
                    </span>
                  </div>

                  <div className="place-associated__track">
                    <div
                      className="place-associated__bar"
                      style={{ width: `${barPercent}%` }}
                    />
                  </div>

                  <span className="place-associated__sentence">
                    {here} of {house} speeches in the house on this subject are
                    about {placeName}.
                  </span>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Right Column: Most discussed with it */}
        <div className="place-subjects__col">
          <div className="place-subjects__subhead">
            <h3 className="place-subjects__subtitle">Most discussed with it</h3>
            <p className="place-subjects__subdesc">
              Subjects most often in the same speeches. Count of shared speeches.
            </p>
          </div>

          <div className="place-related__chips">
            {safeRelated.map((c, idx) => (
              <Link
                key={c.slug || idx}
                to={`/tag/${c.slug}`}
                className="place-related__chip"
              >
                <span className="place-related__chip-name">{c.name}</span>
                <span className="place-related__chip-count mono">
                  {formatNumber(c.n)}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

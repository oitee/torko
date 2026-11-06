import React from "react";
import { Link } from "react-router-dom";
import Chip from "../../components/Chip.jsx";
import { formatNumber } from "../../assets/js/format.js";

// PlaceSubjects shows two lists. The first lists the subjects that share most speeches with the place.
// The second lists the subjects that are more common for the place than for the whole House.
// Each of these has a bar: the share of the speeches on the subject in the whole House that are about the place.
export default function PlaceSubjects({ associated = [], related = [], placeName = "" }) {
  const safeAssociated = Array.isArray(associated) ? associated : [];
  const safeRelated = Array.isArray(related) ? related : [];

  if (safeAssociated.length === 0 && safeRelated.length === 0) {
    return null;
  }

  return (
    <section className="place-section place-subjects" aria-labelledby="subjects-heading">
      <div className="section-header">
        <h2 id="subjects-heading" className="place-section__title">
          What comes up here
        </h2>
        <span className="place-section__meta mono">Across all terms</span>
      </div>

      <div className="place-subjects__grid">
        <div className="place-subjects__col">
          <div className="place-subjects__subhead">
            <h3 className="place-subjects__subtitle">Most discussed with it</h3>
            <p className="place-subjects__subdesc">
              Subjects in the same speeches as {placeName}. The number is the count of shared speeches.
            </p>
          </div>

          <ul className="chip-list">
            {safeRelated.map((c, idx) => (
              <li key={c.slug || idx}>
                <Chip label={c.name} count={c.n} href={`/tag/${c.slug}`} />
              </li>
            ))}
          </ul>
        </div>

        <div className="place-subjects__col">
          <div className="place-subjects__subhead">
            <h3 className="place-subjects__subtitle">Unusually common here</h3>
            <p className="place-subjects__subdesc">
              Subjects that are far more common in speeches about {placeName} than in the whole House. The counts are small.
            </p>
          </div>

          <div className="place-associated__list">
            {safeAssociated.map((o, idx) => {
              const here = formatNumber(o.n);
              const house = formatNumber(o.all);
              const barPercent = o.all > 0 ? Math.min(100, (o.n / o.all) * 100) : 0;
              return (
                <Link key={o.slug || idx} to={`/tag/${o.slug}`} className="place-associated__card">
                  <div className="place-associated__card-top">
                    <span className="place-associated__name">{o.name}</span>
                    <span className="place-associated__ratio mono">
                      {here} of {house}
                    </span>
                  </div>
                  <div className="place-associated__track" aria-hidden="true">
                    <div className="place-associated__bar" style={{ width: `${barPercent}%` }} />
                  </div>
                  <span className="place-associated__sentence">
                    {here} of {house} speeches in the house on this subject are about {placeName}.
                  </span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

import React, { useState } from "react";
import { Link } from "react-router-dom";
import Button from "../../components/Button.jsx";
import Chip from "../../components/Chip.jsx";
import { formatNumber, termShort } from "../../assets/js/format.js";
import PartyLink from "../../components/PartyLink.jsx";

const OLDER_SHOWN = 10;

// The terms of a member, for example "16th LS, 17th LS".
export function termsText(terms) {
  const list = Array.isArray(terms) ? terms : [];
  return list.map((t) => termShort(t)).join(", ");
}

// SeatCard shows one seat: the current member with the subjects of most of their speeches, then the older members.
// The seat name has no link, because the API does not say if a Place page exists for the seat.
export default function SeatCard({ seat, latestTerm }) {
  const [showAll, setShowAll] = useState(false);
  const current = Array.isArray(seat.current) ? seat.current : [];
  const older = Array.isArray(seat.older) ? seat.older : [];
  const state = current[0]?.state || older[0]?.state || null;
  const visibleOlder = showAll ? older : older.slice(0, OLDER_SHOWN);
  const headingId = `seat-${seat.slug}`;

  return (
    <section className="my-mp-seat" aria-labelledby={headingId}>
      <div className="section-header">
        <h2 id={headingId} className="my-mp-seat__title">
          {seat.seat}
        </h2>
        {state && <span className="my-mp-seat__meta mono">{state}</span>}
      </div>

      {current.length === 0 ? (
        <p className="my-mp-seat__none">
          Torko has no member for this seat in the {latestTerm ? termShort(latestTerm) : "latest term"}.
        </p>
      ) : (
        current.map((m) => {
          const terms = termsText(m.terms);
          const tags = Array.isArray(m.top_tags) ? m.top_tags : [];
          return (
            <div key={m.id} className="my-mp-member">
              <span className="my-mp-member__label">Member now</span>
              <Link to={`/member/${m.id}`} className="my-mp-member__name">
                {m.member}
              </Link>
              {(m.party || terms) && (
                <p className="my-mp-member__line mono">
                  <PartyLink code={m.party} />
                  {m.party && terms && " · "}
                  {terms}
                </p>
              )}
              {tags.length > 0 && (
                <div className="my-mp-member__tags">
                  <h3 className="my-mp-member__tags-title">Subjects of most speeches</h3>
                  <ul className="chip-list">
                    {tags.map((t) => (
                      <li key={t.slug}>
                        <Chip label={t.name} count={t.speeches} href={`/tag/${t.slug}`} />
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="my-mp-member__action">
                <Button variant="secondary" href={`/member/${m.id}`}>
                  See all speeches of {m.member}
                </Button>
              </div>
            </div>
          );
        })
      )}

      {seat.same_name_note && <p className="my-mp-seat__note">{seat.same_name_note}</p>}

      {older.length > 0 && (
        <div className="my-mp-older">
          <div className="my-mp-older__header">
            <h3 className="my-mp-older__title">Members before</h3>
            <span className="my-mp-older__meta mono">{formatNumber(older.length)}</span>
          </div>
          <ul className="my-mp-older__list">
            {visibleOlder.map((m) => (
              <li key={m.id}>
                <Link to={`/member/${m.id}`} className="my-mp-older__row">
                  <span className="my-mp-older__name">{m.member}</span>
                  <span className="my-mp-older__party mono">{m.party || "–"}</span>
                  <span className="my-mp-older__terms mono">{termsText(m.terms)}</span>
                </Link>
              </li>
            ))}
          </ul>
          {!showAll && older.length > OLDER_SHOWN && (
            <Button variant="text" onClick={() => setShowAll(true)}>
              Show all {older.length} members
            </Button>
          )}
        </div>
      )}
    </section>
  );
}

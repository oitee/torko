import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";
import "./DebateWho.css";
import PartyLink from "../../components/PartyLink.jsx";

export default function DebateWho({
  people = [],
  selectedMemberId = null,
  onSelectMember,
}) {
  const [showAll, setShowAll] = useState(false);
  const memN = people.length;
  // A long list closes after the first members, so that "The debate" stays close to the top of the page.
  const MAX_SHOWN = 10;
  const shown = showAll ? people : people.slice(0, MAX_SHOWN);
  const memCountText =
    memN === 1 ? "1 member spoke" : `${formatNumber(memN)} members spoke`;
  const subText = `${memCountText}, in the order shown. Pick a member to see everything they said.`;

  return (
    <section id="who" className="debate-who" aria-labelledby="who-heading">
      <div className="debate-who__header">
        <h2 id="who-heading" className="debate-who__heading">
          Who spoke
        </h2>
        <p className="debate-who__sub">{subText}</p>
      </div>

      <div className="debate-who__list" role="list">
        {shown.map((person, idx) => {
          const isSelected = selectedMemberId === person.id;
          const metaText = [person.seat, `${formatNumber(person.words)} words`].filter(Boolean).join(" · ");

          // A member with no speech of their own spoke only in remarks inside other speeches.
          const turnsN = person.turns || 0;
          const spText =
            person.speeches === 1
              ? "1 speech"
              : person.speeches > 0
              ? `${formatNumber(person.speeches)} speeches`
              : turnsN === 1
              ? "1 remark"
              : `${formatNumber(turnsN)} remarks`;

          return (
            <div
              key={person.id || idx}
              role="listitem"
              className={`debate-who__row ${
                isSelected ? "debate-who__row--selected" : ""
              }`}
              onClick={() => onSelectMember && onSelectMember(isSelected ? null : person.id)}
            >
              <span className="debate-who__ord mono">{idx + 1}</span>

              <div className="debate-who__info">
                <Link
                  to={`/member/${person.id}`}
                  className="debate-who__name"
                  onClick={(e) => e.stopPropagation()}
                >
                  {person.name}
                </Link>
                <span className="debate-who__meta meta">
                  <PartyLink code={person.party} />
                  {person.party && " · "}
                  {metaText}
                </span>
              </div>

              <button
                type="button"
                className={`debate-who__btn ${
                  isSelected ? "debate-who__btn--selected" : ""
                }`}
                aria-pressed={isSelected}
                aria-label={`${isSelected ? "Stop showing only" : "Show everything said by"} ${person.name}`}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectMember && onSelectMember(isSelected ? null : person.id);
                }}
              >
                {spText}
              </button>
            </div>
          );
        })}

        {memN > MAX_SHOWN && !showAll && (
          <div className="debate-who__more">
            <button type="button" className="button button--text" onClick={() => setShowAll(true)}>
              Show all {formatNumber(memN)} members
            </button>
          </div>
        )}
      </div>

    </section>
  );
}

export { DebateWho };

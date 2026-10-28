import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";
import "./DebateWho.css";

export default function DebateWho({
  people = [],
  unidentified = null,
  silent = [],
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
          const metaParts = [];
          if (person.party) metaParts.push(person.party);
          if (person.seat) metaParts.push(person.seat);
          const metaLoc = metaParts.join(" · ");
          const metaText = metaLoc
            ? `${metaLoc} · ${formatNumber(person.words)} words`
            : `${formatNumber(person.words)} words`;

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
                <span className="debate-who__meta meta">{metaText}</span>
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

        {unidentified && unidentified.speeches > 0 && (
          <div className="debate-who__unidentified meta">
            Speaker not identified ·{" "}
            <span className="mono">
              {unidentified.speeches === 1
                ? "1 speech"
                : `${formatNumber(unidentified.speeches)} speeches`}
            </span>
            . Torko could not match this name to one member.
          </div>
        )}
      </div>

      {silent && silent.length > 0 && (
        <div className="debate-who__silent">
          <h3 className="debate-who__silent-heading">
            Listed but did not speak{" "}
            <span className="debate-who__silent-count mono meta">
              · {silent.length}
            </span>
          </h3>

          <div className="debate-who__silent-grid">
            {silent.map((s, idx) => {
              const metaParts = [];
              if (s.party) metaParts.push(s.party);
              if (s.seat) metaParts.push(s.seat);
              const metaText = metaParts.join(" · ");

              return (
                <span key={s.member_id || idx} className="debate-who__silent-item">
                  {s.member_id ? (
                    <Link
                      to={`/member/${s.member_id}`}
                      className="debate-who__silent-name"
                    >
                      {s.name}
                    </Link>
                  ) : (
                    <span className="debate-who__silent-name">{s.name}</span>
                  )}
                  {metaText && (
                    <span className="debate-who__silent-meta meta">
                      {" "}{metaText}
                    </span>
                  )}
                </span>
              );
            })}
          </div>

          <p className="debate-who__silent-note meta">
            Names on the official list of speakers for this debate. They may have
            laid a written speech on the table.
          </p>
        </div>
      )}
    </section>
  );
}

export { DebateWho };

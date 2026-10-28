import React from "react";
import { Link } from "react-router-dom";
import { formatNumber, termShort } from "../../assets/js/format.js";

// The kinds of match, in the order that the page shows them.
const KINDS = [
  { kind: "tag", heading: "Tags" },
  { kind: "place", heading: "Places" },
  { kind: "member", heading: "Members" },
  { kind: "subject", heading: "Subjects" },
];
const PER_KIND = 3;

// The second line of a match: where the item sits.
function context(item) {
  switch (item.kind) {
    case "tag":
      return item.domain || "";
    case "place":
      return item.state || "";
    case "member": {
      const terms = (item.terms || []).map(termShort).join(", ");
      return [item.seat_label || item.seat, terms].filter(Boolean).join(" · ");
    }
    default:
      return "";
  }
}

function href(item) {
  if (item.kind === "tag") return `/search?tag=${encodeURIComponent(item.slug)}`;
  if (item.kind === "place") return `/place/${item.slug}`;
  if (item.kind === "member") return `/member/${item.id}`;
  return null;
}

// SearchMatches lists the tags, places, members and subjects whose names match the words.
// A subject has no page of its own, so it links to its parent tag when it has one.
export default function SearchMatches({ results, query }) {
  const groups = KINDS.map(({ kind, heading }) => ({
    kind,
    heading,
    items: (results || []).filter((r) => r.kind === kind).slice(0, PER_KIND),
  })).filter((g) => g.items.length > 0);

  if (groups.length === 0) return null;

  return (
    <section className="search-matches" aria-labelledby="search-matches-title">
      <h2 id="search-matches-title" className="search-matches__title">
        Pages for “{query}”
      </h2>
      <div className="search-matches__groups">
        {groups.map((group) => (
          <div key={group.kind} className="search-matches__group">
            <h3 className="search-matches__kind">{group.heading}</h3>
            <ul className="search-matches__list">
              {group.items.map((item) => {
                const to = href(item);
                const where = context(item);
                const key = `${item.kind}-${item.slug || item.id || item.subject_id || item.name}`;
                return (
                  <li key={key} className="search-matches__item">
                    <div className="search-matches__name-wrap">
                      {to ? (
                        <Link to={to} className="search-matches__name">
                          {item.name}
                        </Link>
                      ) : (
                        <span className="search-matches__name search-matches__name--plain">{item.name}</span>
                      )}
                      {where && <span className="search-matches__where">{where}</span>}
                      {item.kind === "subject" && item.parent_tag_slug && (
                        <span className="search-matches__where">
                          Under{" "}
                          <Link to={`/search?tag=${encodeURIComponent(item.parent_tag_slug)}`} className="search-matches__parent">
                            {item.parent_tag}
                          </Link>
                        </span>
                      )}
                    </div>
                    <span className="search-matches__count">{formatNumber(item.n_speeches)}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
      <p className="search-matches__note">Each number counts the speeches on that page.</p>
    </section>
  );
}

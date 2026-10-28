import React from "react";
import { formatNumber } from "../../assets/js/format.js";
import Button from "../../components/Button.jsx";
import { yearSpan } from "./searchParams.js";

// What each page offers, in one sentence, and the label of its link.
const OFFERS = {
  tag: {
    text: (name) => `See how members discussed ${name}: when it came up, which parties spoke, who spoke most, and its subjects.`,
    action: "Open the tag page",
    href: (v) => `/tag/${encodeURIComponent(v)}`,
  },
  place: {
    text: (name) => `See how ${name} came up: when, its members of parliament, and the parties and subjects.`,
    action: "Open the place page",
    href: (v) => `/place/${encodeURIComponent(v)}`,
  },
};

// SearchScopeCard sits above the results when the search covers one tag or one place.
// It names the tag or place, gives its figures, and links to its own page for the full picture.
export default function SearchScopeCard({ kind, value, info }) {
  const offer = OFFERS[kind];
  if (!offer || !info) return null;
  const name = info.name || value;
  const span = yearSpan(info.first, info.last);
  const figures = [
    info.total != null ? `${formatNumber(info.total)} speeches` : null,
    info.n_members != null ? `${formatNumber(info.n_members)} members` : null,
    span || null,
  ].filter(Boolean);

  return (
    <aside className="search-scope" aria-label={`About ${name}`}>
      <div className="search-scope__text">
        <p className="search-scope__name">
          {name}
          {info.domain && <span className="search-scope__domain">{info.domain}</span>}
        </p>
        {figures.length > 0 && <p className="search-scope__figures">{figures.join(" · ")}</p>}
        <p className="search-scope__offer">{offer.text(name)}</p>
      </div>
      <div className="search-scope__action">
        <Button variant="secondary" href={offer.href(value)}>
          {offer.action} →
        </Button>
      </div>
    </aside>
  );
}

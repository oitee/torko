import React from "react";
import Chip from "../../components/Chip.jsx";

// SearchSuggested lists the tags near the search words in meaning, as chips. /api/search picks them.
// A chip narrows the search to that tag and keeps the words. Example: "farmers suicide" suggests Farmers' Debt.
export default function SearchSuggested({ items = [], hrefFor }) {
  if (items.length === 0) return null;
  return (
    <section className="search-suggested" aria-labelledby="search-suggested-title">
      <h2 id="search-suggested-title" className="search-suggested__title">
        Suggested filters
      </h2>
      <ul className="search-suggested__list">
        {items.map((p) => (
          <li key={`${p.kind}:${p.slug}`}>
            <Chip label={p.name} href={hrefFor(p)} />
          </li>
        ))}
      </ul>
    </section>
  );
}

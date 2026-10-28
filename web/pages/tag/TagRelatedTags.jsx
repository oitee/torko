import React from "react";
import Chip from "../../components/Chip.jsx";
import "./TagRelatedTags.css";

// TagRelatedTags displays tags that frequently co-occur with the current tag.
export default function TagRelatedTags({ related = [] }) {
  const safeRelated = Array.isArray(related) ? related : [];

  if (safeRelated.length === 0) {
    return null;
  }

  const displayTags = safeRelated.slice(0, 12);

  return (
    <section className="tag-related-tags" aria-labelledby="related-heading">
      <div className="tag-related-tags__header">
        <h2 id="related-heading" className="tag-related-tags__title">
          Related tags
        </h2>
      </div>

      <div className="tag-related-tags__chips">
        {displayTags.map((r) => {
          const count = r.n ?? r.speeches_shared;
          return (
            <Chip
              key={r.slug}
              label={r.name}
              count={count}
              href={`/tag/${r.slug}`}
            />
          );
        })}
      </div>
    </section>
  );
}
